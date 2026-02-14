#!/usr/bin/env python3
"""Test: Does device return consistent number of registers in batch reads?"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("Testing: Does device return consistent register count?")
print("=" * 80)
print("Doing 50 batch reads of 50 registers (0x0000, count=50)")
print()

register_counts = {}
first_values = {}
last_values = {}

for i in range(50):
    result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
    
    if result.isError():
        print(f"Read {i+1}: ERROR - {result}")
        continue
    
    count = len(result.registers)
    first_val = result.registers[0] if count > 0 else None
    last_val = result.registers[-1] if count > 0 else None
    
    # Track counts
    register_counts[count] = register_counts.get(count, 0) + 1
    
    # Track first/last values for pattern analysis
    if count not in first_values:
        first_values[count] = []
        last_values[count] = []
    first_values[count].append(first_val)
    last_values[count].append(last_val)
    
    if i < 5 or count != 50:  # Show first 5 and any anomalies
        print(f"Read {i+1:2d}: count={count}, first={first_val}, last={last_val}")
    
    time.sleep(0.2)

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Total reads: 50")
print(f"Different register counts observed: {len(register_counts)}")
print()
for count, freq in sorted(register_counts.items()):
    print(f"  Count {count}: {freq} times ({freq/50*100:.1f}%)")
    if count in first_values:
        unique_first = len(set(first_values[count]))
        unique_last = len(set(last_values[count]))
        print(f"    First value variations: {unique_first}, Last value variations: {unique_last}")

print("\n" + "=" * 80)
print("CONCLUSION:")
if len(register_counts) == 1:
    count = list(register_counts.keys())[0]
    print(f"✓ Device ALWAYS returns {count} registers - consistent count!")
    if count == 50:
        print("  → Register MAPPING might be inconsistent (shifts)")
        print("  → But COUNT is reliable")
    else:
        print(f"  → Device returns {count} instead of requested 50!")
else:
    print("✗ Device returns VARIABLE number of registers:")
    print("  → Count is NOT reliable")
    print("  → This is worse than expected!")

client.close()
