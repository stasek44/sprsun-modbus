# TODO List & Known Issues

## Immediate TODOs

### Testing Setup
- [x] **Local integration tests created** - `scripts/test_local.py`
- [x] **Batch read validation working** - All tests pass ✅
- [ ] Run on different device models to verify compatibility
- [ ] Document test results for various hardware configs

### Documentation
- [x] Testing guide updated with local tests
- [x] README.md updated with quick start
- [ ] Add screenshots to `docs/images/`
  - [ ] Device page screenshot
  - [ ] Sensors list screenshot  
  - [ ] Configuration flow screenshot

### Code Quality
- [ ] Run Black formatter: `black custom_components/`
- [ ] Run Ruff linter: `ruff check custom_components/`
- [ ] Fix any linting issues
- [ ] Type checking: `mypy custom_components/`

## Test Results Summary

**Local Integration Tests** (scripts/test_local.py):
- ✅ Connection test - PASSED
- ✅ Batch read test - PASSED (50 registers in ~200ms)  
- ✅ Batch vs individual - PASSED (all values match!)
- ✅ Consistency test - PASSED
- ✅ Performance test - PASSED

**Key Finding:** Batch read returns **identical values** to individual reads. No offset or misalignment issues detected.

Test outputs saved to: `tests/output/`
- `batch_read_*.csv` - Full register dump
- `batch_vs_individual_*.csv` - Validation results (✓ YES for all)
- `consistency_*.csv` - Multiple reads comparison
- `performance_*.csv` - Timing measurements

## Known Limitations

### 1. Read-Write Parameters ⚠️

**Issue:** Number entities create individual connections for each read/write operation.

**Impact:**
- slower initial load (~4s for 42 params)
- More connection overhead

**Possible Fix:**
```python
# In number.py, use coordinator's client instead of creating new
async def _async_read_register(self):
    # Use self.coordinator.client instead of ModbusTcpClient(...)
    result = self.coordinator.client.read_holding_registers(...)
```

**Status:** Not critical, low priority

### 2. Switch Platform Not Implemented ❌

**Issue:** Control registers (0x0032-0x0034) are complex bitfields requiring read-modify-write operations.

**Required Operations:**
```python
# Example: Set antilegionella enable (bit 0 of 0x0034)
current = read_register(0x0034)
new_value = current | 0b00000001  # Set bit 0
write_register(0x0034, new_value)
```

**Complexity:**
- Multiple bits per register
- Each bit controls different function
- Risk of overwriting other bits
- Requires atomic read-modify-write

**Status:** Planned for future release

### 3. Economic Mode Testing Needed ⚠️

**Issue:** 24 economic mode parameters (0x0169-0x0180) not thoroughly tested.

**Risk:**
- Complex relationships between ambient temps and setpoints
- Could affect heat pump operation if misconfigured

**Recommendation:**
- Test on non-critical days
- Monitor heat pump behavior closely
- Document working configurations

**Status:** Functional but needs real-world validation

### 4. Write Operation Conflicts Possible ⚠️

**Issue:** No write queue - if multiple users change settings simultaneously, last write wins.

**Example:**
```
User A: Set heating_setpoint = 45°C
User B: Set heating_setpoint = 40°C (2 seconds later)
Result: 40°C (B wins)
```

**Mitigation:**
- Usually not a problem (single user)
- Could add write queue in future

**Status:** Acceptable for single-user scenarios

### 5. Climate Entity Not Implemented 🔜

**Issue:** No built-in thermostat entity.

**Current Workaround:**
Use number entities + automations:
```yaml
automation:
  - alias: "Heat Pump Thermostat"
    trigger:
      - platform: numeric_state
        entity_id: sensor.indoor_temperature
        below: 20
    action:
      - service: number.set_value
        target:
          entity_id: number.sprsun_heat_pump_unit_mode
        data:
          value: 1  # Heating mode
```

**Future:** Could implement `climate.py` platform

**Status:** Enhancement, not critical

## Feature Requests

### Priority 1 (High Value)

- [ ] **Climate entity** - Better HA integration
- [ ] **Diagnostic sensors** - Connection health, last update time
- [ ] **Template sensors** - Human-readable COP, unit mode, etc.

### Priority 2 (Medium Value)

- [ ] **Switch platform** - Control register bitfields
- [ ] **Batch RW reads** - Use coordinator for initial values
- [ ] **Write queue** - Handle simultaneous changes

### Priority 3 (Nice to Have)

- [ ] **Energy dashboard** - Better integration
- [ ] **Graphs** - Built-in Lovelace cards
- [ ] **Presets** - Economic mode templates
- [ ] **Multi-device** - Support multiple heat pumps

## Testing Checklist

### Before Release

- [ ] All unit tests pass
- [ ] Integration tests pass with CSV verification
- [ ] Manual testing with real hardware:
  - [ ] Connection establishment
  - [ ] All 50 sensors readable
  - [ ] All 6 binary sensors correct
  - [ ] All 42 numbers readable
  - [ ] Write operations work
  - [ ] Scan interval adjustment works
  - [ ] Options flow auto-reload works
- [ ] Documentation complete
- [ ] Polish translation verified
- [ ] GitHub Actions CI passing

### Real-World Testing

- [ ] 24h stability test (scan_interval=10s)
- [ ] Write operations don't crash pump
- [ ] Economic mode configuration works
- [ ] Antilegionella schedule works
- [ ] Elfin W11 timeout settings optimal
- [ ] No memory leaks in HA

## Maintenance Tasks

### Regular

- [ ] Check for pymodbus updates
- [ ] Check for HA API changes
- [ ] Review GitHub issues
- [ ] Update documentation if needed

### Before Each Release

- [ ] Bump version in `manifest.json`
- [ ] Update CHANGELOG.md
- [ ] Tag release in git
- [ ] Test installation via HACS
- [ ] Verify on fresh HA instance

## Community Feedback Needed

### Questions for Users

1. **Scan interval**: Is 10s default good? Too frequent?
2. **Entity names**: Are they clear enough?
3. **Economic mode**: Does it work correctly?
4. **Write operations**: Any conflicts or issues?
5. **Documentation**: What's missing?

### Known User Reports

*None yet - integration just created*

## Code Debt

### Technical Debt

1. **Number.py connection management** - Should use coordinator client
2. **Error handling** - Could be more granular
3. **Logging** - Need more debug-level logs for troubleshooting
4. **Type hints** - Some functions missing type annotations

### Refactoring Opportunities

1. **Coordinator batch configuration** - Make batch size configurable
2. **Register grouping** - Split const.py into logical modules
3. **Entity factory** - Reduce boilerplate in sensor.py, number.py
4. **Config validation** - More robust input validation

## Dependencies to Watch

- **pymodbus**: Currently 3.12.0
  - Watch for breaking changes in 4.x
  - Consider pinning major version

- **homeassistant**: Minimum 2024.1.0
  - Test with newer versions
  - Update if API changes

## Documentation Gaps

- [ ] Video tutorial (installation + setup)
- [ ] Troubleshooting flowchart
- [ ] FAQ section
- [ ] Performance tuning guide
- [ ] Advanced automation examples

## Next Steps

1. **Install test dependencies**:
   ```bash
   pip install -r requirements_dev.txt
   ```

2. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

3. **Test with real hardware**:
   - Install in HA
   - Monitor for 24h
   - Check logs

4. **Community feedback**:
   - Create GitHub Discussions
   - Monitor issues
   - Iterate based on feedback

---

**Last Updated:** 2026-02-14  
**Status:** Ready for testing, documentation complete
