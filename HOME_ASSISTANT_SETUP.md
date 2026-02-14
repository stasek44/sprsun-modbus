# Home Assistant + Python Poller - Współpraca z Elfin W11

## 🎯 Architektura: 2 Klienty Modbus

```
┌─────────────────┐      ┌─────────────────┐
│  Python Script  │      │ Home Assistant  │
│  (READ tylko)   │      │  (READ + WRITE) │
└────────┬────────┘      └────────┬────────┘
         │                        │
         │    Modbus TCP/502      │
         └────────┬───────────────┘
                  │
          ┌───────▼────────┐
          │  Elfin W11     │
          │  Gateway       │
          │  Max Accept: 2 │  ← Pozwól na 2 klientów!
          └───────┬────────┘
                  │ RS485/UART
          ┌───────▼────────┐
          │ SPRSUN Pompa   │
          │  Ciepła        │
          └────────────────┘
```

## ⚠️ KLUCZOWE PROBLEMY DO ROZWIĄZANIA:

### Problem 1: Konflikty przy zapisie (WRITE)

**Scenariusz:**
1. Home Assistant zmienia setpoint heating: 22°C → 25°C (WRITE 0x00CC)
2. W tym samym czasie Python czyta heating_setpoint (READ 0x00CC)
3. **Konflikt:** Który request przejdzie pierwszy?

**Rozwiązanie:**
- Python: **Tylko READ**, nigdy WRITE
- Home Assistant: READ + WRITE (ma wyłączność na zmiany)
- Elfin timeout: 5s (wystarczająco krótki)
- Poll interval: 10s (bez nakładania się)

### Problem 2: Przepustowość bufora

**Matematyka:**
```
Python poll:        co 10s
HA poll:            co 10s (różne rejestry)
HA write (rzadko):  <5 razy/minutę

Max requesty/minutę:
- Python: 6 requestów (batch ~5 requestów każdy) = 30 req/min
- HA read: 6 requestów = 6 req/min  
- HA write: 5 requestów = 5 req/min
TOTAL: ~41 requestów/minutę

Buffer Elfin (1024 bytes):
- Jeden request+response: ~108 bajtów
- Jednocześnie max: 1 request (timeout 5s, poll 10s)
- Buffer OK: 108 bajty < 1024 limit ✓
```

### Problem 3: Race Conditions

**Co się stanie jeśli oba klienty czytają jednocześnie?**

Elfin W11 ma **Max Accept = 2** (domyślnie 3):
- Dwa połączenia TCP mogą być ESTABLISHED jednocześnie
- Gateway obsługuje requesty sekwencyjnie (FIFO)
- Jeden request blokuje UART dopóki nie dostanie odpowiedzi

**Test:**
```bash
# Terminal 1:
.venv/bin/python modbus_full_poller.py

# Terminal 2 (symulacja HA):
.venv/bin/python -c "
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('192.168.1.234', port=502, timeout=3)
client.connect()
for i in range(10):
    result = client.read_holding_registers(0x00CC, count=1, device_id=1)  # Heating setpoint
    print(f'{i+1}. {result.registers[0] * 0.5}°C')
    import time; time.sleep(5)
client.close()
"
```

**Oczekiwany rezultat:**
- Oba działają bez błędów
- Requesty obsługiwane sekwencyjnie przez Elfin
- Możliwe krótkie opóźnienia (~200ms) gdy jeden czeka na drugiego

---

## ✅ OPTYMALNA KONFIGURACJA:

### Elfin W11 Settings:
```
Timeout:    5s   ← Zmienione z 120s
Buffer:     1024 ← Zostaw (wystarczy)
Keep alive: 65s  ← Zostaw
Max accept: 2    ← WAŻNE: Pozwól na 2 klientów (Python + HA)
```

**Uwaga:** Jeśli Max Accept = 1, to tylko jeden klient może się łączyć!

### Python Script (modbus_full_poller.py):
```python
POLL_INTERVAL = 10  # sekund (działa świetnie)
CLIENT_TIMEOUT = 3  # sekundy

# TYLKO READ - nigdy WRITE!
```

