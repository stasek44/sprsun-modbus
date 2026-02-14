#!/usr/bin/env python3
"""Quick test to see what batch read returns"""

from pymodbus.client import ModbusTcpClient

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("Testing batch read of 50 registers (0x0000 to 0x0031)")
result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)

print(f"isError: {result.isError()}")
print(f"Number of registers returned: {len(result.registers)}")
print(f"First 5 registers: {result.registers[:5]}")
print(f"Last 5 registers: {result.registers[-5:]}")

client.close()
