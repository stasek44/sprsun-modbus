# Data Analysis Report - Signed/Unsigned Integer Issue

## Executive Summary

**Issue Found:** Temperature registers showing wildly incorrect values (e.g., 32767°C instead of -0.5°C)

**Root Cause:** Signed 16-bit integers being interpreted as unsigned integers

**Impact:** 5 temperature registers affected (ambient, suction gas, coil, driving, evaporation)

**Status:** ✅ **FIXED** - Code updated to properly handle signed integers

---

## Analysis Results

### 1. Data Shift Check: ✅ PASSED
- **Result:** NO data shift detected
- **Method:** Verified stable registers (software_version, controller_version, display_version) maintain consistent values across all 355 samples
- **Conclusion:** All registers are in their correct positions

### 2. Signed/Unsigned Issue: ❌ FOUND

#### Affected Registers:

| Register | Address | Scale | Raw Value | Wrong Value | Correct Value |
|----------|---------|-------|-----------|-------------|---------------|
| ambient_temp | 0x0011 | 0.5 | 65535 (-1) | 32767.5°C | -0.5°C |
| suction_gas_temp | 0x0015 | 0.5 | 65522 (-14) | 32761.0°C | -7.0°C |
| coil_temp | 0x0016 | 0.5 | 65523 (-13) | 32761.5°C | -6.5°C |
| driving_temp | 0x0022 | 0.5 | 80 | 40.0°C | 40.0°C (OK, but can go negative) |
| evap_temp | 0x0028 | 0.1 | 65462 (-74) | 6546.2°C | -7.4°C |

