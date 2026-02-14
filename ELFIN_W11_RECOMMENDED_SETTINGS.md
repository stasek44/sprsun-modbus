# Elfin W11 - Rekomendowane Ustawienia dla Modbus

## 🔴 PROBLEMATYCZNE USTAWIENIA (aktualne):
```
Buffer: 1024 bytes           ← za duży! dane się gromadzą
Timeout: 120s                ← ZA DŁUGI! (powinno być 2-5s)
Keep alive: 65s              ← OK
Max accept: 3                ← możliwe race conditions

⚠️ KRYTYCZNY PROBLEM:
Poll interval: 5s            ← 24× KRÓCEJ niż timeout!
Rezultat: 120s / 5s = 24 requesty "w locie" jednocześnie
Buffer overflow: 24 × 108 bajtów = 2592 bajty > 1024 limit!
```

## ✅ PROPOZYCJE ZMIAN:

### 1. **TIMEOUT: 120s → 5s** (PRIORYTET #1)
**Dlaczego:**
- Modbus TCP odpowiedzi powinny przychodzić w **< 1 sekundę**
- Timeout 120s = dane mogą siedzieć w buforze 2 minuty!
- Za długi timeout = stare dane zaśmiecają bufor
- **NAJWAŻNIEJSZE:** Timeout 120s + poll co 5s = 24 requesty jednocześnie → buffer overflow!

**Matematyka:**
```
Obecne: 120s timeout / 5s poll = 24 requesty "w locie"
        24 requesty × 108 bajtów = 2592 bajty > 1024 buffer ← OVERFLOW!

Po zmianie: 5s timeout / 10s poll = 0.5 requestów "w locie"  
            1 request × 108 bajtów = 108 bajty < 1024 buffer ← OK!
```

**Zmień na:**
```
Timeout: 5s          (wystarczy 5 sekund, nawet 2-3s powinno działać)
```

**⚠️ WAŻNE:** Po zmianie timeout musisz też dostosować poll interval w skrypcie!
```python
# W modbus_poller.py / modbus_batch_poller.py:
POLL_INTERVAL = 10  # sekund (2× timeout = bezpieczne)
# REGUŁA: Poll Interval ≥ 2 × Elfin Timeout
```

**Test po zmianie:**
```bash
.venv/bin/python test_elfin_settings.py
```

---

### 2. **BUFFER: 1024 bytes → 512 bytes** (PRIORYTET #2)
**Dlaczego:**
- Pojedyncza odpowiedź Modbus: ~108 bajtów (50 rejestrów × 2 bajty + overhead)
- Buffer 1024 = może pomieścić **9 odpowiedzi naraz**
- Stare dane z poprzednich requestów zaśmiecają nowe odpowiedzi

**Zmień na:**
```
Buffer: 256 bytes    (lub 512 bytes - wystarczy na 2-3 odpowiedzi max)
```

**Jeśli nie można zmienić:**
- Dodaj "flush buffer" między requestami (jeśli Elfin to wspiera)

---

### 3. **MAX ACCEPT: 3 → 1** (PRIORYTET #3)
**Dlaczego:**
- Max accept 3 = **do 3 klientów naraz może pytać pompę**
- Możliwe race conditions:
  - Twój skrypt Python
  - Home Assistant (jeśli już skonfigurowałeś)
  - Aplikacja mobilna?
  - Inny skrypt?
  
**Zmień na:**
```
Max accept: 1        (tylko jedna aplikacja naraz)
```

**Sprawdź NAJPIERW:**
1. Czy tylko twój skrypt łączy się z Elfin?
2. Czy Home Assistant **nie** próbuje się łączyć?
3. Czy aplikacja mobilna nie używa TCP 502?

---

### 4. **KEEP ALIVE: 65s** (OK, nie zmieniaj)
**Status:** 65 sekund jest OK dla keep alive

---

