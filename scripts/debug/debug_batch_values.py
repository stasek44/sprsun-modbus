#!/usr/bin/env python3
"""Debug script to show raw register values from batch read"""

from pymodbus.client import ModbusTcpClient

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

# Register names in order
REGISTER_NAMES = [
    (0x0000, "Compressor Runtime"),
    (0x0001, "COP"),
    (0x0002, "Switching Input Symbol"),
    (0x0003, "Working Status Mark"),
    (0x0004, "Output Symbol 1"),
    (0x0005, "Output Symbol 2"),
    (0x0006, "Output Symbol 3"),
    (0x0007, "Failure Symbol 1"),
    (0x0008, "Failure Symbol 2"),
    (0x0009, "Failure Symbol 3"),
    (0x000A, "Failure Symbol 4"),
    (0x000B, "Failure Symbol 5"),
    (0x000C, "Failure Symbol 6"),
    (0x000D, "Failure Symbol 7"),
    (0x000E, "Inlet temp."),
    (0x000F, "Hotwater temp."),
    (0x0010, "Reserved 0x0010"),
    (0x0011, "Ambi temp."),
    (0x0012, "Outlet temp."),
    (0x0013, "Software Version (Year)"),
    (0x0014, "Software Version (Month/Day)"),
]

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("=" * 80)
print("BATCH READ - Reading 50 registers starting from 0x0000")
print("=" * 80)
result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)

if not result.isError():
    print(f"\nSuccessfully read {len(result.registers)} registers\n")
    print("First 21 registers:")
    print("-" * 80)
    for i, (addr, name) in enumerate(REGISTER_NAMES):
        raw_value = result.registers[i]
        print(f"Index {i:2d} | Addr 0x{addr:04X} | Raw: {raw_value:5d} | {name}")
else:
    print(f"Error: {result}")

print("\n" + "=" * 80)
print("INDIVIDUAL READS - Reading same registers one by one")
print("=" * 80)
print("\nFirst 21 registers:")
print("-" * 80)
for i, (addr, name) in enumerate(REGISTER_NAMES):
    result = client.read_holding_registers(addr, count=1, device_id=DEVICE_ADDRESS)
    if not result.isError() and len(result.registers) > 0:
        raw_value = result.registers[0]
        print(f"Index {i:2d} | Addr 0x{addr:04X} | Raw: {raw_value:5d} | {name}")
    else:
        print(f"Index {i:2d} | Addr 0x{addr:04X} | ERROR | {name}")

client.close()
