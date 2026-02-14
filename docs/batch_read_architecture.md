# Batch Read Architecture - Detailed Explanation

## Overview

This integration uses **batch reading** to efficiently retrieve data from the SPRSUN heat pump via Modbus TCP.

## What is Batch Reading?

Instead of making 50+ individual Modbus requests:

```python
# BAD: 50 individual requests (SLOW!)
temp1 = read_register(0x0000)  # ~100ms
temp2 = read_register(0x0001)  # ~100ms
...
temp50 = read_register(0x0031) # ~100ms
# TOTAL: 50 × 100ms = ~5000ms = 5 seconds!
```

We make **ONE request** to read multiple consecutive registers:

```python
# GOOD: 1 batch request (FAST!)
all_data = read_holding_registers(address=0x0000, count=50)
# TOTAL: ~300ms
```

**Result: 16x faster!** (5s → 0.3s)

## Implementation in SPRSUN Integration

### 1. Read-Only Registers (50 params): ONE BATCH ✅

**Location:** `custom_components/sprsun_modbus/__init__.py`

```python
def _sync_update(self):
    # Single batch read covering 0x0000-0x0031 (50 registers)
    result = self.client.read_holding_registers(
        address=0x0000,
        count=50,
        device_id=self.device_address
    )
    
    # Parse results
    for address, (key, name, scale, unit, device_class) in REGISTERS_READ_ONLY.items():
        index = address - 0x0000  # Calculate offset
        if index < len(result.registers):
            raw_value = result.registers[index]
            data[key] = raw_value * scale
```

**How indexing works:**

```
result.registers[i] = value at address (0x0000 + i)

Examples:
result.registers[0]  = 0x0000 (compressor_runtime)
result.registers[14] = 0x000E (inlet_temp)
result.registers[18] = 0x0012 (outlet_temp)
result.registers[49] = 0x0031 (dc_fan_target)
```

**Why skip 0x0010?**
- Documentation marks it as "Invalid"
- We define it in `REGISTERS_READ_ONLY` dict but skip in parsing
- Batch still reads it (count=50 continuous) but we don't use the value

### 2. Binary Sensors (6 bits): ONE READ ✅

**Location:** `custom_components/sprsun_modbus/__init__.py`

```python
# Read working status register
result = self.client.read_holding_registers(
    address=0x0003,
    count=1,
    device_id=self.device_address
)

data["working_status_register"] = result.registers[0]
```

**Location:** `custom_components/sprsun_modbus/binary_sensor.py`

```python
@property
def is_on(self) -> bool:
    register_value = self.coordinator.data.get("working_status_register", 0)
    # Extract bit using bitwise AND
    return bool(register_value & (1 << self._bit))
```

**Bit extraction examples:**

```
Register value: 0b00110011

Bit 0 (hotwater_demand):    0b00110011 & 0b00000001 = 1 → ON
Bit 1 (heating_demand):     0b00110011 & 0b00000010 = 1 → ON
Bit 5 (cooling_demand):     0b00110011 & 0b00100000 = 1 → ON
Bit 6 (alarm_stop):         0b00110011 & 0b01000000 = 0 → OFF
Bit 7 (defrost_active):     0b00110011 & 0b10000000 = 0 → OFF
```

### 3. Read-Write Numbers (42 params): INDIVIDUAL READS ⚠️

**Location:** `custom_components/sprsun_modbus/number.py`

```python
async def async_added_to_hass(self) -> None:
    """Read initial value when entity added."""
    if self._key not in self.coordinator.data:
        value = await self._async_read_register()
        self.coordinator.data[self._key] = value

def _async_read_register(self) -> float:
    # Creates NEW connection for each read!
    client = ModbusTcpClient(host=self._host, port=self._port, timeout=5)
    client.connect()
    
    result = client.read_holding_registers(
        address=self._address,
        count=1,
        device_id=self._device_address
    )
    
    client.close()  # Closes connection after single read
    return result.registers[0] * self._scale
```

**Why not batched?**

1. **Sparse addresses**: RW registers are not consecutive
   ```
   0x0036, 0x00C6, 0x00C8, 0x00CA-0x00CC (gaps!)
   0x0169-0x019E (economic mode block)
   ```

2. **Not needed for update cycle**: RW values don't change unless user modifies them

3. **Read on-demand**: Only when entity is created or after write

**Performance impact:**
- Initial load: 42 individual reads = ~4-5 seconds
- Normal operation: No RW reads during scan_interval updates
- After write: 1 read to confirm new value

