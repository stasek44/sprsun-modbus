# SPRSUN Heat Pump - Home Assistant Custom Integration

## 📦 Instalacja

### Metoda 1: HACS (zalecane)

1. Otwórz HACS w Home Assistant
2. Kliknij "Integrations" 
3. Kliknij "+" w prawym dolnym rogu
4. Wyszukaj "SPRSUN Heat Pump"
5. Kliknij "Install"
6. Restart Home Assistant

### Metoda 2: Ręczna instalacja

1. Skopiuj folder `custom_components/sprsun_modbus` do katalogu `config/custom_components/` w Home Assistant
2. Restart Home Assistant  
3. Idź do Settings → Devices & Services
4. Kliknij "+ ADD INTEGRATION"
5. Wyszukaj "SPRSUN Heat Pump"

## ⚙️ Konfiguracja

### Wymagania

- **Elfin W11 Gateway** skonfigurowana jako Modbus TCP
- **Pompa ciepła SPRSUN** podłączona do Elfin przez RS485

### Ustawienia Elfin W11

**WAŻNE**: Przed konfiguracją integracji ustaw odpowiedni **timeout w Elfin W11**:

```
Protocol: Modbus TCP
IP: 192.168.1.234 (twój adres)
Port: 502
Timeout: 30s          ← WAŻNE! Min 30s dla scan_interval=10s
Keep alive: 65s
Max accept: 2
```

**Formuła**: `Elfin Timeout >= Scan Interval + 10s margin`

### Konfiguracja w Home Assistant

1. **Settings → Devices & Services → "+ ADD INTEGRATION"**
2. Wyszukaj **"SPRSUN Heat Pump"**
3. Wypełnij dane:
   - **Name**: "SPRSUN Heat Pump" (dowolna nazwa)
   - **Host**: 192.168.1.234 (IP Elfin W11)
   - **Port**: 502 (domyślny Modbus TCP)
   - **Device Address**: 1 (adres Modbus pompy)
   - **Scan Interval**: 10s (zalecane: 10-30s)

4. Kliknij **"Submit"**
5. Integracja wykryje pompę i utworzy wszystkie encje

## 📊 Encje

Integracja tworzy **92 encje**:

### Sensors (50) - Read-Only

**System Status (6):**
- `sensor.sprsun_compressor_runtime` - Czas pracy sprężarki
- `sensor.sprsun_cop` - Współczynnik COP
- `sensor.sprsun_software_version_year` - Wersja oprogramowania (rok)
- `sensor.sprsun_software_version_month_day` - Wersja oprogramowania (miesiąc/dzień)
- `sensor.sprsun_controller_version` - Wersja kontrolera
- `sensor.sprsun_display_version` - Wersja wyświetlacza

**Status Flags (11):**
- `sensor.sprsun_switching_input_symbol` - Status wejść
- `sensor.sprsun_working_status_mark` - Status pracy
- `sensor.sprsun_output_symbol_1` - Status wyjść 1
- `sensor.sprsun_output_symbol_2` - Status wyjść 2
- `sensor.sprsun_output_symbol_3` - Status wyjść 3
- `sensor.sprsun_failure_symbol_1` - `sensor.sprsun_failure_symbol_7` - Symbole usterek

**Temperatury (10):**
- `sensor.sprsun_inlet_temp` - Temperatura wejściowa wody
- `sensor.sprsun_hotwater_temp` - Temperatura ciepłej wody użytkowej
- `sensor.sprsun_ambient_temp` - Temperatura otoczenia
- `sensor.sprsun_outlet_temp` - Temperatura wyjściowa wody
- `sensor.sprsun_suction_gas_temp` - Temperatura ssania
- `sensor.sprsun_coil_temp` - Temperatura cewki
- `sensor.sprsun_exhaust_temp` - Temperatura wydechu
- `sensor.sprsun_driving_temp` - Temperatura modułu mocy
- `sensor.sprsun_evap_temp` - Temperatura parowania
- `sensor.sprsun_cond_temp` - Temperatura kondensacji

**Pomiary systemowe (18):**
- `sensor.sprsun_ac_voltage` - Napięcie AC
- `sensor.sprsun_pump_flow` - Przepływ pompy
- `sensor.sprsun_heating_cooling_capacity` - Moc grzewcza/chłodnicza
- `sensor.sprsun_ac_current` - Prąd AC
- `sensor.sprsun_eev1_step` - Otwarcie zaworu EEV1
- `sensor.sprsun_eev2_step` - Otwarcie zaworu EEV2
- `sensor.sprsun_compressor_frequency` - Częstotliwość sprężarki
- `sensor.sprsun_dc_bus_voltage` - Napięcie magistrali DC
- `sensor.sprsun_compressor_current` - Prąd sprężarki
- `sensor.sprsun_target_frequency` - Częstotliwość docelowa
- `sensor.sprsun_dc_fan1_speed` - Prędkość wentylatora 1
- `sensor.sprsun_dc_fan2_speed` - Prędkość wentylatora 2
- `sensor.sprsun_dc_pump_speed` - Prędkość pompy DC
- `sensor.sprsun_suction_pressure` - Ciśnienie ssania
- `sensor.sprsun_discharge_pressure` - Ciśnienie tłoczenia
- `sensor.sprsun_dc_fan_target` - Prędkość docelowa wentylatorów
- `sensor.sprsun_smart_grid_status` - Status smart grid
- `sensor.sprsun_freq_conversion_fault_high/low` - Usterki falownika

