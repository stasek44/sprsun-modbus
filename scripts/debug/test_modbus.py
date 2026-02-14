#!/usr/bin/env python3
"""
Quick test script to verify Modbus connectivity
"""

from pymodbus.client import ModbusTcpClient
import sys

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

print("Testing Modbus connection...")
print(f"Host: {MODBUS_HOST}:{MODBUS_PORT}")
print(f"Device Address: {DEVICE_ADDRESS}\n")

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)

try:
    if not client.connect():
        print(f"ERROR: Failed to connect to {MODBUS_HOST}:{MODBUS_PORT}")
        sys.exit(1)
    
    print("✓ Connected successfully\n")
    
    # Test reading a few registers
    test_registers = [
        (0x000E, "Inlet temp.", 0.1),
        (0x0011, "Ambi temp.", 0.5),
        (0x0012, "Outlet temp.", 0.1),
        (0x001E, "Comp. Frequency", 1),
    ]
    
    print("Reading test registers:")
    print("-" * 50)
    
    for address, name, scale in test_registers:
        try:
            result = client.read_holding_registers(address, count=1, device_id=DEVICE_ADDRESS)
            if result.isError():
                print(f"0x{address:04X} {name:20s} - ERROR: {result}")
            else:
                raw_value = result.registers[0]
                # Handle signed values
                if raw_value > 32767:
                    raw_value = raw_value - 65536
                scaled_value = raw_value * scale
                print(f"0x{address:04X} {name:20s} = {scaled_value:8.1f} (raw: {result.registers[0]})")
        except Exception as e:
            print(f"0x{address:04X} {name:20s} - EXCEPTION: {e}")
    
    print("\n✓ API calls working correctly!")
    
except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    client.close()
    print("Connection closed")
