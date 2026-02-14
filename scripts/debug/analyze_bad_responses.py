#!/usr/bin/env python3
"""
Zbadaj wzorzec "złych" odpowiedzi - co oznaczają te wartości 60, 70?
"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("=" * 100)
print("TEST: Gdy dostajemy >50 rejestrów, co to za dane?")
print("=" * 100)
print()

good_responses = []
bad_responses = []

for attempt in range(30):
    result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
    
    if result.isError():
        continue
    
    count = len(result.registers)
    
    if count == 50:
        good_responses.append(result.registers[:10])  # Pierwsze 10
        print(f"Próba {attempt+1:2d}: ✓ 50 rejestrów - OK")
    else:
        bad_responses.append((count, result.registers[:10], result.registers[-10:]))
        print(f"Próba {attempt+1:2d}: ✗ {count} rejestrów - BAD")
        print(f"  Pierwsze 10: {result.registers[:10]}")
        print(f"  Ostatnie 10: {result.registers[-10:]}")
    
    time.sleep(0.1)

client.close()

print("\n" + "=" * 100)
print("ANALIZA WZORCÓW:")
print("=" * 100)

if good_responses:
    print(f"\n✓ DOBRE odpowiedzi (50 rejestrów) - zebranych: {len(good_responses)}")
    print(f"  Przykładowa pierwsza 10: {good_responses[0]}")
    
    # ASCII check - czy to nie są przypadkiem znaki?
    first_vals = good_responses[0][:5]
    print(f"\n  Pierwszych 5 wartości jako ASCII:")
    for val in first_vals:
        char = chr(val) if 32 <= val <= 126 else '?'
        print(f"    {val:5d} (0x{val:04X}) → '{char}'")

if bad_responses:
    print(f"\n✗ ZŁE odpowiedzi (≠50 rejestrów) - zebranych: {len(bad_responses)}")
    
    for i, (count, first10, last10) in enumerate(bad_responses[:3], 1):
        print(f"\n  Przykład #{i}: {count} rejestrów")
        print(f"    Pierwsze 10: {first10}")
        
        # Sprawdź czy to nie są ASCII znaki
        print(f"    Jako ASCII: ", end='')
        for val in first10:
            char = chr(val) if 32 <= val <= 126 else '?'
            print(f"'{char}'", end=' ')
        print()
        
        # Sprawdź wzorzec
        if len(set(first10)) == 1:
            print(f"    ⚠️  WZORZEC: Wszystkie wartości identyczne = {first10[0]}")
        
        # Sprawdź czy wartości są w sensownym zakresie dla naszych rejestrów
        print(f"    Ostatnie 10: {last10}")

print("\n" + "=" * 100)
print("HIPOTEZY:")
print("=" * 100)
print("""
1. Jeśli wartości 60,70 powtarzają się → może to buffer padding (ASCII '<' '>' ?)
2. Jeśli wartości są losowe → może to dane z innego zapytania
3. Jeśli CRC się zgadza → firmware faktycznie wysyła więcej danych
4. Dekodowanie w pymodbus jest automatyczne - nie trzeba ręcznie parsować
""")
