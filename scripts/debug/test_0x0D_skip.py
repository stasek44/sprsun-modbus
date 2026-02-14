#!/usr/bin/env python3
"""Test hypothesis: Device occasionally skips 0x000D in batch reads"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("Testing if batch read occasionally skips register 0x000D")
print("=" * 100)
print("Doing 20 batch reads and checking for inconsistencies...")
print()

for attempt in range(20):
    # Batch read
    batch_result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
    batch = batch_result.registers
    
    # Read 0x000D and 0x000E individually to compare
    result_0x0D = client.read_holding_registers(0x000D, count=1, device_id=DEVICE_ADDRESS)
    val_0x0D = result_0x0D.registers[0] if not result_0x0D.isError() and len(result_0x0D.registers) > 0 else -1
    
    result_0x0E = client.read_holding_registers(0x000E, count=1, device_id=DEVICE_ADDRESS)
    val_0x0E = result_0x0E.registers[0] if not result_0x0E.isError() and len(result_0x0E.registers) > 0 else -1
    
    # Check batch indices
    batch_idx_0x0D = 13  # 0x000D
    batch_idx_0x0E = 14  # 0x000E
    
    batch_val_0x0D = batch[batch_idx_0x0D]
    batch_val_0x0E = batch[batch_idx_0x0E]
    
    # Look for shift: batch[13] matches 0x000E instead of 0x000D
    if batch_val_0x0D == val_0x0E and batch_val_0x0D != val_0x0D:
        print(f"Attempt {attempt+1}: ❌ SHIFT DETECTED!")
        print(f"  Batch[13] = {batch_val_0x0D} matches Individual[0x000E] = {val_0x0E}")
        print(f"  Batch[13] ≠ Individual[0x000D] = {val_0x0D}")
        print(f"  Batch[14] = {batch_val_0x0E} (should be ~{val_0x0E})")
        print()
    elif batch_val_0x0D == val_0x0D:
        print(f"Attempt {attempt+1}: ✓ OK - Batch[13]={batch_val_0x0D} matches 0x000D={val_0x0D}")
    else:
        print(f"Attempt {attempt+1}: ? Unknown state")
    
    time.sleep(0.5)

client.close()
