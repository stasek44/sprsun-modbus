#!/usr/bin/env python3
"""Test: Is there actually an extra 0x0032 register value somewhere in batch?"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

# Do batch read FIRST (before device state changes)
print("Reading BATCH first...")
batch = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS).registers
print(f"Batch returned {len(batch)} registers")

# Small delay
time.sleep(0.1)

# Now read all 51 registers individually (0x0000-0x0032)
print("\nReading INDIVIDUAL registers 0x0000 - 0x0032 (51 registers)...")
individual = {}
for addr in range(0x0000, 0x0033):
    result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
    if not result.isError() and len(result.registers) > 0:
        individual[addr] = result.registers[0]
    else:
        individual[addr] = None
    time.sleep(0.01)

print("\nLooking for pattern:")
print("=" * 100)
print(f"{'Batch[i]':<10} {'Value':<10} {'Matches Individual[addr]':<30} {'Notes'}")
print("=" * 100)

for i in range(50):
    batch_val = batch[i]
    
    # Check which individual address has this value
    matches = []
    for addr in range(0x0000, 0x0033):
        if individual.get(addr) == batch_val:
            matches.append(f"0x{addr:04X}")
    
    # Expected address if no shift
    expected_addr = 0x0000 + i
    expected_val = individual.get(expected_addr, "?")
    
    if batch_val == expected_val:
        status = "✓ Correct"
    elif len(matches) > 0:
        status = f"✗ Shifted - matches {', '.join(matches)}"
    else:
        status = "? Changed"
    
    if i < 10 or i > 45 or status != "✓ Correct":
        print(f"Batch[{i:2d}]   {batch_val:<10} Expected 0x{expected_addr:04X}={expected_val:<10}     {status}")

client.close()
