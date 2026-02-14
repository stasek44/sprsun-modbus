#!/usr/bin/env python3
"""
Test małych batchy jako rozwiązanie problemu
Jeśli batch 50 nie działa, może 5× batch 10 będzie stabilny?
"""

from pymodbus.client import ModbusTcpClient
import time

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

def test_small_batches(batch_size=10, total_registers=50, attempts=50):
    """
    Test czytania w małych paczkach
    
    Args:
        batch_size: Rozmiar pojedynczego batcha
        total_registers: Całkowita liczba rejestrów do przeczytania
        attempts: Ile razy powtórzyć test
    """
    print(f"\n{'='*100}")
    print(f"TEST: Batch size = {batch_size} (całość: {total_registers} rejestrów)")
    print(f"{'='*100}")
    
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT, timeout=3)
    
    if not client.connect():
        print("❌ Nie można połączyć")
        return None
    
    success_count = 0
    fail_count = 0
    error_count = 0
    
    for attempt in range(attempts):
        all_ok = True
        all_registers = []
        
        # Przeczytaj w małych paczkach
        for start_addr in range(0x0000, total_registers, batch_size):
            # Oblicz ile rejestrów czytać (może być < batch_size na końcu)
            count = min(batch_size, total_registers - start_addr)
            
            result = client.read_holding_registers(start_addr, count=count, device_id=DEVICE_ADDRESS)
            
            if result.isError():
                all_ok = False
                error_count += 1
                print(f"  Próba {attempt+1:2d}: ✗ ERROR przy adresie 0x{start_addr:04X}")
                break
            elif len(result.registers) != count:
                all_ok = False
                fail_count += 1
                print(f"  Próba {attempt+1:2d}: ✗ BAD przy 0x{start_addr:04X} (oczekiwano {count}, otrzymano {len(result.registers)})")
                break
            else:
                all_registers.extend(result.registers)
            
            # Mały delay między batchami
            time.sleep(0.1)
        
        if all_ok:
            if len(all_registers) == total_registers:
                success_count += 1
                print(f"  Próba {attempt+1:2d}: ✓ OK (wszystkie {total_registers} rejestrów)")
            else:
                fail_count += 1
                print(f"  Próba {attempt+1:2d}: ✗ Otrzymano {len(all_registers)} zamiast {total_registers}")
        
        # Delay między pełnymi cyklami
        time.sleep(0.2)
    
    client.close()
    
    # Statystyki
    print(f"\n  WYNIKI (batch size = {batch_size}):")
    print(f"    ✓ Sukces:  {success_count}/{attempts} ({success_count*100//attempts}%)")
    print(f"    ✗ Błędne:  {fail_count}/{attempts} ({fail_count*100//attempts}%)")
    print(f"    ⚠ Errory:  {error_count}/{attempts} ({error_count*100//attempts}%)")
    
    return success_count


print("="*100)
print("TEST MAŁYCH BATCHY: Czy małe paczki są bardziej stabilne?")
print("="*100)
print("\nCel: Znaleźć optymalny rozmiar batcha dla stabilności 100%\n")

# Test różnych rozmiarów batch
results = {}

# Test 1: Pojedyncze rejestry (baseline - wiemy że działa 100%)
print("\n" + "="*100)
print("BASELINE: Pojedyncze odczyty (wiemy że to działa)")
print("="*100)
print("(Pomijamy, żeby zaoszczędzić czas - wiemy że jest 100% stabilny)")

# Test 2-7: Różne rozmiary batchy
for batch_size in [5, 8, 10, 12, 15, 20]:
    success = test_small_batches(batch_size=batch_size, total_registers=50, attempts=50)
    if success is not None:
        results[batch_size] = success
    time.sleep(1)  # Pauza między testami

# Podsumowanie
print("\n" + "="*100)
print("PODSUMOWANIE")
print("="*100)

print("\nStabilność dla różnych rozmiarów batch:")
print("-" * 50)
for batch_size in sorted(results.keys()):
    success_rate = results[batch_size] * 100 // 50
    bar = "█" * (success_rate // 2)  # Progress bar
    print(f"  Batch {batch_size:2d}: {success_rate:3d}% {bar}")

# Znajdź najlepszy rozmiar
if results:
    best_size = max(results.keys(), key=lambda k: results[k])
    best_rate = results[best_size] * 100 // 50
    
    print(f"\n✅ NAJLEPSZY ROZMIAR: {best_size} rejestrów ({best_rate}% sukcesu)")
    
    if best_rate == 100:
        batches_needed = (50 + best_size - 1) // best_size  # Zaokrąglij w górę
        print(f"\n🎯 REKOMENDACJA:")
        print(f"   - Czytaj w {batches_needed} paczkach po {best_size} rejestrów")
        print(f"   - Będzie {batches_needed}× szybsze niż 50 pojedynczych odczytów")
        print(f"   - Stabilność: 100%")
    elif best_rate >= 95:
        print(f"\n⚠️  95%+ sukcesu jest wystarczające z fallbackiem do individual reads")
    else:
        print(f"\n❌ Żaden batch size nie daje 95%+ stabilności")
        print(f"   Rozwiązanie: Zostań przy individual reads lub zmień ustawienia Elfin W11")
else:
    print("\n❌ Wszystkie testy się nie powiodły - problem z połączeniem")

print("\n" + "="*100)
print("NASTĘPNE KROKI:")
print("="*100)
print("""
1. Jeśli znaleziono stabilny batch size:
   → Zmodyfikuj modbus_batch_poller.py aby używał małych batchy
   
2. Jeśli żaden batch nie jest 100% stabilny:
   → Zmień ustawienia Elfin W11 (patrz: ELFIN_W11_RECOMMENDED_SETTINGS.md)
   → Timeout: 120s → 5s
   → Buffer: 1024 → 512 bytes
   
3. Jeśli nic nie pomaga:
   → Zostań przy modbus_poller.py (individual reads)
   → Jest wolny (~5s) ale 100% niezawodny
""")
