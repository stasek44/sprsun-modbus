#!/usr/bin/env python3
"""Simple targeted test - check first 10 registers"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

# Batch read
batch = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS).registers

time.sleep(0.2)

# Individual reads for first 10 registers
print("Batch vs Individual for first 10 registers:")
print("=" * 80)
print(f"{'Index':<8} {'Address':<10} {'Batch':<10} {'Individual':<12} {'Status'}")
print("=" * 80)

for i in range(10):
    addr = 0x0000 + i
    batch_val = batch[i]
    
    result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
    ind_val = result.registers[0] if not result.isError() and len(result.registers) > 0 else -999
    
    status = "✓ Match" if batch_val == ind_val else "✗ Differ"
    
    print(f"{i:<8} 0x{addr:04X}    {batch_val:<10} {ind_val:<12} {status}")
    time.sleep(0.02)

# Check if batch[3] matches individual[4]
print("\n" + "=" * 80)
print("Hypothesis check: Does Batch[3] match Individual[0x0004]?")
result_0x04 = client.read_holding_registers(0x0004, count=1, device_id=DEVICE_ADDRESS)
val_0x04 = result_0x04.registers[0] if not result_0x04.isError() and len(result_0x04.registers) > 0 else -999
print(f"Batch[3] = {batch[3]}")
print(f"Individual[0x0004] = {val_0x04}")
if batch[3] == val_0x04:
    print("✓ YES! Batch IS shifted by +1 starting from index 3")

client.close()