### Home Assistant Configuration:
```yaml
# configuration.yaml
modbus:
  - name: sprsun
    type: tcp
    host: 192.168.1.234
    port: 502
    timeout: 3
    
    # SENSORS (READ tylko)
    sensors:
      - name: "Heat Pump Inlet Temp"
        address: 0x000E
        slave: 1
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "°C"
        scan_interval: 10  # Dopasowane do Python script
        
      - name: "Heat Pump Hotwater Temp"
        address: 0x000F
        slave: 1
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "°C"
        scan_interval: 10
        
      - name: "Heat Pump Heating Setpoint"
        address: 0x00CC
        slave: 1
        data_type: int16
        scale: 0.5
        precision: 1
        unit_of_measurement: "°C"
        scan_interval: 10
    
    # CLIMATE (READ + WRITE)
    climates:
      - name: "Heat Pump Heating"
        address: 0x00CC  # Heating setpoint (RW)
        slave: 1
        data_type: int16
        scale: 0.5
        offset: 0
        precision: 1
        max_temp: 55
        min_temp: 10
        temp_step: 0.5
        target_temp_register: 0x00CC
        
    # NUMBERS (WRITE setpoints)
    numbers:
      - name: "Heat Pump Cooling Setpoint"
        address: 0x00CB
        slave: 1
        data_type: int16
        scale: 0.5
        min_value: 12
        max_value: 30
        step: 0.5
        
      - name: "Heat Pump Hotwater Setpoint"
        address: 0x00CA
        slave: 1
        data_type: int16
        scale: 0.5
        min_value: 10
        max_value: 55
        step: 0.5
    
    # SWITCHES (WRITE control bits)
    switches:
      - name: "Heat Pump Power"
        address: 0x0032
        slave: 1
        command_on: 1
        command_off: 0
        write_type: holding
        verify:  # Opcjonalnie: sprawdź po zapisie
          address: 0x0032
          delay: 1
```

---

## 🔄 SYNCHRONIZACJA MIĘDZY KLIENTAMI:

### Strategia 1: Staggered Polling (Przesunięte)

**Aby uniknąć kolizji, przesuń czasy pollingu:**

```python
# Python script:
POLL_INTERVAL = 10  # Start at :00, :10, :20, :30...
```

```yaml
# Home Assistant:
scan_interval: 10  # Start at :05, :15, :25, :35...
# (HA automatycznie rozkłada na minutę)
```

**Rezultat:**
```
t=00s: Python poll
t=05s: HA poll
t=10s: Python poll
t=15s: HA poll
t=20s: Python poll
```

Konflikty: **ZERO** (idealna synchronizacja)

---

### Strategia 2: Python Jako Backup (Preferred)

**Jeśli Home Assistant już działa:**

1. **HA robi wszystko** (READ + WRITE) co 10s
2. **Python backup** tylko do long-term CSV storage
   - Poll co 60s (rejestruje historię)
   - Nie przeszkadza HA

```python
# modbus_full_poller.py:
POLL_INTERVAL = 60  # 1 minuta - backup only
```

**Zalety:**
- HA ma wyłączność na real-time monitoring
- Python zapisuje długoterminowe dane do CSV
- Konflikty prawie niemożliwe

---

## 📊 TESTOWANIE WSPÓŁPRACY:

### Test 1: Równoczesne odczyty
```bash
# Terminal 1:
.venv/bin/python modbus_full_poller.py

# Terminal 2:
watch -n 10 '.venv/bin/python -c "
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient(\"192.168.1.234\", port=502, timeout=3)
client.connect()
result = client.read_holding_registers(0x00CC, count=1, device_id=1)
print(f\"HA read: {result.registers[0] * 0.5}°C\")
client.close()
"'
```

**Sprawdź:**
- Czy oba działają bez błędów?
- Czy czasy odpowiedzi to ~200-500ms?
- Czy żaden nie dostaje timeout?

---

### Test 2: Zapis podczas odczytu (symulacja HA WRITE)
```bash
# Terminal 1: Python czyta
.venv/bin/python modbus_full_poller.py

# Terminal 2: Symuluj HA write
.venv/bin/python -c "
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('192.168.1.234', port=502, timeout=3)
client.connect()

# Zmień heating setpoint na 24°C (= 48 w raw)
result = client.write_register(0x00CC, 48, device_id=1)
print(f'Write result: {result}')

# Sprawdź czy zapisało
import time
time.sleep(1)
result = client.read_holding_registers(0x00CC, count=1, device_id=1)
print(f'New setpoint: {result.registers[0] * 0.5}°C')

client.close()
"
```

**Sprawdź:**
- Czy Python kontynuował polling?
- Czy WRITE się powiódł?
- Czy następny READ Python pokazał nową wartość?