### Binary Sensors (6) - Read-Only Status

- `binary_sensor.sprsun_hotwater_demand` - Zapotrzebowanie na CWU
- `binary_sensor.sprsun_heating_demand` - Zapotrzebowanie na ogrzewanie
- `binary_sensor.sprsun_cooling_demand` - Zapotrzebowanie na chłodzenie
- `binary_sensor.sprsun_antilegionella_active` - Aktywna antylegionella
- `binary_sensor.sprsun_defrost_active` - Aktywne odszranianie
- `binary_sensor.sprsun_alarm_stop` - Stop awaryjny

### Numbers (42) - Read-Write

**Podstawowa konfiguracja:**
- `number.sprsun_unit_mode` - Tryb pracy (0=CWU, 1=Ogrzew, 2=Chłodz, 3=Ogrzew+CWU, 4=Chłodz+CWU)
- `number.sprsun_heating_setpoint` - Temperatura zadana ogrzewania (10-55°C) ⭐
- `number.sprsun_cooling_setpoint` - Temperatura zadana chłodzenia (12-30°C) ⭐
- `number.sprsun_hotwater_setpoint` - Temperatura zadana CWU (10-55°C) ⭐
- `number.sprsun_temp_diff_heating_cooling` - Histereza ogrzewania/chłodzenia (2-18°C)
- `number.sprsun_temp_diff_hotwater` - Histereza CWU (2-18°C)
- `number.sprsun_fan_mode` - Tryb wentylatora (0=NOR, 1=ECO, 2=Night, 3=Test)

**Tryb ekonomiczny - Ogrzewanie (8):**
- `number.sprsun_econ_heat_ambi_1` - `number.sprsun_econ_heat_ambi_4` - Temperatura otoczenia
- `number.sprsun_econ_heat_temp_1` - `number.sprsun_econ_heat_temp_4` - Temperatura wody

**Tryb ekonomiczny - CWU (8):**
- `number.sprsun_econ_water_ambi_1` - `number.sprsun_econ_water_ambi_4` - Temperatura otoczenia
- `number.sprsun_econ_water_temp_1` - `number.sprsun_econ_water_temp_4` - Temperatura wody

**Tryb ekonomiczny - Chłodzenie (8):**
- `number.sprsun_econ_cool_ambi_1` - `number.sprsun_econ_cool_ambi_4` - Temperatura otoczenia
- `number.sprsun_econ_cool_temp_1` - `number.sprsun_econ_cool_temp_4` - Temperatura wody

**Konfiguracja ogólna (11):**
- `number.sprsun_comp_delay_hotwater` - Opóźnienie grzałki CWU (1-60 min)
- `number.sprsun_comp_delay_heating` - Opóźnienie grzałki ogrzewania (1-60 min)
- `number.sprsun_hotwater_heater_ext_temp` - Temp. startu grzałki CWU (-30-30°C)
- `number.sprsun_heating_heater_ext_temp` - Temp. startu grzałki ogrzew. (-30-30°C)
- `number.sprsun_pump_cycle` - Cykl termostatu pompy (1-120 min)
- `number.sprsun_dc_pump_temp_diff` - Różnica temp. pompy DC (5-30°C)
- `number.sprsun_mode_control_enable` - Włączenie kontroli trybu
- `number.sprsun_ambient_switch_setpoint` - Punkt przełączania wg temp. (-20-30°C)
- `number.sprsun_ambient_switch_diff` - Histereza przełączania (1-10°C)
- `number.sprsun_pump_work_mode` - Tryb pracy pompy (0=Interval, 1=Normal, 2=Demand)

**Antylegionella (4):**
- `number.sprsun_antilegionella_temp` - Temperatura antylegionella (30-70°C)
- `number.sprsun_antilegionella_weekday` - Dzień tygodnia (0=Nie, 6=Sob)
- `number.sprsun_antilegionella_start_hour` - Godzina startu (0-23)
- `number.sprsun_antilegionella_end_hour` - Godzina końca (0-23)

## 🎛️ Przykładowa karta Dashboard

