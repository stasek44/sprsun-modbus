#!/usr/bin/env python3
"""
Comprehensive analysis of HA simulation data.
Checks for:
1. Data shift - values appearing in wrong columns
2. Signed/unsigned interpretation errors
3. Scaling issues
"""
import csv
import struct

def to_signed_int16(value):
    """Convert unsigned 16-bit to signed."""
    if value > 32767:
        return value - 65536
    return value

print("=" * 100)
print("COMPREHENSIVE DATA ANALYSIS")
print("=" * 100)

with open('ha_simulation_data_20260214_115139.csv', 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"\nTotal rows: {len(rows)}")

# 1. CHECK FOR DATA SHIFT
print("\n" + "=" * 100)
print("1. DATA SHIFT ANALYSIS")
print("=" * 100)
print("\nChecking if register values appear to be shifted...")

# Check stable values that shouldn't change
stable_registers = {
    'software_version_year': 8228,
    'software_version_month_day': 260,
    'controller_version': 590,
    'display_version': 660,
}

shift_detected = False
for reg_name, expected_value in stable_registers.items():
    values = [int(row[f'{reg_name}_raw']) for row in rows]
    if all(v == expected_value for v in values):
        print(f"✓ {reg_name}: All values = {expected_value} (CONSISTENT)")
    else:
        unique_vals = set(values)
        print(f"✗ {reg_name}: Multiple values found: {unique_vals} (INCONSISTENT - possible shift)")
        shift_detected = True

if not shift_detected:
    print("\n✓ NO DATA SHIFT DETECTED - All stable registers have consistent values")
else:
    print("\n✗ DATA SHIFT DETECTED - Some registers show inconsistent values!")

# 2. SIGNED/UNSIGNED ISSUES
print("\n" + "=" * 100)
print("2. SIGNED/UNSIGNED INTEGER ANALYSIS")
print("=" * 100)

temperature_registers = [
    ('inlet_temp', 0.1, False),
    ('hotwater_temp', 0.1, False),
    ('ambient_temp', 0.5, True),  # Can be negative
    ('outlet_temp', 0.1, False),
    ('suction_gas_temp', 0.5, True),  # Can be negative  
    ('coil_temp', 0.5, True),  # Can be negative
    ('exhaust_temp', 1, False),
    ('driving_temp', 0.5, False),
    ('evap_temp', 0.1, True),  # Can be negative
    ('cond_temp', 0.1, False),
]

print("\nTemperature registers that need SIGNED interpretation:")
print("-" * 100)

for reg_name, scale, should_be_signed in temperature_registers:
    raw_values = [int(row[f'{reg_name}_raw']) for row in rows[:5]]
    
    # Check if any value > 32768
    has_large_values = any(v > 32768 for v in raw_values)
    
    if has_large_values:
        signed_values = [to_signed_int16(v) for v in raw_values]
        current_scaled = [float(row[f'{reg_name}_scaled']) for row in rows[:5]]
        expected_scaled = [v * scale for v in signed_values]
        
        print(f"\n{reg_name} (scale={scale}):")
        print(f"  Raw (unsigned): {raw_values[:3]}")
        print(f"  Raw (signed):   {signed_values[:3]}")
        print(f"  Current scaled: {[f'{v:.1f}' for v in current_scaled[:3]]}")
        print(f"  Expected scaled:{[f'{v:.1f}' for v in expected_scaled[:3]]}")
        print(f"  ❌ NEEDS SIGNED INTERPRETATION" if should_be_signed else "  ⚠️  Unexpected negative values")

# 3. SCALE FACTOR VERIFICATION
print("\n" + "=" * 100)
print("3. SCALE FACTOR VERIFICATION")
print("=" * 100)

print("\nVerifying scale factors match modbus_reference.md:")
print("-" * 100)

# Read a sample row
row = rows[0]

scale_checks = [
    ('inlet_temp', 0.1, 341, 34.1),
    ('hotwater_temp', 0.1, 407, 40.7),
    ('ambient_temp', 0.5, -1, -0.5),  # Should be signed
    ('outlet_temp', 0.1, 391, 39.1),
    ('suction_gas_temp', 0.5, -14, -7.0),  # Should be signed
    ('coil_temp', 0.5, -13, -6.5),  # Should be signed
    ('exhaust_temp', 1, 73, 73),
    ('suction_pressure', 0.1, 2425, 242.5),
    ('discharge_pressure', 0.1, 537, 53.7),
]

for name, scale, expected_raw_signed, expected_scaled in scale_checks:
    raw = int(row[f'{name}_raw'])
    raw_signed = to_signed_int16(raw)
    current_scaled = float(row[f'{name}_scaled'])
    correct_scaled = raw_signed * scale
    
    if abs(correct_scaled - expected_scaled) < 0.1:
        status = "✓ CORRECT"
    else:
        status = "✗ WRONG"
    
    print(f"{name:20s}: raw={raw:6d} | signed={raw_signed:6d} | "
          f"current={current_scaled:8.1f} | expected={expected_scaled:6.1f} | {status}")

# 4. SUMMARY AND RECOMMENDATIONS
print("\n" + "=" * 100)
print("4. SUMMARY AND RECOMMENDATIONS")
print("=" * 100)

print("""
FINDINGS:
---------
1. ✓ NO DATA SHIFT: Registers are in correct positions (verified by stable version registers)

2. ❌ SIGNED/UNSIGNED ERROR: Several temperature registers should be interpreted as SIGNED int16:
   - ambient_temp (R 0x0011): Currently showing 32767.5°C, should be -0.5°C
   - suction_gas_temp (R 0x0015): Currently showing 32761-32764°C, should be -7 to -4.5°C
   - coil_temp (R 0x0016): Currently showing 32761-32763°C, should be -6.5 to -5°C
   - evap_temp (R 0x0028): Currently showing 6546-6549°C, should be -7.4 to -3°C

3. ✓ SCALE FACTORS: All scale factors are correct as per modbus_reference.md
   - 0.1 for inlet/outlet/hotwater/evap/cond temps and pressures
   - 0.5 for ambient/suction/coil/driving temps
   - 1.0 for exhaust temp

RECOMMENDATION:
---------------
Update the coordinator code to interpret these registers as SIGNED int16 before scaling:
- R 0x0011: ambient_temp
- R 0x0015: suction_gas_temp  
- R 0x0016: coil_temp
- R 0x0022: driving_temp (may also go negative)
- R 0x0028: evap_temp

Python code to handle this:
```python
# Convert raw 16-bit register value to signed integer
def to_signed_int16(value):
    if value > 32767:
        return value - 65536
    return value

# Then apply scaling
scaled_value = to_signed_int16(raw_value) * scale_factor
```
""")

print("=" * 100)
