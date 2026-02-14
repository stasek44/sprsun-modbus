#!/usr/bin/env python3
"""Compare batch read values with individual read values to find shift"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

# Key registers to check
CHECK_REGISTERS = [
    (0x0000, "Compressor Runtime", 1),
    (0x0001, "COP", 1),
    (0x0002, "Switching Input Symbol", 1),
    (0x0003, "Working Status Mark", 1),
    (0x0004, "Output Symbol 1", 1),
    (0x0005, "Output Symbol 2", 1),
    (0x0006, "Output Symbol 3", 1),
    (0x000E, "Inlet temp.", 0.1),
    (0x000F, "Hotwater temp.", 0.1),
    (0x0010, "Reserved 0x0010", 1),
    (0x0011, "Ambi temp.", 0.5),
    (0x0012, "Outlet temp.", 0.1),
    (0x0013, "Software Version (Year)", 1),
]

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("Reading batch...")
batch_result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
batch_registers = batch_result.registers if not batch_result.isError() else []

print(f"Batch read returned {len(batch_registers)} registers")
print()

# Small delay
time.sleep(0.5)

print("Comparing batch vs individual reads:")
print("=" * 100)
print(f"{'Addr':<8} {'Register Name':<30} {'Batch Raw':<12} {'Individual Raw':<15} {'Match'}")
print("=" * 100)

for addr, name, scale in CHECK_REGISTERS:
    # Batch value (index = address since we start at 0x0000)
    batch_idx = addr - 0x0000
    batch_raw = batch_registers[batch_idx] if batch_idx < len(batch_registers) else "N/A"
    
    # Individual read
    ind_result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
    if not ind_result.isError() and len(ind_result.registers) > 0:
        ind_raw = ind_result.registers[0]
        match = "✓" if batch_raw == ind_raw else "✗ SHIFT!"
    else:
        ind_raw = "ERROR"
        match = "?"
    
    print(f"0x{addr:04X}   {name:<30} {str(batch_raw):<12} {str(ind_raw):<15} {match}")
    time.sleep(0.01)

client.close()
