# Jak działa Batch Read w Modbus?

## Problem który naprawiłem

### Przed:
```python
result = client.read_holding_registers(address=0x0000, count=46)
# Czytało tylko do 0x002D!
```

**const.py miał:**
```python
0x002E: ("dc_pump_speed", ...)      # ❌ Nigdy nie czytany!
0x002F: ("suction_pressure", ...)   # ❌ Nigdy nie czytany!
0x0030: ("discharge_pressure", ...) # ❌ Nigdy nie czytany!
0x0031: ("dc_fan_target", ...)      # ❌ Nigdy nie czytany!
```

### Po naprawie:
```python
result = client.read_holding_registers(address=0x0000, count=50)
# Czyta cały zakres 0x0000-0x0031 ✓
```

---

## Matematyka Batch Read

### Jak Modbus zwraca dane?

```python
result = client.read_holding_registers(address=START, count=N)
# Zwraca: result.registers = [val0, val1, val2, ..., val(N-1)]
```

**Listę indeksowaną od 0!**

### Mapping: indeks listy → adres rejestru

```
result.registers[index] = wartość rejestru (START + index)
```

**Przykład dla count=50, start=0x0000:**

| Indeks | Adres hex | Adres dec | Parametr |
|--------|-----------|-----------|----------|
| 0 | 0x0000 | 0 | compressor_runtime |
| 1 | 0x0001 | 1 | cop |
| 14 | 0x000E | 14 | inlet_temp |
| 18 | 0x0012 | 18 | outlet_temp |
| 46 | 0x002E | 46 | dc_pump_speed |
| 47 | 0x002F | 47 | suction_pressure |
| 48 | 0x0030 | 48 | discharge_pressure |
| 49 | 0x0031 | 49 | dc_fan_target |

### Kod w __init__.py:

```python
# Czytamy 50 rejestrów od 0x0000
result = self.client.read_holding_registers(
    address=0x0000,
    count=50,  # ← FIXED! Było 46
    device_id=self.device_address
)

# Parsujemy każdy rejestr z const.REGISTERS_READ_ONLY
for address, (key, name, scale, unit, device_class) in REGISTERS_READ_ONLY.items():
    index = address - 0x0000  # Oblicz offset od początku batch
    if index < len(result.registers):  # Sprawdź czy w zakresie
        raw_value = result.registers[index]
        data[key] = raw_value * scale
```

### Przykład dla outlet_temp (0x0012):

```python
address = 0x0012
index = 0x0012 - 0x0000 = 18  # Hex: 0x12 = Dec: 18
raw_value = result.registers[18]
scale = 0.1  # ←  z const.py
data["outlet_temp"] = raw_value * 0.1  # np. 235 * 0.1 = 23.5°C
```

### Przykład dla dc_pump_speed (0x002E):

```python
address = 0x002E
index = 0x002E - 0x0000 = 46  # Hex: 0x2E = Dec: 46
raw_value = result.registers[46]  # ← Teraz działa! (count=50)
scale = 1
data["dc_pump_speed"] = raw_value * 1  # np. 1500 rpm
```

**PRZED naprawą (count=46):**
```python
index = 46
46 < 46? NIE! ❌
# Warunek if nie przechodzi, dc_pump_speed NIE zostaje dodany!
```

**PO naprawie (count=50):**
```python
index = 46
46 < 50? TAK! ✓
# Wartość zostaje dodana do data{}
```

---

## Porównanie: pojedyncze vs batch

### Bez batch (przestarzałe, WOLNE):
```python
# 50 osobnych requestów TCP:
temp1 = read(0x0000)  # ~100ms
temp2 = read(0x0001)  # ~100ms
# ...
temp50 = read(0x0031) # ~100ms
# TOTAL: 50 * 100ms = ~5000ms = 5 sekund!
```

### Z batch (SZYBKO):
```python
# 1 request TCP:
all_temps = read_holding_registers(0x0000, count=50)  # ~300ms
# TOTAL: ~300ms!
```

**Batch jest 16x SZYBSZY!** (5s → 0.3s)

---

## Dlaczego to ważne?

1. **Timeout calculation zależy od cycle time:**
   - Bez batch: cycle ~5s → potrzeba timeout 20-30s
   - Z batch: cycle ~3s → wystarczy timeout 15-30s

2. **Elfin W11 ma buffer limit:**
   - Max 1024 bytes
   - 50 requests * ~20 bytes = ~1000 bytes ✓ OK
   - 94 requests osobnych = przekroczenie bufferu! ❌

3. **Atomowość danych:**
   - Batch = wszystkie wartości z tego samego momentu
   - 50x read = wartości rozrzucone w czasie 5 sekund!

4. **Persistent connection:**
   - HA utrzymuje JEDNO połączenie TCP
   - Batch używa tego samego connection
   - Bez zamykania/otwierania co request

---

## Weryfikacja w logach

Po naprawie w logach HA powinieneś zobaczyć:

```
[sprsun_modbus] Read 50 read-only registers successfully
[sprsun_modbus] Working status register: 0x0003 = 0b00101011
```

Jeśli było tylko 46, rejestry 0x002E-0x0031 miały `None` lub `unavailable`.

