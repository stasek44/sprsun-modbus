#!/usr/bin/env python3
"""Test if batch read is actually skipping 0x0003 and reading 0x0032 instead"""

from pymodbus.client import ModbusTcpClient

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("Testing hypothesis: Batch read skips 0x0003 and includes 0x0032")
print("=" * 80)

# Read batch (supposedly 0x0000-0x0031)
batch_result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
batch = batch_result.registers

print(f"\nBatch read returned {len(batch)} registers")
print("\nChecking if batch includes 0x0032 instead of 0x0003:")
print("-" * 80)

# Read 0x0032 individually
result_0x32 = client.read_holding_registers(0x0032, count=1, device_id=DEVICE_ADDRESS)
val_0x32 = result_0x32.registers[0] if not result_0x32.isError() and len(result_0x32.registers) > 0 else "ERROR"

# Check last value in batch
print(f"Batch[49] (last value) = {batch[49]}")
print(f"Individual read of 0x0032 = {val_0x32}")

if batch[49] == val_0x32:
    print("\n✓ CONFIRMED: Batch[49] matches 0x0032!")
    print("  Batch read is actually returning: 0x0000-0x0002, 0x0004-0x0032")
    print("  (skipping 0x0003)")
else:
    # Check 0x0031
    result_0x31 = client.read_holding_registers(0x0031, count=1, device_id=DEVICE_ADDRESS)
    val_0x31 = result_0x31.registers[0] if not result_0x31.isError() and len(result_0x31.registers) > 0 else "ERROR"
    print(f"Individual read of 0x0031 = {val_0x31}")
    if batch[49] == val_0x31:
        print("\n✗ Batch[49] matches 0x0031 - different issue")

print("\n" + "=" * 80)
print("Full comparison of last few registers:")
print("-" * 80)

for offset in range(45, 50):
    addr_expected = 0x0000 + offset
    addr_if_skipped = addr_expected + 1  # If 0x0003 is skipped
    
    batch_val = batch[offset]
    
    # Read both addresses
    result_exp = client.read_holding_registers(addr_expected, count=1, device_id=DEVICE_ADDRESS)
    val_exp = result_exp.registers[0] if not result_exp.isError() and len(result_exp.registers) > 0 else "?"
    
    result_skip = client.read_holding_registers(addr_if_skipped, count=1, device_id=DEVICE_ADDRESS)
    val_skip = result_skip.registers[0] if not result_skip.isError() and len(result_skip.registers) > 0 else "?"
    
    exp_match = "✓" if batch_val == val_exp else " "
    skip_match = "✓" if batch_val == val_skip else " "
    
    print(f"Batch[{offset}] = {batch_val:5d}  |  0x{addr_expected:04X} = {val_exp:5s} {exp_match}  |  0x{addr_if_skipped:04X} = {val_skip:5s} {skip_match}")

client.close()
