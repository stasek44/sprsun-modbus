#!/usr/bin/env python3
"""Quick check - find where the shift starts"""

from pymodbus.client import ModbusTcpClient

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("Reading batch of 50 registers...")
batch = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS).registers

print("\nReading first 20 registers individually...")
individual = {}
for addr in range(0x0000, 0x0014):
    result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
    if not result.isError() and len(result.registers) > 0:
        individual[addr] = result.registers[0]
    else:
        individual[addr] = None

print("\nComparison:")
print("=" * 80)
print(f"{'Address':<10} {'Batch[i]':<15} {'Individual[addr]':<20} {'Status'}")
print("=" * 80)

for addr in range(0x0000, 0x0014):
    batch_idx = addr
    batch_val = batch[batch_idx] if batch_idx < len(batch) else "N/A"
    ind_val = individual.get(addr, "N/A")
    
    if batch_val == ind_val:
        status = "✓ Match"
    else:
        # Check if batch matches next individual
        if addr + 1 in individual and batch_val == individual[addr + 1]:
            status = f"✗ Shift! Batch matches 0x{addr+1:04X}"
        else:
            status = "✗ Different"
    
    print(f"0x{addr:04X}     {str(batch_val):<15} {str(ind_val):<20} {status}")

client.close()