## Connection Management

### Coordinator (Read-Only + Binary)

**Persistent TCP connection:**

```python
def __init__(self):
    # Create client once
    self.client = ModbusTcpClient(
        host=self.host,
        port=self.port,
        timeout=30,
    )

def _sync_update(self):
    # Reuse existing connection
    if not self.client.connected:
        self.client.connect()
    
    # Read batch + binary  sensors
    # ... (connection stays open)

async def async_shutdown(self):
    # Only close on shutdown
    self.client.close()
```

**Benefits:**
- One TCP connection for all read-only sensors
- No reconnection overhead per update
- Faster and more reliable

### Number Entities (Read-Write)

**Temporary connections:**

```python
def _async_read_register(self):
    client = ModbusTcpClient(...)  # New connection
    client.connect()
    result = client.read_holding_registers(...)
    client.close()  # Immediate close
```

**Why separate?**
- Write operations can't use coordinator's cycle
- Need immediate response for user changes
- Simpler error handling per entity

**Future improvement:**
Could use coordinator's client for reads, create temp connection only for writes.

## Timing & Performance

### Current Architecture

**Per scan_interval (default 10s):**

1. **Batch read RO**: ~300ms (50 registers)
2. **Single read binary**: ~50ms (1 register)
3. **Parse & update**: ~10ms
4. **Total cycle**: ~360ms

**Initial entity load (once):**

1. **Coordinator setup**: ~100ms
2. **RW entity reads**: 42 × ~100ms = ~4200ms
3. **Total startup**: ~4300ms

### Network Traffic

**Per update cycle:**
- Requests sent: 2 (batch + binary)
- Registers read: 51 (50 + 1)
- Data transferred: ~200 bytes per cycle
- At 10s interval: ~20 bytes/second

**Comparison with individual reads:**
- Individual: 50 requests, ~5000 bytes per cycle
- Batch: 2 requests, ~200 bytes per cycle
- **Reduction: 96%**

## Elfin W11 Gateway Considerations

### Buffer Limitations

**Elfin W11 specs:**
- Buffer size: 1024 bytes
- Max accept: 2 connections

**Our usage:**
- Batch request: ~50 bytes
- Batch response: ~100 bytes (50 × 2 bytes)
- Well within buffer limits ✅

### Timeout Calculation

```
Elfin Timeout ≥ Scan Interval + Cycle Time + Safety Margin

Example (default):
30s ≥ 10s + 0.36s + margin
30s ≥ ~11s ✓ (plenty of headroom)
```

**Why 30s recommended?**
- User may increase scan_interval to 30s
- Network delays possible
- Provides 2-3x safety margin

## Comparison Table

| Aspect | Individual Reads | Batch Read | Improvement |
|--------|-----------------|------------|-------------|
| Requests per cycle | 50 | 2 | **25x fewer** |
| Cycle time | ~5s | ~0.36s | **14x faster** |
| Network traffic | ~5KB | ~0.2KB | **25x less** |
| TCP connections | 50 | 1 (persistent) | **50x fewer** |
| Elfin buffer usage | High (risky) | Low (safe) | ✅ |
| Data atomicity | Poor (5s span) | Good (0.3s span) | ✅ |

## Limitations & Future Improvements

### Current Limitations

1. **RW registers not batched**: Each number entity reads individually
2. **Economic mode**: 24 params in 0x0169-0x0180 could be batched
3. **Write operations**: Create new connection each time

### Possible Improvements

1. **Batch RW reads:**
   ```python
   # Read economic heating block in one go
   economic_heat = read_holding_registers(0x0169, count=12)
   ```

2. **Coordinator RW reads:**
   ```python
   # Add selected RW registers to coordinator update
   # Numbers become read-only until user changes
   ```

3. **Write queue:**
   ```python
   # Batch multiple writes if user changes several params
   # Use coordinator connection instead of creating new
   ```

## Summary

The SPRSUN integration uses smart batch reading for:

✅ **Read-Only sensors (50)**: ONE batch request
✅ **Binary sensors (6)**: ONE register read, bit extraction
⚠️ **Read-Write numbers (42)**: Individual reads on-demand

This architecture provides:
- 14x faster sensor updates
- 25x less network overhead
- Reliable persistent connection
- Efficient Elfin W11 gateway usage

**Trade-off**: RW parameters read individually, but this is acceptable since they're only read once at startup and after writes.
