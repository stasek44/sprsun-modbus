# Testing and Debugging Guide

## 1. HA Data Simulation Script

### Purpose
The `test_ha_simulation.py` script simulates exactly how Home Assistant fetches data from the heat pump. This helps debug issues like incorrect temperature readings (e.g., suction gas temp showing 30000°C).

### Usage

```bash
# Basic usage (5 minutes test)
python3 test_ha_simulation.py

# Or if you want to customize duration, edit the script and change:
TEST_DURATION = 300  # seconds (5 minutes)
# to your desired duration
```

### What it does:
1. Connects to the heat pump via Modbus TCP
2. Reads registers 0x0000-0x0031 (50 registers) in a single batch - **exactly** like HA does
3. Applies the same scaling factors as HA uses:
   - Inlet/Outlet/Hotwater temps: `raw * 0.1`
   - Ambient/Suction/Coil/Driving temps: `raw * 0.5`
   - Exhaust temp: `raw * 1`
   - Pressures: `raw * 0.1`
4. Logs every read cycle to CSV file with timestamp
5. Displays key temperatures on console for real-time monitoring

### Output
Creates a CSV file: `ha_simulation_data_YYYYMMDD_HHMMSS.csv`

**Columns:**
- `timestamp`: ISO format timestamp
- `iteration`: Read cycle number
- For each register: `<name>_raw` and `<name>_scaled`

### Example output:
```
[1] Fetching data... OK - Suction Gas: 42.5°C (raw: 85), Inlet: 35.2°C, Outlet: 38.7°C
[2] Fetching data... OK - Suction Gas: 42.0°C (raw: 84), Inlet: 35.3°C, Outlet: 38.8°C
...
```

### Analyzing Results

**To find anomalies:**
```bash
# Check for unrealistic temperatures
grep "suction_gas_temp_scaled" ha_simulation_data_*.csv | awk -F',' '{if ($X > 100 || $X < -50) print}'

# Import into LibreOffice/Excel and plot:
# - suction_gas_temp_scaled over time
# - Compare raw vs scaled values
# - Look for sudden jumps or out-of-range values
```

**Common issues to look for:**
1. **Raw value > 65000**: Indicates signed/unsigned interpretation issue
2. **Scaled value wildly different from raw**: Check scale factor
3. **Value jumps by exactly 256x**: Byte order issue
4. **Periodic spikes**: Timing/polling issue

---

## 2. Home Assistant Integration Changes

### Fixed Issues

#### A. Read/Write Entities Not Showing Values
**Problem:** Number entities (setpoints, etc.) showed "unknown" after adding integration.

**Fix:** Updated coordinator (`__init__.py`) to read all R/W registers during polling cycle.

#### B. Incorrect Entity Types
**Problem:** All inputs showed as "volume" type instead of proper types.

**Fixes:**
1. **Mode controls** (Unit Mode, Fan Mode, Pump Mode) → Changed from `number` to `select` entities
   - Now show proper dropdown with options:
     - Unit Mode: "Hot Water Only", "Heating Only", etc.
     - Fan Mode: "Normal", "Economic", "Night", "Test"
     - Pump Mode: "Interval", "Normal", "Demand"

2. **Temperature controls** → Proper `temperature` device class
   - Heating/Cooling/Hotwater setpoints
   - Economic mode temperatures
   - All temp differentials

3. **Voltage sensor** → Fixed from "power" to "voltage" device class

#### C. Input Validation/Ranges
All number entities now have proper constraints:

| Entity | Min | Max | Step | Unit |
|--------|-----|-----|------|------|
| Heating Setpoint | 10 | 55 | 0.5 | °C |
| Cooling Setpoint | 12 | 30 | 0.5 | °C |
| Economic Heat Ambient | -30 | 50 | 1 | °C |
| Economic Heat Temp | 10 | 55 | 0.5 | °C |
| Economic Cool Temp | 12 | 30 | 0.5 | °C |
| Temp Differentials | 2 | 18 | 1 | °C |
| Antilegionella Temp | 30 | 70 | 1 | °C |
| Comp Delay | 1 | 60 | 1 | min |

### New Entities

#### Select Entities:
- **Unit Mode**: Control operating mode (DHW/Heating/Cooling combinations)
- **Fan Mode**: Control fan operation (Normal/Economic/Night/Test)
- **Pump Mode**: Control pump operation (Interval/Normal/Demand)

These replace the previous numeric inputs and provide user-friendly dropdown selection.

### Testing the Integration

1. **Remove and re-add integration** in HA to ensure clean state
2. **Check all entities load**: Should see ~90+ entities:
   - 49 sensors (read-only)
   - 6 binary sensors
   - 34 number entities (read-write)
   - 3 select entities (modes)
3. **Verify values load**: None should show "unknown" after initial poll
4. **Test setpoint changes**: Change a temperature, verify it writes to device
5. **Test mode changes**: Change unit mode, verify dropdown options work

### Configuration

No configuration changes needed. Integration auto-discovers all entities based on register definitions in `const.py`.

---

## 3. Troubleshooting

### Issue: Entities still show "unknown"
**Check:**
1. Modbus connection is stable
2. Device address is correct (usually 1)
3. Check HA logs for Modbus errors: `grep sprsun /config/home-assistant.log`

### Issue: Wrong temperature values
**Steps:**
1. Run `test_ha_simulation.py` for 5-10 minutes
2. Check CSV output for anomalies
3. Compare raw values with actual device display
4. Check if scale factors are correct in `const.py`

### Issue: Can't write to registers
**Check:**
1. Register address is in R/W range (not R-only)
2. Value is within min/max range
3. Device isn't in a locked state (check manual)

### Issue: Mode selection doesn't work
**Verify:**
1. Select entity is created (check Developer Tools → States)
2. Options are populated correctly
3. Writing to register succeeds (check logs)
4. Device accepts the mode value (some modes may be disabled by device)

---

## 4. Advanced: Adding New Registers

### To add a new sensor (read-only):
1. Add to `REGISTERS_READ_ONLY` in `const.py`:
```python
0x00XX: ("key_name", "Display Name", scale, "unit", "device_class"),
```

### To add a new number control (read-write):
1. Add to `REGISTERS_NUMBER` in `const.py`:
```python
0x00XX: ("key_name", "Display Name", scale, "°C", min, max, step, "temperature"),
```

### To add a new mode control:
1. Add to `REGISTERS_SELECT` in `const.py`:
```python
0x00XX: ("key_name", "Display Name", {
    0: "Option 1",
    1: "Option 2",
}),
```

After changes:
1. Restart Home Assistant
2. Remove and re-add integration
3. All new entities should appear automatically
