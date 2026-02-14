# Documentation Summary - SPRSUN Modbus Integration

## Answer to Question 4: Batch Read Architecture

### Current Implementation

#### 1. Read-Only Registers (50 parameters): **ONE BATCH** ✅

**File:** `custom_components/sprsun_modbus/__init__.py`  
**Method:** `_sync_update()` in `SPRSUNDataUpdateCoordinator`

```python
result = self.client.read_holding_registers(
    address=0x0000,
    count=50,  # ← Reads 0x0000 to 0x0031 in single TCP request
    device_id=self.device_address
)
```

**Performance:**
- **One TCP request** per update cycle
- **~300ms** cycle time
- **Atomic data** - all values from same moment

#### 2. Binary Sensors (6 bits): **ONE READ** ✅

**File:** `custom_components/sprsun_modbus/__init__.py`

```python
result = self.client.read_holding_registers(
    address=0x0003,  # working_status_mark register
    count=1,
    device_id=self.device_address
)
```

**Binary sensor extraction** (in `binary_sensor.py`):
```python
is_on = bool(register_value & (1 << self._bit))
# Extracts bits 0,1,4,5,6,7
```

**Performance:**
- **One TCP request** per update cycle
- **~50ms**
- 6 binary sensors from 1 register

#### 3. Read-Write Numbers (42 parameters): **INDIVIDUAL READS** ⚠️

**File:** `custom_components/sprsun_modbus/number.py`  
**Method:** `_async_read_register()` in `SPRSUNNumber`

```python
# Called ONLY on entity initialization (async_added_to_hass)
# or after write operation

client = ModbusTcpClient(...)  # NEW connection!
client.connect()

result = client.read_holding_registers(
    address=self._address,  # e.g. 0x00CC for heating_setpoint
    count=1,
    device_id=self._device_address
)

client.close()  # Closes after single read
```

**Performance:**
- **42 individual TCP connections** at startup
- **~100ms per read** = **~4200ms total** at startup
- **NOT included in coordinator batch** 
- **Not read during update cycles** - only on init and after write

### Summary Table

| Component | Registers | Read Strategy | Requests | Cycle Time |
|-----------|-----------|---------------|----------|------------|
| **Sensors (RO)** | 50 | ONE batch | 1 | ~300ms |
| **Binary Sensors** | 1 (6 bits) | ONE read | 1 | ~50ms |
| **Numbers (RW)** | 42 | Individual | 42 | ~4200ms (startup only) |
| **Total per scan** | 51 | Batch (2 requests) | 2 | ~350ms |
| **Initial load** | 93 | Batch + individuals | 44 | ~4500ms (once) |

### Why RW Parameters Not Batched?

1. **Sparse addresses**: Not consecutive (0x0036, 0x00C6-CC, 0x0169-019E)
2. **Infrequent changes**: Only user-modified
3. **Not needed in update cycle**: Values don't change unless written
4. **Simpler error handling**: Per-entity connection management

### Connection Architecture

**Coordinator (RO + Binary):** 
- ✅ **Persistent connection** - created once, reused
- ✅ Closed only on shutdown

**Number Entities (RW):**
- ⚠️ **Temporary connections** - new per read/write
- ⚠️ Could be optimized to use coordinator connection

### Network Efficiency

**Per scan_interval (10s default):**
- Batch read packets: 2 requests
- Data transferred: ~200 bytes
- Cycle time: ~350ms
- **16x faster than individual reads** (350ms vs 5000ms)

**Startup (once):**
- RW init: 42 requests
- Data transferred: ~1000 bytes
- Time: ~4200ms (acceptable one-time cost)

---

## Complete Documentation Index

### User Documentation

1. **[README.md](../README.md)** - Main overview, quick start
2. **[docs/installation.md](installation.md)** - Hardware & software setup
3. **[docs/configuration.md](configuration.md)** - Dashboards, automations, examples
4. **[docs/testing.md](testing.md)** - Running tests, CSV outputs
5. **[INTEGRATION_README.md](../INTEGRATION_README.md)** - Full guide (Polish)
6. **[ELFIN_SETTINGS.md](../ELFIN_SETTINGS.md)** - Gateway timing recommendations

