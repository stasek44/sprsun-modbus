#!/usr/bin/env python3
"""
Zmierz rzeczywisty czas requestu Modbus
To pomoże określić optymalny poll interval
"""

from pymodbus.client import ModbusTcpClient
import time
import statistics

MODBUS_HOST = "192.168.1.234"
MODBUS_PORT = 502
DEVICE_ADDRESS = 1

def measure_single_request():
    """Zmierz czas pojedynczego requestu batch 50 rejestrów"""
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT, timeout=3)
    
    if not client.connect():
        print("❌ Nie można połączyć z Modbus")
        return None
    
    times = []
    register_counts = []
    
    print("="*80)
    print("POMIAR CZASU REQUESTU - 20 prób")
    print("="*80)
    
    for i in range(20):
        start = time.time()
        result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
        elapsed = time.time() - start
        
        if result.isError():
            print(f"  Próba {i+1:2d}: ✗ ERROR (czas: {elapsed:.3f}s)")
        else:
            count = len(result.registers)
            times.append(elapsed)
            register_counts.append(count)
            
            status = "✓" if count == 50 else "✗"
            print(f"  Próba {i+1:2d}: {status} {elapsed:.3f}s, {count} rejestrów")
        
        time.sleep(0.5)  # Krótki delay między testami
    
    client.close()
    
    if not times:
        print("\n❌ Wszystkie requesty się nie powiodły!")
        return None
    
    # Statystyki
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    median_time = statistics.median(times)
    
    ok_count = sum(1 for c in register_counts if c == 50)
    bad_count = len(register_counts) - ok_count
    
    print("\n" + "="*80)
    print("WYNIKI")
    print("="*80)
    print(f"\nCzas requestu:")
    print(f"  Średni:   {avg_time:.3f}s")
    print(f"  Mediana:  {median_time:.3f}s")
    print(f"  Min:      {min_time:.3f}s")
    print(f"  Max:      {max_time:.3f}s")
    
    print(f"\nPoprawność:")
    print(f"  OK (50 reg):  {ok_count}/20 ({ok_count*5}%)")
    print(f"  BAD (≠50):    {bad_count}/20 ({bad_count*5}%)")
    
    return avg_time


def recommend_poll_interval(request_time):
    """Zaproponuj optymalny poll interval na podstawie czasu requestu"""
    print("\n" + "="*80)
    print("REKOMENDACJE POLL INTERVAL")
    print("="*80)
    
    print(f"\nObecne ustawienia Elfin (domyślnie):")
    print(f"  Timeout: 120s")
    print(f"  Poll interval: 5s")
    print(f"  Requesty 'w locie': 120 / 5 = 24 ← PROBLEM!")
    
    print(f"\n⚠️  Z obecnym Elfin Timeout = 120s:")
    print(f"  Minimum poll interval: 120s (2 minuty)")
    print(f"  Bezpieczny poll:       240s (4 minuty)")
    print(f"  Wniosek: ZA WOLNO dla Home Assistant!")
    
    print(f"\n✅ PO ZMIANIE Elfin Timeout → 5s:")
    
    # Oblicz rekomendacje
    safe_poll = max(10, request_time * 3)  # 3× request time lub min 10s
    aggressive_poll = max(5, request_time * 2)  # 2× request time lub min 5s
    
    print(f"  Request trwa:          {request_time:.2f}s")
    print(f"  Bezpieczny poll:       {safe_poll:.0f}s (3× request time)")
    print(f"  Agresywny poll:        {aggressive_poll:.0f}s (2× request time)")
    print(f"  Bardzo agresywny:      {max(3, request_time):.0f}s (ryzykowne!)")
    
    print(f"\n🎯 REKOMENDACJA:")
    print(f"   1. Zmień Elfin Timeout: 120s → 5s")
    print(f"   2. Ustaw poll interval: {safe_poll:.0f}s")
    print(f"   3. Dla HA: odczyt co {safe_poll:.0f}s = {60/safe_poll:.1f} razy/minutę")
    
    if request_time > 2:
        print(f"\n⚠️  UWAGA: Request trwa > 2s!")
        print(f"   To sugeruje problem z:")
        print(f"   - Parametrami UART (zbyt niski baudrate?)")
        print(f"   - Siecią (wolne WiFi? packet loss?)")
        print(f"   - Gateway (Elfin W11 przeciążony?)")
        print(f"   Sprawdź konfigurację!")
    elif request_time < 0.5:
        print(f"\n✓ Request < 0.5s - świetnie!")
        print(f"  Możesz użyć krótszych poll intervals (5-10s)")


