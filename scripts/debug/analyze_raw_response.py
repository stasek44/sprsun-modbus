#!/usr/bin/env python3
"""
Analiza RAW odpowiedzi Modbus - co dokładnie zwraca urządzenie?
"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
client.connect()

print("=" * 100)
print("ANALIZA: Co zwraca urządzenie gdy prosimy o 50 rejestrów?")
print("=" * 100)
print()

for attempt in range(10):
    print(f"\n{'=' * 100}")
    print(f"Próba #{attempt + 1}")
    print('=' * 100)
    
    # Prosimy o 50 rejestrów
    requested_count = 50
    result = client.read_holding_registers(0x0000, count=requested_count, device_id=DEVICE_ADDRESS)
    
    print(f"\n1. Co zwrócił pymodbus.read_holding_registers():")
    print(f"   - result.isError() = {result.isError()}")
    
    if hasattr(result, 'function_code'):
        print(f"   - Function Code = {result.function_code}")
    
    if hasattr(result, 'registers'):
        actual_count = len(result.registers)
        print(f"   - Liczba rejestrów w result.registers = {actual_count}")
        print(f"   - Oczekiwana liczba = {requested_count}")
        
        if actual_count != requested_count:
            print(f"   - ⚠️  NIEZGODNOŚĆ! Różnica: {actual_count - requested_count}")
        else:
            print(f"   - ✓ OK")
    
    # Sprawdź czy są informacje o błędzie
    if hasattr(result, 'exception_code'):
        print(f"   - Exception Code = {result.exception_code}")
    
    # Surowe informacje o odpowiedzi
    print(f"\n2. Szczegóły odpowiedzi Modbus:")
    print(f"   - Typ obiektu: {type(result)}")
    print(f"   - Atrybuty: {[attr for attr in dir(result) if not attr.startswith('_')]}")
    
    # Jeśli mamy registers, pokaż pierwsze i ostatnie
    if hasattr(result, 'registers') and len(result.registers) > 0:
        regs = result.registers
        print(f"\n3. Zawartość rejestrów:")
        print(f"   - Pierwsze 5: {regs[:5]}")
        print(f"   - Ostatnie 5: {regs[-5:]}")
        
        # W Modbus każdy rejestr to 16 bitów (2 bajty)
        total_bytes = len(regs) * 2
        print(f"\n4. Rozmiar danych:")
        print(f"   - Rejestrów: {len(regs)} × 16 bit = {len(regs) * 16} bitów = {total_bytes} bajtów")
        
        # Sprawdź czy to mogą być dane 32-bitowe zakodowane jako 2x16-bit
        print(f"\n5. Analiza: Czy to mogą być wartości 32-bitowe?")
        print(f"   - Jeśli tak, {len(regs)} rejestrów = {len(regs)//2} wartości 32-bitowych")
        print(f"   - Ale dokumentacja mówi o {requested_count} pojedynczych rejestrach 16-bit")
    
    time.sleep(0.2)

client.close()

print("\n" + "=" * 100)
print("WNIOSKI:")
print("=" * 100)
print("""
W Modbus:
- Każdy REJESTR = 16 bitów (2 bajty)
- Wartość 32-bitowa = 2 rejestry
- Stringi = N rejestrów (2N znaków ASCII)

Jeśli dostajemy 110 rejestrów zamiast 50:
- To 220 bajtów zamiast 100 bajtów
- Ponad 2x więcej danych niż prosiliśmy!
- To NIE może być kwestia pomyłki 16-bit vs 32-bit
""")