### 5. **POLL INTERVAL w skryptach Python** (PRIORYTET #1B - RÓWNIE WAŻNE!)

**Obecny problem:**
```python
# modbus_poller.py, linia z time.sleep(5):
time.sleep(5)  # Poll co 5 sekund

# Elfin Timeout = 120s
# 120s / 5s = 24 requesty czekają jednocześnie!
# Buffer overflow gwarantowany!
```

**REGUŁA ZŁOTA:**
```
Poll Interval ≥ 2 × Elfin Timeout
```

**Dostosuj do nowego timeout:**

| Elfin Timeout | Minimum Poll | Bezpieczny Poll | Home Assistant |
|---------------|--------------|-----------------|----------------|
| 120s (teraz)  | 120s         | 240s (4 min)    | ❌ Za wolno     |
| 5s (ZMIEŃ!)   | 5s           | 10s             | ✅ Idealne     |
| 3s            | 3s           | 6s              | ✅ Świetne     |

**Po zmianie Elfin Timeout → 5s, zmień w skryptach:**

```python
# modbus_poller.py:
POLL_INTERVAL = 10  # sekund (było 5)

# modbus_batch_poller.py:
POLL_INTERVAL = 10  # sekund (było 5)
BATCH_DELAY = 0.1   # sekund między małymi batchami (OK)
```

**Dlaczego 10s a nie 5s?**
- 10s = 2× timeout (bezpieczny margines)
- 5s = 1× timeout (ryzykowne, ciasno)
- 3s = < timeout (overflow znowu!)

**Dla Home Assistant:**
- 10s poll = 6 odczytów na minutę
- Wystarczające dla monitoringu temperatury/ciśnienia
- Szybsze = ryzyko niestabilności

---

## 🧪 PLAN TESTÓW:

### Krok 0: Zmierz rzeczywisty czas requestu
```bash
.venv/bin/python -c "
from pymodbus.client import ModbusTcpClient
import time
client = ModbusTcpClient('192.168.1.234', port=502, timeout=3)
client.connect()
start = time.time()
result = client.read_holding_registers(0x0000, count=50, device_id=1)
elapsed = time.time() - start
print(f'Request trwał: {elapsed:.2f}s')
print(f'Rejestrów otrzymano: {len(result.registers)}')
print(f'Expected: 50')
client.close()
"
# Jeśli < 1s → OK!
# Jeśli > 5s → problem z Elfin lub UART
```

### Krok 1: Test PRZED zmianami
```bash
.venv/bin/python quick_batch_test.py
# Oczekiwany wynik: ~80% OK, ~20% źle (110/112 rejestrów)
```

### Krok 2: Zmień Timeout 120s → 5s w Elfin W11
**Jak zmienić:**
1. Zaloguj się do interfejsu webowego Elfin: http://192.168.1.234
2. Szukaj sekcji "TCP Server" lub "Network Settings"
3. Znajdź "Timeout" lub "Connection Timeout"
4. Zmień z 120 na 5 (sekund)
5. ZAPISZ i RESTART Elfin W11

### Krok 3: Zmień Poll Interval w skryptach Python
**W modbus_poller.py i modbus_batch_poller.py:**
```python
# Było:
time.sleep(5)

# Zmień na:
POLL_INTERVAL = 10  # 2× Elfin Timeout = bezpieczne
# ...
time.sleep(POLL_INTERVAL)
```

### Krok 4: Test PO zmianach timeout + poll interval
```bash
.venv/bin/python quick_batch_test.py
# Jeśli poprawiło → sukces! Jeśli nie → przejdź do kroku 5
```

### Krok 5: Zmień Buffer 1024 → 512 bytes
**Jak zmienić:**
1. Szukaj w Elfin: "Buffer Size" lub "RX Buffer" / "TX Buffer"
2. Zmień na 512 (lub najmniejszą możliwą wartość > 256)
3. ZAPISZ i RESTART

