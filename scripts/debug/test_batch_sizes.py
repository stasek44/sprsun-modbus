#!/usr/bin/env python3
"""
Test różnych rozmiarów batch read - znajdź stabilny rozmiar
"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("=" * 100)
print("TEST: Czy urządzenie zwraca zawsze tyle samo rejestrów?")
print("=" * 100)
print()

# Test różnych rozmiarów batch
batch_sizes = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

for requested_count in batch_sizes:
    print(f"\n{'=' * 100}")
    print(f"Testowanie batch size = {requested_count} rejestrów (0x0000 + {requested_count})")
    print(f"{'=' * 100}")
    
    returned_counts = []
    
    # 10 prób dla każdego rozmiaru
    for attempt in range(10):
        result = client.read_holding_registers(0x0000, count=requested_count, device_id=DEVICE_ADDRESS)
        
        if result.isError():
            print(f"  Próba {attempt+1}: ERROR")
            returned_counts.append(-1)
        else:
            returned = len(result.registers)
            returned_counts.append(returned)
            
            if returned != requested_count:
                print(f"  Próba {attempt+1}: Requested={requested_count}, GOT={returned} ⚠️ NIEZGODNOŚĆ!")
            else:
                print(f"  Próba {attempt+1}: OK - otrzymano {returned} rejestrów")
        
        time.sleep(0.2)
    
    # Podsumowanie
    unique_counts = set(returned_counts)
    print(f"\n  PODSUMOWANIE dla batch size={requested_count}:")
    print(f"    Unikalne wartości zwrócone: {unique_counts}")
    
    if len(unique_counts) == 1 and requested_count in unique_counts:
        print(f"    ✓ STABILNY - zawsze {requested_count} rejestrów")
    else:
        print(f"    ✗ NIESTABILNY - różne liczby rejestrów!")
        for count in unique_counts:
            occurrences = returned_counts.count(count)
            print(f"      {count} rejestrów: {occurrences}/10 razy ({occurrences*10}%)")

client.close()

print("\n" + "=" * 100)
print("Szukaj batch size, który pokazuje: '✓ STABILNY'")
print("=" * 100)
