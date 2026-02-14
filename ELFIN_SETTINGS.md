# Elfin W11 Gateway - Zalecane Ustawienia

## Dla Debug Script (modbus_debug_poller.py)

**Wymagane ustawienia Elfin W11:**

```
Protocol: Modbus TCP
IP: 192.168.1.234
Port: 502
Timeout: 10s          ← ZWIĘKSZ z 5s!
Keep alive: 65s
Max accept: 2
```

**Dlaczego timeout 10s?**
- Cycle time: ~2s (czytanie wszystkich parametrów)
- Poll interval: 5s (przerwa między cyklami)
- Total: 2s + 5s = 7s
- **Bezpieczeństwo**: Timeout = 10s > 7s ✓

## Dla Home Assistant Integration

**Zalecane ustawienia Elfin W11:**

```
Protocol: Modbus TCP
IP: 192.168.1.234
Port: 502
Timeout: 30s          ← Długi dla batch reads
Keep alive: 65s
Max accept: 2
```

**Dlaczego timeout 30s?**
- Cycle time: ~3s (czytanie 50 rejestrów w batch)
- Default scan_interval: 10s (konfigurowalne 5-300s)
- Total: 10s + 3s + margin = ~15s
- **Bezpieczeństwo**: Timeout = 30s > 15s ✓ (2x margin)

## Formuła

```
Elfin Timeout >= (Max Scan Interval + Max Cycle Time + Margin)

Gdzie:
- Max Scan Interval = najdłuższy interwał czytania
- Max Cycle Time = czas wszystkich batch reads
- Margin = 2-3s bezpieczeństwa
```

## Przykłady

| Use Case | Scan Interval | Cycle Time | Elfin Timeout |
|----------|---------------|------------|---------------|
| Debug Script (26 params) | 5s | ~2s | **10s** |
| HA Normal (50 regs batch) | 10s | ~3s | **30s** |
| HA Conservative | 30s | ~3s | **40s** |
| HA Aggressive | 5s | ~3s | **10s** |

## Jak działa batch read?

**Modbus batch read** czyta wiele rejestrów w jednej transakcji TCP:

```python
result = read_holding_registers(address=0x0000, count=50)
# Zwraca listę: registers[0], registers[1], ..., registers[49]
```

**Mapping indeks → adres:**
```
registers[index] = adres (start_address + index)

Przykłady:
registers[0]  = adres 0x0000 (compressor_runtime)
registers[18] = adres 0x0012 (outlet_temp) bo 0x0012 - 0x0000 = 18  
registers[46] = adres 0x002E (dc_pump_speed)
registers[49] = adres 0x0031 (dc_fan_target)
```

**Zalety batch read:**
- ✓ 1 transakcja TCP zamiast 50 osobnych
- ✓ ~3s cycle time zamiast ~50s (50 x 1s per request)
- ✓ Mniej obciążenia dla Elfin W11
- ✓ Atomowe odczytanie (wszystkie wartości z tego samego momentu)

## Jak zmienić Elfin timeout?

1. Połącz się z Elfin web interface: http://192.168.1.234
2. Login: admin / admin (lub twoje hasło)
3. Serial Port -> Timeout: **10s** lub **30s**
4. Apply & Restart
5. Test połączenia