```yaml
type: vertical-stack
cards:
  # Status główny
  - type: glance
    title: SPRSUN Heat Pump
    entities:
      - entity: sensor.sprsun_inlet_temp
        name: Inlet
      - entity: sensor.sprsun_hotwater_temp
        name: Hot Water
      - entity: sensor.sprsun_ambient_temp
        name: Ambient
      - entity: sensor.sprsun_frequency
        name: Freq
      - entity: sensor.sprsun_cop
        name: COP
  
  # Kontrola trybu
  - type: entities
    title: Kontrola
    entities:
      - entity: number.sprsun_unit_mode
      - entity: switch.sprsun_heating_control
      - entity: switch.sprsun_cooling_control
      - entity: switch.sprsun_hotwater_control
  
  # Temperatury zadane
  - type: entities
    title: Temperatury Zadane
    entities:
      - entity: number.sprsun_heating_setpoint
      - entity: number.sprsun_cooling_setpoint
      - entity: number.sprsun_hotwater_setpoint
  
  # Wydajność
  - type: entities
    title: Wydajność
    entities:
      - entity: sensor.sprsun_input_power
      - entity: sensor.sprsun_output_power
      - entity: sensor.sprsun_cop
      - entity: sensor.sprsun_low_pressure
      - entity: sensor.sprsun_high_pressure
```

## 🔧 Zmiana parametrów

### Zmiana scan_interval

Możesz zmienić interwał skanowania BEZ restartu HA:

1. Settings → Devices & Services
2. Znajdź "SPRSUN Heat Pump"
3. Kliknij "CONFIGURE" (ikonka koła zębatego)
4. Zmień "Scan Interval"
5. **Integracja automatycznie się przeładuje!**

**Pamiętaj**: `Elfin Timeout >= Scan Interval + 20s`

### Dostosowanie Elfin Timeout

| Scan Interval | Min Elfin Timeout |
|---------------|-------------------|
| 5s | 15s |
| 10s | 20s |
| 30s | 40s |

## 🐛 Debug

Włącz logi debug w `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.sprsun_modbus: debug
    pymodbus: debug
```

Logi dostępne w: Settings → System → Logs

## 📚 Dokumentacja techniczna

- [ELFIN_SETTINGS.md](ELFIN_SETTINGS.md) - Szczegóły konfiguracji Elfin W11
- [modbus_reference.md](modbus_reference.md) - Mapa rejestrów Modbus
- [homeassistant_full_config.yaml](homeassistant_full_config.yaml) - Alternatywna konfiguracja YAML

## ⚠️ Rozwiązywanie problemów

### "Cannot connect" podczas konfiguracji

1. Sprawdź IP i port Elfin W11
2. Sprawdź czy pompa odpowiada: `telnet 192.168.1.234 502`
3. Sprawdź adres Modbus urządzenia (domyślnie 1)
4. Sprawdź czy Elfin W11 jest w trybie Modbus TCP (nie RTU!)

### Encje pokazują "Unavailable"

1. Sprawdź logi: Settings → System → Logs → filtruj "sprsun"
2. Sprawdź Elfin timeout (min 30s dla scan_interval=10s)
3. Sprawdź czy pompa jest w trybie ON
4. Reload integracji: Settings → Devices & Services → SPRSUN → ⋮ → Reload

### Wolne odpowiedzi / timeout

1. Zwiększ Elfin W11 timeout (30s → 60s)
2. Zwiększ scan_interval w opcjach integracji (10s → 30s)
3. Sprawdź połączenie RS485 z pompą (terminacja, polaryzacja)

### Połączenie JEST podtrzymywane

Integracja używa **persistent connection** - jednego połączenia TCP dla wszystkich operacji.
Elfin W11 "Keep alive: 65s" powinien być OK.

## � Uwagi techniczne

1. **Persistent connection**: Integracja używa jednego połączenia TCP, które jest utrzymywane przez cały czas
2. **Batch reads**: 50 R rejestrów czytanych w jednym batch (0x0000-0x0031)
3. **Async operations**: Wszystkie operacje są asynchroniczne - nie blokują HA
4. **device_id parametr**: Używa nowoczesnego `device_id=` zamiast przestarzałego `slave=`
5. **Reload on config change**: Zmiana scan_interval automatycznie przeładowuje integrację

## ⚠️ Ograniczenia

1. **Switche (0x0032-0x0034)**: Nie zaimplementowane - wymaga bitowej manipulacji
2. **Write restrictions**: Tylko urządzenie #1 może być modyfikowane
3. **Economic mode**: 24 parametry - używaj ostrożnie!

## 🔜 Przyszłe funkcjonalności

- [ ] Switche dla control marks (0x0032-0x0034 bitfields)
- [ ] Climate entity dla lepszej integracji z HA
- [ ] Diagnostyka połączenia
- [ ] Template binary_sensors dla złożonych warunków

## 📝 Licencja

MIT License - feel free to modify and distribute!

## 🤝 Wkład

Pull requesty mile widziane! 

## 📧 Wsparcie

Issues: https://github.com/stasek44/sprsun-modbus/issues
