#!/usr/bin/env python3
"""Szybki test - czy liczba rejestrów jest stała?"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("Test 1: Czy batch size=50 zwraca zawsze 50 rejestrów?")
print("=" * 80)

counts_50 = []
for i in range(20):
    result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
    count = len(result.registers) if not result.isError() else -1
    counts_50.append(count)
    print(f"Próba {i+1:2d}: {count} rejestrów")
    time.sleep(0.1)

print(f"\nUnikalne wartości: {set(counts_50)}")
print(f"Min: {min(counts_50)}, Max: {max(counts_50)}, Stabilny: {len(set(counts_50)) == 1}")

print("\n" + "=" * 80)
print("Test 2: Czy batch size=20 zwraca zawsze 20 rejestrów?")
print("=" * 80)

counts_20 = []
for i in range(20):
    result = client.read_holding_registers(0x0000, count=20, device_id=DEVICE_ADDRESS)
    count = len(result.registers) if not result.isError() else -1
    counts_20.append(count)
    print(f"Próba {i+1:2d}: {count} rejestrów")
    time.sleep(0.1)

print(f"\nUnikalne wartości: {set(counts_20)}")
print(f"Min: {min(counts_20)}, Max: {max(counts_20)}, Stabilny: {len(set(counts_20)) == 1}")

print("\n" + "=" * 80)
print("Test 3: Czy batch size=10 zwraca zawsze 10 rejestrów?")
print("=" * 80)

counts_10 = []
for i in range(20):
    result = client.read_holding_registers(0x0000, count=10, device_id=DEVICE_ADDRESS)
    count = len(result.registers) if not result.isError() else -1
    counts_10.append(count)
    print(f"Próba {i+1:2d}: {count} rejestrów")
    time.sleep(0.1)

print(f"\nUnikalne wartości: {set(counts_10)}")
print(f"Min: {min(counts_10)}, Max: {max(counts_10)}, Stabilny: {len(set(counts_10)) == 1}")

client.close()

print("\n" + "=" * 80)
print("WNIOSKI:")
print("=" * 80)
print(f"Batch 50: {'STABILNY ✓' if len(set(counts_50)) == 1 and 50 in counts_50 else 'NIESTABILNY ✗'}")
print(f"Batch 20: {'STABILNY ✓' if len(set(counts_20)) == 1 and 20 in counts_20 else 'NIESTABILNY ✗'}")
print(f"Batch 10: {'STABILNY ✓' if len(set(counts_10)) == 1 and 10 in counts_10 else 'NIESTABILNY ✗'}")