### Krok 6: Test PO zmianie buffer
```bash
.venv/bin/python quick_batch_test.py
# Jeśli teraz 100% → brawo!
```

### Krok 7: Zmień Max Accept 3 → 1
**Uwaga:** Najpierw sprawdź czy nic innego się nie łączy!
```bash
# Sprawdź aktywne połączenia:
netstat -anp | grep 192.168.1.234:502

# Jeśli widzisz tylko swój skrypt → zmień na 1
# Jeśli są inne połączenia → zidentyfikuj je najpierw
```

```bash
.venv/bin/python quick_batch_test.py
# Jeśli nadal nie działa → problem jest gdzie indziej
```

---

## 📊 OCZEKIWANE WYNIKI:

| Zmiana | Oczekiwana Poprawa | Powód |
|--------|-------------------|-------|
| Timeout 120s→5s | **+40-60%** stabilności | Requesty nie zalegają w buforze 2 minuty |
| Poll 5s→10s | **+30-50%** stabilności | Brak nakładania się requestów |
| Buffer 1024→512 | **+20-30%** stabilności | Mniej miejsca na stare dane |
| Max accept 3→1 | **+10-20%** stabilności | Brak race conditions |
| **WSZYSTKIE 4** | **95-100%** stabilności | Eliminacja głównych przyczyn |

**KLUCZOWA ZMIANA:** Timeout + Poll Interval razem dają największą poprawę!
```
Timeout 120s + Poll 5s = 24 requesty w locie → OVERFLOW
Timeout 5s + Poll 10s = 1 request w locie → STABILNE
```

---

## 🔍 DIAGNOSTYKA:

### Sprawdź co jeszcze łączy się do Elfin:
```bash
# Na komputerze Linux:
sudo netstat -anp | grep 192.168.1.234:502

# Lub:
ss -tnp | grep 192.168.1.234:502
```

**Szukaj:**
- Czy jest więcej niż 1 połączenie ESTABLISHED?
- Skąd pochodzą te połączenia? (IP source)

### Sprawdź logi Elfin W11:
1. Zaloguj się do http://192.168.1.234
2. Szukaj "Logs" lub "System Log"
3. Sprawdź czy są błędy typu:
   - "Buffer overflow"
   - "RX timeout"
   - "Multiple connections"

---

## ⚙️ PARAMETRY UART (do sprawdzenia):

Zapytaj producentę pompy SPRSUN o poprawne parametry RS485/UART:
- **Baudrate:** 9600? 19200? 115200?
- **Data bits:** 8
- **Parity:** None? Even? Odd?
- **Stop bits:** 1? 2?

**Aktualne ustawienia w Elfin:**
```
Szukaj w interfejsie webowym:
- Serial Settings
- UART Configuration
- RS485 Parameters
```

**Jeśli baudrate za niski:**
- 50 rejestrów × 2 bajty = 100 bajtów
- Przy 9600 baud = ~0.1 sekundy transmisji
- Przy 115200 baud = ~0.01 sekundy transmisji

**Nie zwiększaj baudrate bez potwierdzenia z pompą!**
(Może przestać działać całkowicie)

---

## 🎯 OSTATECZNE ROZWIĄZANIE:

### Opcja A: Batch z małymi paczkami (jeśli timeout/buffer fix zadziała)
```python
# Zamiast 1× 50 rejestrów, czytaj 5× 10 rejestrów
for start in range(0, 50, 10):
    result = client.read_holding_registers(start, count=10, device_id=1)
    # result będzie stabilny (małe paczki)
```

**Zalety:**
- Szybsze niż 50 pojedynczych odczytów
- Bardziej niezawodne niż 1 duża paczka

**Wady:**
- Nadal 5 requestów zamiast 1

---

### Opcja B: Individual reads (jeśli nic nie pomoże)
```python
# Stary sposób: 50 pojedynczych requestów
# Wolny (~5s), ale 100% niezawodny
for addr in range(0x0000, 0x0032):
    result = client.read_holding_registers(addr, count=1, device_id=1)
```

