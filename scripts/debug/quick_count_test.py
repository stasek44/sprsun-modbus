#!/usr/bin/env python3
"""Quick test: What counts does device return?"""

from pymodbus.client import ModbusTcpClient
import time
from collections import Counter

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("Quick test: 30 batch reads, checking register count...")
print()

counts = []
anomalies = []

for i in range(30):
    result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
    
    if result.isError():
        counts.append(-1)
        print(f"{i+1}. ERROR")
        continue
    
    count = len(result.registers)
    counts.append(count)
    
    if count != 50:
        anom = {
            'read': i+1,
            'count': count, 
            'first': result.registers[0] if count > 0 else None,
            'last': result.registers[-1] if count > 0 else None,
            'first_3': result.registers[:3] if count >= 3 else result.registers[:count],
            'last_3': result.registers[-3:] if count >= 3 else result.registers[:count]
        }
        anomalies.append(anom)
        if count > 0:
            print(f"{i+1}. ❌ {count} registers (expected 50!) - first=[{anom['first']}], last=[{anom['last']}]")
        else:
            print(f"{i+1}. ❌ {count} registers - EMPTY!")
    else:
        print(f"{i+1}. ✓ {count} registers")
    
    time.sleep(0.15)

print("\n" + "=" * 80)
print("WYNIKI:")
print("=" * 80)

counter = Counter(counts)
for count, freq in sorted(counter.items()):
    pct = freq/len(counts)*100
    status = "✓" if count == 50 else "❌"
    print(f"{status} Count {count:3d}: {freq:2d}x ({pct:5.1f}%)")

if anomalies:
    print("\n" + "=" * 80)
    print("ANOMALIE - szczegóły:")
    print("=" * 80)
    for anom in anomalies:
        print(f"\nOdczyt #{anom['read']}: {anom['count']} rejestrów")
        print(f"  Pierwsze 3: {anom['first_3']}")
        print(f"  Ostatnie 3: {anom['last_3']}")

print("\n" + "=" * 80)
print("WNIOSKI:")
print("=" * 80)
if len(counter) == 1 and 50 in counter:
    print("✓ Urządzenie ZAWSZE zwraca 50 rejestrów")
    print("  → Problem to MAPOWANIE (które rejestry są zwracane)")
else:
    print("❌ Urządzenie zwraca ZMIENNĄ liczbę rejestrów!")
    print("  → To gorsze niż spodziewaliśmy się")
    print(f"  → Zaobserwowano {len(counter)} różnych wartości")

client.close()
