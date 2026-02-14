# Polling Intervals vs Elfin W11 Parameters

## ❌ PROBLEM z obecnymi ustawieniami:

```
Elfin Timeout: 120s
Poll Interval:   5s
```

**Co się dzieje:**
```
t=0s   → Request #1 wysłany
t=5s   → Request #2 wysłany (Request #1 może jeszcze "wisiał" w buforze!)
t=10s  → Request #3 wysłany (Request #1 i #2 mogą być w buforze!)
t=15s  → Request #4 wysłany
...
t=120s → Request #24 wysłany (Dopiero teraz Request #1 timeout!)
```

**Rezultat:** 
- W buforze 1024 bytes może być **do 24 requestów jednocześnie**!
- 24 requesty × ~108 bajtów = **2592 bajty** (buffer overflow!)
- Dlatego otrzymujesz 110/112 rejestrów zamiast 50

---

## 📐 MATEMATYKA:

### Obecne parametry (ZŁE):
```
Timeout:        120s  (za długi!)
Poll interval:    5s  (za krótki dla tego timeout!)
Max requests:  120/5 = 24 requesty "w locie"
Buffer need:  24×108 = 2592 bytes
Buffer size:         1024 bytes  ← OVERFLOW!
```

### Po zmianie timeout → 5s (DOBRE):
```
Timeout:         5s  (wystarczający dla Modbus)
Poll interval:   5s  (OK, ale ciasno)
Max requests:   5/5 = 1 request "w locie"
Buffer need:   1×108 = 108 bytes
Buffer size:        1024 bytes  ← OK! (9× zapas)
```

### Bezpieczny margines:
```
Timeout:         5s
Poll interval:  10s  (2× timeout = bezpieczny)
Max requests:   5/10 = 0.5 (zaokrąglij do 1)
Buffer need:   1×108 = 108 bytes
Buffer size:        1024 bytes  ← Bardzo bezpieczne!
```

---

## ✅ REKOMENDACJE:

### Scenariusz 1: **NIE ZMIENISZ** parametrów Elfina (Timeout = 120s)

**Musisz zwiększyć polling interval:**

```python
POLL_INTERVAL = 120  # sekund (tak, 2 minuty!)
```

**Dlaczego:**
- Timeout 120s = request może wisieć 2 minuty
- Jeśli pollujesz częściej, requesty się nakładają
- Buffer overflow gwarantowany

**Wady:**
- Bardzo wolny odczyt (1 pomiar co 2 minuty)
- Nie nadaje się do Home Assistant
- Ale będzie stabilny!

---

### Scenariusz 2: **ZMIENISZ** Timeout → 5s (ZALECANE)

**Możesz użyć krótszych interwałów:**

```python
# Bezpieczny (rekomendowany):
POLL_INTERVAL = 10  # sekund (2× timeout)

# Agresywny (ryzykowny):
POLL_INTERVAL = 5   # sekund (1× timeout, ciasno)

# Bardzo agresywny (nie rób tego):
POLL_INTERVAL = 3   # sekund (< timeout, overflow!)
```

**Reguła:**
```
Poll Interval ≥ Timeout  (minimum)
Poll Interval ≥ 2 × Timeout  (bezpieczne)
```

---

### Scenariusz 3: **ZMIENISZ** Timeout → 5s + **małe batche**

Jeśli czytasz w małych paczkach (5× batch po 10):

```python
POLL_INTERVAL = 10  # sekund między pełnymi cyklami
BATCH_DELAY = 0.2   # sekund między batchami w cyklu
```

**Przykład:**
```
t=0.0s  → Batch 1: rejestry 0-9   (0.2s na odpowiedź)
t=0.2s  → Batch 2: rejestry 10-19
t=0.4s  → Batch 3: rejestry 20-29
t=0.6s  → Batch 4: rejestry 30-39
t=0.8s  → Batch 5: rejestry 40-49
t=1.0s  → Pełny cykl zakończony
t=10.0s → Następny cykl
```

**Zalety:**
- Szybki cykl (~1s zamiast 5s)
- Bezpieczny interwał (10s)
- Małe batche = mniej ryzyka

---

## 🧮 KALKULATOR:

### Ile czasu trwa pojedynczy request?

**Batch 50 rejestrów:**
```
Czas = (Network RTT) + (UART transmission) + (Device processing)
     ≈ 50ms + 100ms + 50ms
     ≈ 200ms (0.2 sekundy)
```

**Rzeczywisty czas** (z testów):
```
Individual read (1 reg):  ~100ms
Individual read (50 reg): ~5 sekund (50 × 100ms)
Batch read (50 reg):      ~200-500ms (JEŚLI działa)
```

### Jaki poll interval dla różnych timeout?

| Elfin Timeout | Min. Poll Interval | Bezpieczny Interval | Home Assistant OK? |
|---------------|-------------------|--------------------|--------------------|
| 120s          | 120s (2 min)      | 240s (4 min)       | ❌ Zbyt wolny      |
| 60s           | 60s (1 min)       | 120s (2 min)       | ⚠️ Za wolny         |
| 30s           | 30s               | 60s (1 min)        | ⚠️ Akceptowalne     |
| 10s           | 10s               | 20s                | ✅ OK              |
| 5s            | 5s                | 10s                | ✅ Bardzo dobre    |
| 3s            | 3s                | 6s                 | ✅ Idealne         |