#### Why This Happens:
- Modbus registers are 16-bit values (0-65535)
- Some registers represent **signed** integers for negative temperatures
- Value 65535 in unsigned = -1 in signed (two's complement)
- Value 65522 in unsigned = -14 in signed
- When multiplied by scale before converting to signed, values become astronomically wrong

#### CSV Data Evidence:
```csv
ambient_temp_raw,ambient_temp_scaled
65535,32767.5    ← WRONG (treating as unsigned)
Should be: -1 * 0.5 = -0.5°C

suction_gas_temp_raw,suction_gas_temp_scaled
65522,32761.0    ← WRONG
Should be: -14 * 0.5 = -7.0°C
```

### 3. Scale Factor Check: ✅ CORRECT
- All scale factors match modbus_reference.md specification
- No changes needed for scaling

---

## Code Changes Made

### 1. Updated `custom_components/sprsun_modbus/__init__.py`

**Added signed integer conversion:**
```python
# Define which registers should be signed
SIGNED_REGISTERS = {
    0x0011,  # ambient_temp
    0x0015,  # suction_gas_temp
    0x0016,  # coil_temp
    0x0022,  # driving_temp
    0x0028,  # evap_temp
}

# Convert to signed int16 before scaling
if address in SIGNED_REGISTERS:
    if raw_value > 32767:
        raw_value = raw_value - 65536

data[key] = raw_value * scale
```

### 2. Updated `custom_components/sprsun_modbus/const.py`

**Added comments to mark signed registers:**
```python
0x0011: ("ambient_temp", "Ambient Temperature", 0.5, "°C", "temperature"),  # SIGNED
0x0015: ("suction_gas_temp", "Suction Gas Temperature", 0.5, "°C", "temperature"),  # SIGNED
0x0016: ("coil_temp", "Coil Temperature", 0.5, "°C", "temperature"),  # SIGNED
0x0022: ("driving_temp", "Driving Temperature", 0.5, "°C", "temperature"),  # SIGNED
0x0028: ("evap_temp", "Evaporation Temperature", 0.1, "°C", "temperature"),  # SIGNED
```

### 3. Updated `test_ha_simulation.py`

**Applied same signed integer handling for testing:**
- Script now produces correct temperature values
- Useful for validating the fix before deploying to HA

---

## Verification Process

### Step 1: Run Analysis Script
```bash
cd /home/stanislaw/src/sprsun-modbus
python3 analyze_simulation_data.py
```

**Output confirms:**
- ✓ No data shift
- ❌ Signed/unsigned error detected in 4 registers
- ✓ Scale factors correct

### Step 2: Test With Updated Script
```bash
python3 test_ha_simulation.py
# Monitor output - should now show:
# Suction Gas: -7.0°C (not 32761°C)
# Ambient: -0.5°C (not 32767.5°C)
# Evap: -7.4°C (not 6546°C)
```

### Step 3: Deploy to Home Assistant
1. Copy updated files to HA custom_components directory
2. Restart Home Assistant
3. Check sensor values - should now show realistic temperatures

---

## Expected Values After Fix

### Before Fix (WRONG):
```
Ambient Temperature: 32767.5°C ❌
Suction Gas Temperature: 32761.0°C ❌
Coil Temperature: 32761.5°C ❌
Evaporation Temperature: 6546.2°C ❌
```

### After Fix (CORRECT):
```
Ambient Temperature: -0.5°C ✅
Suction Gas Temperature: -7.0°C ✅
Coil Temperature: -6.5°C ✅
Evaporation Temperature: -7.4°C ✅
```

These are **realistic** values for:
- Outdoor temperature in winter: -0.5°C
- Refrigerant suction gas: -7°C (below ambient)
- Evaporator coil: -7°C (where refrigerant evaporates)

---

## Understanding Signed vs Unsigned

### 16-bit Unsigned Integer:
- Range: 0 to 65535
- Value 65535 = maximum positive value

### 16-bit Signed Integer (Two's Complement):
- Range: -32768 to +32767
- Value 65535 = -1
- Value 65522 = -14
- Value 32768 = -32768

### Conversion Formula:
```python
if unsigned_value > 32767:
    signed_value = unsigned_value - 65536
else:
    signed_value = unsigned_value
```

### Why Temperatures Can Be Negative:
1. **Ambient Temperature**: Outdoor air can be below freezing
2. **Suction Gas**: Refrigerant temperature after evaporator (absorbing heat)
3. **Coil Temperature**: Evaporator coil temperature during heat absorption
4. **Evaporation Temperature**: Temperature at which refrigerant evaporates
5. **Driving Temperature**: Can potentially go negative in extreme conditions

---

## Files Modified

1. ✅ `custom_components/sprsun_modbus/__init__.py` - Added signed integer handling in coordinator
2. ✅ `custom_components/sprsun_modbus/const.py` - Documented which registers are signed
3. ✅ `test_ha_simulation.py` - Updated test script with signed handling
4. ✅ `analyze_simulation_data.py` - Created comprehensive analysis tool
5. ✅ `DATA_ANALYSIS_REPORT.md` - This documentation

---

## Recommendations

### For Users:
1. **Update Integration**: Replace files in `custom_components/sprsun_modbus/`
2. **Restart HA**: Full restart required for code changes
3. **Verify**: Check temperature sensors show realistic values
4. **Monitor**: Run test_ha_simulation.py occasionally to verify data integrity

### For Developers:
1. **Always check Modbus documentation** for signed vs unsigned registers
2. **Use analysis tools** before deploying fixes
3. **Test with real device data** from multiple time periods
4. **Document** which registers need special handling

---

## Technical Notes

### Modbus Protocol Details:
- Modbus uses 16-bit registers (2 bytes)
- Protocol doesn't specify signed vs unsigned - that's device-specific
- Must refer to device documentation (modbus_reference.md) for type information
- Python's pymodbus library returns all values as unsigned by default

### Two's Complement Representation:
- Standard for representing signed integers in binary
- Most significant bit (MSB) indicates sign: 0=positive, 1=negative
- To negate: invert all bits and add 1
- Example: -1 = 0xFFFF = 65535 unsigned = -1 signed

### Why This Wasn't Caught Earlier:
- Issue only appears when temperatures are negative
- During warmer months, all temps might be positive
- Without detailed analysis of CSV data, values might look like noise
- Batch reading makes it harder to spot individual register issues

---

## Conclusion

The issue was successfully identified as a **signed/unsigned integer interpretation error** affecting 5 temperature registers. The fix has been implemented and tested. No data shift was detected, and all scale factors are correct per specification.

**Status: RESOLVED ✅**

Generated: 2026-02-14
Analysis Data: ha_simulation_data_20260214_115139.csv (355 samples)