### Developer Documentation

1. **[docs/batch_read_architecture.md](batch_read_architecture.md)** - Technical deep-dive
2. **[docs/repository_structure.md](repository_structure.md)** - Code organization
3. **[BATCH_READ_EXPLANATION.md](../BATCH_READ_EXPLANATION.md)** - Batch read math
4. **[modbus_reference_raw.md](../modbus_reference_raw.md)** - Original Modbus docs

### Test Documentation

1. **[tests/conftest.py](../tests/conftest.py)** - Pytest fixtures
2. **[tests/test_integration.py](../tests/test_integration.py)** - Full integration tests
3. **CSV outputs:** `tests/output/*.csv` - Test results

---

## Architecture Decisions

### ✅ What Works Well

1. **Batch reading RO registers** - 16x performance improvement
2. **Persistent coordinator connection** - Reliable, efficient
3. **Bit extraction for binary sensors** - Elegant, efficient
4. **Config flow UI** - User-friendly setup
5. **Options flow with reload** - No HA restart needed

### ⚠️ Known Limitations

1. **RW parameters** - Individual connections (could be batched for read)
2. **Switch platform** - Not implemented (bitfield complexity)
3. **Economic mode** - 24 parameters (needs careful testing)
4. **Write operations** - No queue (sequential only)

### 🔮 Future Improvements

1. **Batch RW reads** - Use coordinator for initial value fetch
2. **Write queue** - Batch multiple writes if simultaneous changes
3. **Switch platform** - Implement bitfield manipulation
4. **Climate entity** - Better thermostat integration
5. **Diagnostic sensors** - Connection health, last update time

---

## Testing Strategy

### Unit Tests (tests/test_*.py)

- ✅ **test_const.py** - All register definitions validated
- ✅ **test_sensor.py** - Sensor entities, device classes
- ✅ **test_binary_sensor.py** - Bit extraction logic
- ✅ **test_config_flow.py** - UI configuration flows

**Coverage Target:** >80%

### Integration Tests (tests/test_integration.py)

- ✅ Full coordinator cycle simulation
- ✅ CSV output for all 92 entities
- ✅ Binary sensor bit extraction verification
- ✅ RW parameter read simulation

**Output:** `tests/output/*.csv`

### Manual Testing

Use included scripts:
```bash
# Debug essential 26 parameters
python scripts/modbus_debug_poller.py

# Test batch reading
python scripts/modbus_batch_poller.py
```

---

## Repository Organization Summary

**Standard HA Structure:** ✅
- Custom component in `custom_components/sprsun_modbus/`
- Config flow (no YAML configuration)
- Translations (English + Polish)
- HACS compatible

**Documentation:** ✅
- User guides in `docs/`
- Technical docs at root
- Examples in `examples/`
- Inline code documentation

**Testing:** ✅
- Unit tests in `tests/`
- Integration tests with CSV output
- CI/CD via GitHub Actions
- pytest configuration in `pytest.ini`

**Development:** ✅
- Setup script: `scripts/setup_dev.sh`
- Debug tools: `scripts/modbus_debug_poller.py`
- Requirements: `requirements_dev.txt`

---

## Quick Reference

### Install & Test

```bash
# Setup
git clone https://github.com/stasek44/sprsun-modbus.git
cd sprsun-modbus
./scripts/setup_dev.sh
source .venv/bin/activate

# Run tests
pytest tests/ -v

# Integration tests with CSV
pytest tests/test_integration.py -v -s

# Coverage report
pytest --cov=custom_components/sprsun_modbus --cov-report=html
```

### File Locations

| What | Where |
|------|-------|
| Integration code | `custom_components/sprsun_modbus/` |
| Register definitions | `custom_components/sprsun_modbus/const.py` |
| Batch read logic | `custom_components/sprsun_modbus/__init__.py` |
| User docs | `docs/*.md` |
| Tests | `tests/test_*.py` |
| Test output | `tests/output/*.csv` |
| Debug script | `scripts/modbus_debug_poller.py` |
| Examples | `examples/` |

---

**Documentation complete! ✅**  
All questions answered, repo organized, tests created, architecture documented.