def test_poll_conflicts():
    """Symuluj konflikt: próbuj pollować zbyt szybko"""
    print("\n" + "="*80)
    print("TEST: Symulacja konfliktu (poll co 2s przez 30s)")
    print("="*80)
    print("Sprawdzamy czy szybki polling powoduje problemy...\n")
    
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT, timeout=3)
    
    if not client.connect():
        print("❌ Nie można połączyć")
        return
    
    start_time = time.time()
    ok_count = 0
    bad_count = 0
    error_count = 0
    attempt = 0
    
    while time.time() - start_time < 30:
        attempt += 1
        result = client.read_holding_registers(0x0000, count=50, device_id=DEVICE_ADDRESS)
        
        if result.isError():
            error_count += 1
            print(f"  {attempt:2d}. ERROR")
        else:
            count = len(result.registers)
            if count == 50:
                ok_count += 1
                print(f"  {attempt:2d}. OK (50 reg)")
            else:
                bad_count += 1
                print(f"  {attempt:2d}. BAD ({count} reg) ← Konflikt!")
        
        time.sleep(2)  # Agresywny poll co 2s
    
    client.close()
    
    total = ok_count + bad_count + error_count
    print(f"\nWYNIKI (poll co 2s przez 30s):")
    print(f"  OK:     {ok_count}/{total} ({ok_count*100//total if total > 0 else 0}%)")
    print(f"  BAD:    {bad_count}/{total} ({bad_count*100//total if total > 0 else 0}%)")
    print(f"  ERROR:  {error_count}/{total} ({error_count*100//total if total > 0 else 0}%)")
    
    if bad_count > 0 or error_count > 0:
        print(f"\n❌ Poll co 2s POWODUJE PROBLEMY!")
        print(f"   Konflikt requestów → buffer overflow")
        print(f"   Rozwiązanie: Zwiększ poll interval LUB zmień Elfin Timeout")
    else:
        print(f"\n✅ Poll co 2s działa! Elfin może mieć już zmieniony timeout.")


if __name__ == "__main__":
    print("="*80)
    print("DIAGNOZA: Czas requestu i optymalny poll interval")
    print("="*80)
    print()
    
    # Test 1: Zmierz czas requestu
    avg_time = measure_single_request()
    
    if avg_time:
        # Test 2: Zaproponuj ustawienia
        recommend_poll_interval(avg_time)
        
        # Test 3: Sprawdź czy szybki polling powoduje problemy
        print("\n" + "="*80)
        input("Naciśnij ENTER aby uruchomić test konfliktu (30s)...")
        test_poll_conflicts()
    
    print("\n" + "="*80)
    print("PODSUMOWANIE")
    print("="*80)
    print("""
NASTĘPNE KROKI:

1. ✅ Zmierzyłeś rzeczywisty czas requestu
2. ⏭  Zmień parametry Elfin W11:
   - Zaloguj: http://192.168.1.234
   - Timeout: 120s → 5s
   - Buffer: 1024 → 512 (opcjonalnie)
   
3. ⏭  Dostosuj poll interval w skryptach:
   - modbus_poller.py: time.sleep(5) → time.sleep(10)
   - modbus_batch_poller.py: POLL_INTERVAL = 10
   
4. ⏭  Test ponownie:
   python measure_request_time.py
   
5. ⏭  Jeśli stabilne → wdrożenie produkcyjne!
""")