---

## ⚠️ PROBLEMY I ROZWIĄZANIA:

### Problem: "Connection refused" dla drugiego klienta

**Przyczyna:** Elfin Max Accept = 1

**Rozwiązanie:**
1. Zaloguj: http://192.168.1.234
2. Znajdź "Max Accept" lub "Max Connections"
3. Zmień na **2** (lub 3 jeśli planujesz więcej)
4. Restart Elfin

---

### Problem: HA write nie działa, Python działa

**Przyczyna:** Python i HA próbują pisać jednocześnie

**Rozwiązanie:**
- Python: **NIGDY nie rób WRITE**
- Tylko HA ma prawo do WRITE
- Python jest read-only observer

---

### Problem: Oba klienty dostają timeout

**Przyczyna:** Poll interval za krótki lub Elfin timeout za długi

**Rozwiązanie:**
```python
# Zwiększ poll interval:
POLL_INTERVAL = 15  # był 10

# Lub w HA:
scan_interval: 15
```

---

### Problem: Dane się nie zgadzają między Python a HA

**Przyczyna:** Cache w HA lub delay

**Rozwiązanie:**
```yaml
# W HA dodaj:
scan_interval: 5  # Częstsze odczyty
lazy_error_count: 1  # Nie cache errors
```

---

## 🎯 REKOMENDOWANA KONFIGURACJA FINALNA:

### Scenariusz: HA Primary, Python Backup

```yaml
# Elfin W11:
Timeout: 5s
Max Accept: 2
Buffer: 1024

# Home Assistant:
scan_interval: 10s  (sensors)
write: on demand (user changes setpoint)

# Python Script:
POLL_INTERVAL: 60s  (tylko backup/logging)
```

**Dlaczego:**
- HA ma real-time access (10s)
- Python nie przeszkadza (60s)
- Konflikty praktycznie niemożliwe
- Buffer nigdy nie overflows

---

## 📝 CHECKLIST WDROŻENIA:

- [ ] Zmień Elfin Timeout: 120s → 5s
- [ ] Zmień Elfin Max Accept: 1 → 2 (lub zostaw 3)
- [ ] Test Python alone: `python modbus_full_poller.py`
- [ ] Sprawdź stabilność: 100% success rate
- [ ] Skonfiguruj HA Modbus integration
- [ ] Test HA alone: sprawdź czy sensors działają
- [ ] Test obu razem: Python + HA jednocześnie
- [ ] Test HA WRITE: zmień setpoint przez UI
- [ ] Sprawdź czy Python widzi zmienioną wartość
- [ ] Monitor przez 1 godzinę: sprawdź logi
- [ ] Jeśli OK: Deploy production

---

## 🚀 QUICK START:

### Krok 1: Test Python (solo)
```bash
.venv/bin/python modbus_full_poller.py
# Powinno być 100% stabilne, ~2s per poll
```

### Krok 2: Dodaj HA config
```yaml
# configuration.yaml - dodaj podstawowe sensory
modbus:
  - name: sprsun
    type: tcp
    host: 192.168.1.234
    port: 502
    sensors:
      - name: "HP Inlet Temp"
        address: 0x000E
        slave: 1
        data_type: int16
        scale: 0.1
        scan_interval: 10
```

### Krok 3: Restart HA
```bash
# Developer Tools → YAML → Reload Modbus
```

### Krok 4: Test obu razem
```bash
# Terminal 1:
.venv/bin/python modbus_full_poller.py

# Terminal 2: Sprawdź HA sensor
# Home Assistant → Developer Tools → States
# Szukaj: sensor.hp_inlet_temp
```

### Krok 5: Monitor
```bash
# Obserwuj logi przez 15 minut
# Sprawdź czy są błędy timeoutów
# Sprawdź czy wartości są spójne
```

---

## 🎉 PODSUMOWANIE:

**Konfiguracja która działa:**
- Elfin Timeout: 5s ✓
- Max Accept: 2 ✓
- Python Poll: 10s (lub 60s jako backup) ✓
- HA Scan: 10s ✓
- Python: READ tylko ✓
- HA: READ + WRITE ✓

**Expected Performance:**
- Python: 100% success rate
- HA: Wszystkie sensory działają
- WRITE: Setpointy zmieniają się natychmiast
- No timeouts, no conflicts!

Gotowe do wdrożenia! 🚀
