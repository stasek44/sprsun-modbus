#!/usr/bin/env python3
"""Detailed analysis of the shift - where does it start?"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

# Read batch
batch_result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
batch_regs = batch_result.registers

print("Detailed shift analysis:")
print("=" * 110)
print(f"{'Addr':<8} {'Batch[i]':<12} {'Individual[addr]':<18} {'Match?':<12} {'Batch[i] matches Individual[?]'}")
print("=" * 110)

for addr in range(0x0000, 0x0020):  # Check first 32 registers
    batch_idx = addr - 0x0000
    batch_val = batch_regs[batch_idx]
    
    # Read individual
    ind_result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
    ind_val = ind_result.registers[0] if (not ind_result.isError() and len(ind_result.registers) > 0) else -1
    
    match = "✓ MATCH" if batch_val == ind_val else "✗ SHIFT"
    
    # Check if batch value matches any nearby individual register
    batch_matches_addr = "?"
    if batch_val != ind_val:
        # Check if batch[addr] matches individual[addr-1] or individual[addr+1]
        for check_offset in range(-2, 3):
            check_addr = addr + check_offset
            if check_addr >= 0 and check_addr < 0x0032:
                check_result = client.read_holding_registers(check_addr, count=1, device_id=DEVICE_ADDRESS)
                if not check_result.isError() and len(check_result.registers) > 0:
                    check_val = check_result.registers[0]
                    if batch_val == check_val and check_offset != 0:
                        batch_matches_addr = f"0x{check_addr:04X} (offset {check_offset:+d})"
                        break
    
    print(f"0x{addr:04X}   {batch_val:<12} {ind_val:<18} {match:<12} {batch_matches_addr}")
    time.sleep(0.01)

client.close()