**Zalety:**
- 100% niezawodność
- Działa zawsze

**Wady:**
- Wolny (5 sekund na pełny odczyt)

---

## 📝 PYTANIA DO PRODUCENTA ELFIN:

Email do: support@hi-flying.com (lub sprawdź na elfin.cn)

```
Subject: Modbus TCP Buffer Issues - Elfin-EW11

Hi,

I'm using Elfin-EW11 as TCP-to-Serial gateway for Modbus communications.
Current settings:
- Buffer: 1024 bytes
- Timeout: 120s
- Keep alive: 65s
- Max accept: 3

Issue:
- Batch reads (50 registers) return inconsistent results
- Sometimes 50 registers (correct), sometimes 110 or 112 (wrong)
- Garbage data appears to be from buffer not clearing between requests

Questions:
1. What is recommended timeout for Modbus TCP applications?
2. Should buffer size be reduced to prevent data accumulation?
3. Is there a way to flush buffer between requests?
4. Any known issues with batch reads > 10 registers?

Thank you!
```

---

## ✅ CHECKLIST:

- [ ] **Zmierz rzeczywisty czas requestu** (Krok 0 z planu testów)
- [ ] Sprawdź aktualne ustawienia Elfin W11 w interfejsie webowym
- [ ] Zapisz screenshot obecnych ustawień (backup)
- [ ] **PRIORYTET #1A:** Zmień Timeout 120s → 5s
- [ ] **PRIORYTET #1B:** Zmień Poll Interval w skryptach: 5s → 10s
- [ ] Test: `python quick_batch_test.py`
- [ ] Jeśli nie pomoże: Zmień Buffer 1024 → 512
- [ ] Test: `python quick_batch_test.py`
- [ ] Jeśli nie pomoże: Zmień Max accept 3 → 1
- [ ] Test: `python quick_batch_test.py`
- [ ] Sprawdź czy jest więcej połączeń TCP: `netstat -anp | grep :502`
- [ ] Sprawdź parametry UART w Elfin vs dokumentacja SPRSUN
- [ ] Sprawdź logi w Elfin W11 (jeśli dostępne)
- [ ] Jeśli nic nie działa: Napisz do supportu Elfin
- [ ] Rozważ użycie małych batchy (10 rejestrów) zamiast 50

**⚠️ NIE ZAPOMNIJ:** Zmiana timeout bez zmiany poll interval NIE POMOŻE!
Musisz zmienić OBA parametry jednocześnie.

---

## 🚀 NASTĘPNE KROKI:

1. **Najpierw (DIAGNOZA):** Zmierz rzeczywisty czas requestu
   ```bash
   # Zobacz Krok 0 w planie testów
   ```

2. **Potem (NAPRAWA - część 1):** Zmień ustawienia Elfin W11
   - Timeout: 120s → 5s
   - Buffer: 1024 → 512 (opcjonalnie)
   - Max accept: 3 → 1 (opcjonalnie)

3. **RÓWNOCZEŚNIE (NAPRAWA - część 2):** Zmień poll interval w skryptach
   ```python
   # modbus_poller.py, modbus_batch_poller.py:
   POLL_INTERVAL = 10  # było 5
   time.sleep(POLL_INTERVAL)
   ```

4. **Na końcu (TEST):** Test z małymi batchami
   ```bash
   .venv/bin/python test_small_batches.py
   ```

**⚠️ KLUCZOWE:** 
Zmiana TYLKO timeout Elfina bez zmiany poll interval NIE ROZWIĄŻE problemu!
Zmiana TYLKO poll interval bez zmiany timeout Elfina sprawi, że polling będzie bardzo wolny!
**Musisz zmienić OBA!**

---

**Zobacz też:** [POLLING_INTERVALS.md](POLLING_INTERVALS.md) - szczegółowa matematyka i wyjaśnienia

Powodzenia! 🎉
