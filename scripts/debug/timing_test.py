#!/usr/bin/env python3
"""Test with minimal delay between batch and individual reads"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

for attempt in range(3):
    print(f"\n{'=' * 80}")
    print(f"Attempt #{attempt + 1}")
    print('=' * 80)
    
    # Batch read
    start = time.time()
    batch = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS).registers
    batch_time = time.time() - start
    
    # Immediately read first 10 individually
    individual = []
    start = time.time()
    for addr in range(0x0000, 0x000A):
        result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
        val = result.registers[0] if not result.isError() and len(result.registers) > 0 else -999
        individual.append((addr, val))
    ind_time = time.time() - start
    
    print(f"Batch read time: {batch_time*1000:.1f}ms")
    print(f"Individual reads time: {ind_time*1000:.1f}ms")
    print(f"\n{'Index':<8} {'Address':<10} {'Batch':<10} {'Individual':<12} {'Match'}")
    print('-' * 80)
    
    for i in range(10):
        addr, ind_val = individual[i]
        batch_val = batch[i]
        match = "✓" if batch_val == ind_val else f"✗ diff={batch_val-ind_val}"
        print(f"{i:<8} 0x{addr:04X}    {batch_val:<10} {ind_val:<12} {match}")
    
    time.sleep(1)  # Wait between attempts

client.close()