---

## 🎯 OPTYMALNA KONFIGURACJA:

### Dla Home Assistant (potrzebujesz updates co 10-30s):

**Elfin W11:**
```
Timeout:    5s   ← ZMIEŃ z 120s
Buffer:   512    ← ZMIEŃ z 1024 (opcjonalne)
Keep alive: 65s  ← Zostaw
Max accept:  1   ← ZMIEŃ z 3 (zapobiega race conditions)
```

**Python skrypt:**
```python
POLL_INTERVAL = 10      # sekund (2× timeout = bezpieczne)
BATCH_SIZE = 10         # małe batche zamiast 50
BATCH_DELAY = 0.1       # sekund między batchami
TIMEOUT = 3             # sekund client timeout (< server timeout)
```

---

### Dla rzadkich pomiarów (co 5 minut OK):

**Elfin W11:**
```
Timeout:  60s   ← Możesz zostawić dłuższy
Buffer:  1024   ← Zostaw
Keep alive: 65s ← Zostaw
Max accept:  1  ← ZMIEŃ z 3
```

**Python skrypt:**
```python
POLL_INTERVAL = 300  # 5 minut
# Możesz użyć batch 50 (jeden request)
```

---

## ⚠️ DIAGNOZA OBECNEGO PROBLEMU:

### Twoje obecne ustawienia:
```python
# W modbus_poller.py:
time.sleep(5)  # 5 sekund między pollami

# Elfin:
Timeout: 120s   ← 24× dłuższy niż poll interval!
```

**To jest źródło problemu:**
1. Co 5s wysyłasz nowy request
2. Stary request może wisieć 120s
3. W tym czasie wyślesz 24 nowe requesty
4. Bufor 1024 nie pomieści wszystkich
5. Dane się mieszają → 110/112 rejestrów

---

## 🔧 SZYBKA NAPRAWA:

### Opcja A: Zmień tylko skrypt (TYMCZASOWE)
```python
POLL_INTERVAL = 120  # Dopasuj do Elfin timeout
```

**Test:**
```bash
# W modbus_poller.py lub modbus_batch_poller.py
# Zmień: time.sleep(5) → time.sleep(120)
```

### Opcja B: Zmień Elfin (ZALECANE)
1. Zaloguj: http://192.168.1.234
2. Timeout: 120s → 5s
3. Restart Elfin
4. Zmień skrypt: `time.sleep(5)` → `time.sleep(10)` (bezpieczny margines)

### Opcja C: Test z realnym czasem (DIAGNOZA)
```python
import time
start = time.time()
result = client.read_holding_registers(0x0000, count=50, device_id=1)
elapsed = time.time() - start
print(f"Request trwał: {elapsed:.2f}s")

# Jeśli elapsed < 1s → możesz pollować co 2-3s
# Jeśli elapsed > 5s → coś jest nie tak z Elfin/siecią
```

---

## 📊 TABELKA DECYZYJNA:

| Chcesz pollować co: | Elfin Timeout musi być: | Bezpieczeństwo |
|---------------------|-------------------------|----------------|
| 5s                  | ≤ 5s                    | Ryzykowne      |
| 10s                 | ≤ 5s                    | Bezpieczne     |
| 30s                 | ≤ 15s                   | Bardzo bezpieczne |
| 60s                 | ≤ 30s                   | Overkill       |
| 300s (5 min)        | Dowolny                 | Nie ma problemu |

---

## ✅ ACTION PLAN:

1. **Najpierw:** Zmierz rzeczywisty czas requestu
   ```bash
   .venv/bin/python -c "
   from pymodbus.client import ModbusTcpClient
   import time
   client = ModbusTcpClient('192.168.1.234', port=502, timeout=3)
   client.connect()
   start = time.time()
   result = client.read_holding_registers(0x0000, count=50, device_id=1)
   print(f'Request: {time.time()-start:.2f}s, Rejestrów: {len(result.registers)}')
   client.close()
   "
   ```

2. **Potem:** Dostosuj poll interval
   ```
   Jeśli request < 1s  → poll co 3-5s OK (po zmianie Elfin timeout)
   Jeśli request > 5s  → problem z Elfin/UART
   ```

3. **Na końcu:** Zmień Elfin parametry jak w ELFIN_W11_RECOMMENDED_SETTINGS.md

---

## 🎓 PODSUMOWANIE:

**Złota zasada:**
```
Poll Interval ≥ 2 × Elfin Timeout
```

**Twój przypadek:**
- Obecny Elfin Timeout: 120s → **Minimum poll co 240s**
- Chcesz pollować co 10s? → **Zmień Elfin Timeout na ≤5s**

**Dlatego batch reads są niestabilne** - nie timeout jest problemem, ale **nakładanie się requestów** przez zbyt krótki poll interval! 🎯
