#!/usr/bin/env python3
"""
Test różnych ustawień komunikacji z Elfin W11
Sprawdź które zmiany poprawiają stabilność
"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

def test_with_settings(description, timeout=3, retries=3):
    """Test z różnymi ustawieniami pymodbus"""
    print(f"\n{'='*100}")
    print(f"TEST: {description}")
    print(f"{'='*100}")
    
    # Utwórz klienta z określonymi ustawieniami
    client = ModbusTcpClient(
        MODBUS_HOST, 
        port=MODBUS_PORT,
        timeout=timeout,  # Timeout dla pojedynczego requestu
        retries=retries,  # Ile razy spróbować ponownie
    )
    
    if not client.connect():
        print("❌ Nie można połączyć")
        return
    
    results = []
    
    for attempt in range(20):
        result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
        
        if result.isError():
            results.append(("ERROR", 0))
            print(f"  Próba {attempt+1:2d}: ERROR")
        else:
            count = len(result.registers)
            results.append(("OK" if count == 50 else "BAD", count))
            
            if count == 50:
                print(f"  Próba {attempt+1:2d}: ✓ {count} rejestrów")
            else:
                print(f"  Próba {attempt+1:2d}: ✗ {count} rejestrów (expected 50)")
        
        # Dodaj delay między requestami
        time.sleep(0.2)
    
    client.close()
    
    # Statystyki
    ok_count = sum(1 for status, count in results if status == "OK")
    bad_count = sum(1 for status, count in results if status == "BAD")
    error_count = sum(1 for status, count in results if status == "ERROR")
    
    print(f"\n  WYNIKI:")
    print(f"    ✓ OK (50 reg):  {ok_count}/20 ({ok_count*5}%)")
    print(f"    ✗ BAD (≠50):    {bad_count}/20 ({bad_count*5}%)")
    print(f"    ⚠ ERROR:         {error_count}/20 ({error_count*5}%)")
    
    return ok_count, bad_count, error_count


print("="*100)
print("TESTY: Jak różne ustawienia wpływają na stabilność?")
print("="*100)

# Test 1: Domyślne ustawienia (timeout 3s)
test_with_settings("Domyślne: timeout=3s, retries=3", timeout=3, retries=3)

# Test 2: Krótszy timeout (szybkie fail dla złych odpowiedzi)
test_with_settings("Krótki timeout: timeout=1s, retries=1", timeout=1, retries=1)

# Test 3: Dłuższy timeout (więcej czasu dla Elfin)
test_with_settings("Długi timeout: timeout=5s, retries=0", timeout=5, retries=0)

# Test 4: Bez retry (nie próbuj ponownie jeśli coś pójdzie źle)
test_with_settings("Bez retry: timeout=2s, retries=0", timeout=2, retries=0)

print("\n" + "="*100)
print("WNIOSKI:")
print("="*100)
print("""
1. Jeśli krótszy timeout pomaga → Elfin buffering problem
2. Jeśli dłuższy timeout pomaga → UART za wolny lub pompa za wolna
3. Jeśli retries=0 pomaga → powtarzane requesty zaśmiecają bufor
4. Jeśli nic nie pomaga → trzeba zmienić ustawienia Elfin W11
""")
