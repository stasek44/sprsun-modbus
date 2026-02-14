# Home Assistant - Kompletna Konfiguracja Modbus dla SPRSUN

## 📋 configuration.yaml

```yaml
# Dodaj do swojego configuration.yaml

modbus:
  - name: sprsun_heat_pump
    type: tcp
    host: 192.168.1.234
    port: 502
    timeout: 3
    delay: 0
    
    # ==========================================
    # SENSORS (Read-Only) - Temperatury
    # ==========================================
    sensors:
      # Temperatury wody
      - name: "SPRSUN Inlet Temperature"
        unique_id: sprsun_inlet_temp
        address: 0x000E
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
        scan_interval: 10
        
      - name: "SPRSUN Hotwater Temperature"
        unique_id: sprsun_hotwater_temp
        address: 0x000F
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
        scan_interval: 10
        
      - name: "SPRSUN Heating Temperature"
        unique_id: sprsun_heating_temp
        address: 0x0011
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
        scan_interval: 10
        
      - name: "SPRSUN Ambient Temperature"
        unique_id: sprsun_ambient_temp
        address: 0x0012
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
        scan_interval: 10
        
      - name: "SPRSUN Coil Temperature"
        unique_id: sprsun_coil_temp
        address: 0x0016
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
        scan_interval: 10
        
      - name: "SPRSUN Exhaust Temperature"
        unique_id: sprsun_exhaust_temp
        address: 0x0017
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
        scan_interval: 10
      
      # Ciśnienia
      - name: "SPRSUN High Pressure"
        unique_id: sprsun_high_pressure
        address: 0x001B
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "bar"
        device_class: pressure
        state_class: measurement
        scan_interval: 10
        
      - name: "SPRSUN Low Pressure"
        unique_id: sprsun_low_pressure
        address: 0x001C
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.1
        precision: 1
        unit_of_measurement: "bar"
        device_class: pressure
        state_class: measurement
        scan_interval: 10
      
      # Status i wydajność
      - name: "SPRSUN COP"
        unique_id: sprsun_cop
        address: 0x0001
        slave: 1
        input_type: holding
        data_type: int16
        scale: 1.0
        precision: 0
        state_class: measurement
        scan_interval: 10
        
      - name: "SPRSUN Compressor Frequency"
        unique_id: sprsun_comp_freq
        address: 0x001D
        slave: 1
        input_type: holding
        data_type: int16
        scale: 1.0
        precision: 0
        unit_of_measurement: "Hz"
        state_class: measurement
        scan_interval: 10
        
      - name: "SPRSUN Inverter Power"
        unique_id: sprsun_inverter_power
        address: 0x0029
        slave: 1
        input_type: holding
        data_type: int16
        scale: 1.0
        precision: 0
        unit_of_measurement: "W"
        device_class: power
        state_class: measurement
        scan_interval: 10
        
      # Setpointy (READ - do wyświetlania aktualnych ustawień)
      - name: "SPRSUN Heating Setpoint Current"
        unique_id: sprsun_heating_setp_sensor
        address: 0x00CC
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.5
        precision: 1
        unit_of_measurement: "°C"
        device_class: temperature
        scan_interval: 10
        
      - name: "SPRSUN Cooling Setpoint Current"
        unique_id: sprsun_cooling_setp_sensor
        address: 0x00CB
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.5
        precision: 1
        unit_of_measurement: "°C"
        device_class: temperature
        scan_interval: 10
        
      - name: "SPRSUN Hotwater Setpoint Current"
        unique_id: sprsun_hotwater_setp_sensor
        address: 0x00CA
        slave: 1
        input_type: holding
        data_type: int16
        scale: 0.5
        precision: 1
        unit_of_measurement: "°C"
        device_class: temperature
        scan_interval: 10
      
      # Tryb pracy (do wyświetlania)
      - name: "SPRSUN Unit Mode"
        unique_id: sprsun_unit_mode_sensor
        address: 0x0036
        slave: 1
        input_type: holding
        data_type: int16
        scan_interval: 10
        # 0=DHW, 1=Heating, 2=Cooling, 3=Heating+DHW, 4=Cooling+DHW
      
      # Wersje oprogramowania
      - name: "SPRSUN Software Version Year"
        unique_id: sprsun_sw_version_year
        address: 0x0013
        slave: 1
        input_type: holding
        data_type: int16
        scan_interval: 300  # Rzadko się zmienia
        
      - name: "SPRSUN Controller Version"
        unique_id: sprsun_controller_version
        address: 0x002C
        slave: 1
        input_type: holding
        data_type: int16
        scan_interval: 300
    
    # ==========================================
    # BINARY SENSORS - Flagi ON/OFF
    # ==========================================
    binary_sensors:
      # Status pracy
      - name: "SPRSUN Compressor Running"
        unique_id: sprsun_compressor_running
        address: 0x0004
        slave: 1
        input_type: holding
        scan_interval: 10
        device_class: running
      
      - name: "SPRSUN Fan Running"
        unique_id: sprsun_fan_running
        address: 0x0004
        slave: 1
        input_type: holding
        scan_interval: 10
        device_class: running
      
      # Alarmy (przykład - możesz dodać więcej z rejestrów 0x0007-0x000D)
      - name: "SPRSUN Alarm Active"
        unique_id: sprsun_alarm
        address: 0x0007
        slave: 1
        input_type: holding
        scan_interval: 10
        device_class: problem
    
    # ==========================================
    # NUMBERS - Zmiana Setpointów (READ+WRITE)
    # ==========================================
    numbers:
      - name: "SPRSUN Heating Setpoint"
        unique_id: sprsun_heating_setpoint
        address: 0x00CC
        slave: 1
        data_type: int16
        scale: 0.5
        precision: 1
        min_value: 10
        max_value: 55
        step: 0.5
        unit_of_measurement: "°C"
        mode: slider
        device_class: temperature
        
      - name: "SPRSUN Cooling Setpoint"
        unique_id: sprsun_cooling_setpoint
        address: 0x00CB
        slave: 1
        data_type: int16
        scale: 0.5
        precision: 1
        min_value: 12
        max_value: 30
        step: 0.5
        unit_of_measurement: "°C"
        mode: slider
        device_class: temperature
        
      - name: "SPRSUN Hotwater Setpoint"
        unique_id: sprsun_hotwater_setpoint
        address: 0x00CA
        slave: 1
        data_type: int16
        scale: 0.5
        precision: 1
        min_value: 10
        max_value: 55
        step: 0.5
        unit_of_measurement: "°C"
        mode: slider
        device_class: temperature
    
    # ==========================================
    # SELECT - Wybór Trybu Pracy (READ+WRITE)
    # ==========================================
    selects:
      - name: "SPRSUN Operating Mode"
        unique_id: sprsun_operating_mode
        address: 0x0036
        slave: 1
        data_type: int16
        scan_interval: 10
        options:
          0: "DHW Only"
          1: "Heating Only"
          2: "Cooling Only"
          3: "Heating + DHW"
          4: "Cooling + DHW"
```

---

## 📊 Lovelace Dashboard (UI)

Przykładowa karta do wyświetlania w Home Assistant:

```yaml
# W pliku ui-lovelace.yaml lub przez UI Editor

type: vertical-stack
cards:
  # Temperatury
  - type: entities
    title: SPRSUN Temperatures
    entities:
      - entity: sensor.sprsun_inlet_temperature
        name: Inlet Water
      - entity: sensor.sprsun_hotwater_temperature
        name: Hot Water Tank
      - entity: sensor.sprsun_heating_temperature
        name: Heating Water
      - entity: sensor.sprsun_ambient_temperature
        name: Outdoor Air
      - entity: sensor.sprsun_coil_temperature
        name: Coil
      - entity: sensor.sprsun_exhaust_temperature
        name: Exhaust Gas
  
  # Setpointy (kontrola)
  - type: entities
    title: SPRSUN Setpoints
    entities:
      - entity: number.sprsun_heating_setpoint
        name: Heating Target
      - entity: number.sprsun_cooling_setpoint
        name: Cooling Target
      - entity: number.sprsun_hotwater_setpoint
        name: Hot Water Target
  
  # Tryb pracy
  - type: entities
    title: SPRSUN Operating Mode
    entities:
      - entity: select.sprsun_operating_mode
        name: Mode
      - entity: sensor.sprsun_unit_mode
        name: Current Mode (sensor)
  
  # Status i wydajność
  - type: entities
    title: SPRSUN Performance
    entities:
      - entity: sensor.sprsun_cop
        name: COP
      - entity: sensor.sprsun_compressor_frequency
        name: Compressor Frequency
      - entity: sensor.sprsun_inverter_power
        name: Power Consumption
      - entity: sensor.sprsun_high_pressure
        name: High Pressure
      - entity: sensor.sprsun_low_pressure
        name: Low Pressure
  
  # Wykresy
  - type: history-graph
    title: Temperature History (24h)
    hours_to_show: 24
    entities:
      - entity: sensor.sprsun_inlet_temperature
        name: Inlet
      - entity: sensor.sprsun_hotwater_temperature
        name: Hot Water
      - entity: sensor.sprsun_heating_temperature
        name: Heating
      - entity: sensor.sprsun_ambient_temperature
        name: Outdoor
  
  - type: history-graph
    title: Performance History (24h)
    hours_to_show: 24
    entities:
      - entity: sensor.sprsun_cop
        name: COP
      - entity: sensor.sprsun_compressor_frequency
        name: Frequency
```

---

## 🔧 Konfiguracja Zaawansowana

### Template Sensors (opcjonalnie)

```yaml
# configuration.yaml

template:
  - sensor:
      # Przelicz tryb na tekst czytelny
      - name: "SPRSUN Mode Text"
        unique_id: sprsun_mode_text
        state: >
          {% set mode = states('sensor.sprsun_unit_mode') | int %}
          {% if mode == 0 %}DHW Only
          {% elif mode == 1 %}Heating Only
          {% elif mode == 2 %}Cooling Only
          {% elif mode == 3 %}Heating + DHW
          {% elif mode == 4 %}Cooling + DHW
          {% else %}Unknown
          {% endif %}
      
      # Delta temperatura inlet-outlet
      - name: "SPRSUN Temperature Delta"
        unique_id: sprsun_temp_delta
        unit_of_measurement: "°C"
        state: >
          {{ (states('sensor.sprsun_heating_temperature') | float - 
              states('sensor.sprsun_inlet_temperature') | float) | round(1) }}
      
      # Status czy grzeje czy chłodzi
      - name: "SPRSUN Active Operation"
        unique_id: sprsun_active_op
        state: >
          {% if is_state('binary_sensor.sprsun_compressor_running', 'on') %}
            {% set mode = states('sensor.sprsun_unit_mode') | int %}
            {% if mode == 1 or mode == 3 %}Heating
            {% elif mode == 2 or mode == 4 %}Cooling
            {% elif mode == 0 %}Hot Water
            {% else %}Running
            {% endif %}
          {% else %}
            Idle
          {% endif %}
```

---

## 🚀 Wdrożenie Krok Po Kroku

### 1. Dodaj konfigurację
```bash
# Edytuj configuration.yaml
nano /config/configuration.yaml

# Wklej sekcję modbus: z góry
```

### 2. Sprawdź składnię
```bash
# Home Assistant → Developer Tools → YAML
# Kliknij "CHECK CONFIGURATION"
```

### 3. Restart HA
```bash
# Developer Tools → Server Controls → "Restart"
```

### 4. Sprawdź sensory
```bash
# Developer Tools → States
# Szukaj: sprsun
# Powinno być ~15-20 sensorów
```

### 5. Test zapisu
```bash
# Settings → Devices & Services → Modbus
# Znajdź "number.sprsun_heating_setpoint"
# Zmień wartość przez UI
# Sprawdź czy pompa zareagowała
```

---

## ⚠️ Znane Problemy i Rozwiązania

### Problem: "Entity not available"

**Rozwiązanie:**
```bash
# Sprawdź logi:
# Settings → System → Logs

# Sprawdź połączenie Modbus:
ping 192.168.1.234

# Test z Python:
.venv/bin/python -c "
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('192.168.1.234', port=502)
print('Connected:', client.connect())
"
```

### Problem: Write nie działa

**Przyczyna:** Device address = 1 (master), tylko #1 może zapisywać

**Rozwiązanie:**
Upewnij się że `slave: 1` we wszystkich entities

### Problem: Wartości dziwne (np. 655.35°C)

**Przyczyna:** Signed/unsigned int problem

**Rozwiązanie:**
```yaml
# Zmień data_type:
data_type: int16  # signed
# lub:
data_type: uint16  # unsigned
```

---

## 📈 Monitoring i Debugging

### Enable detailed logging
```yaml
# configuration.yaml

logger:
  default: info
  logs:
    homeassistant.components.modbus: debug
    pymodbus.client: debug
```

### Sprawdź statystyki
```bash
# Developer Tools → Statistics
# Entity: sensor.sprsun_inlet_temperature
# Zobacz history, min, max, avg
```

---

## 🎯 Gotowe Szablony Automatyzacji

### Auto-adjust setpoint based on outdoor temp
```yaml
# automations.yaml

- alias: "SPRSUN Auto Adjust Heating"
  trigger:
    - platform: numeric_state
      entity_id: sensor.sprsun_ambient_temperature
      below: 0
  action:
    - service: number.set_value
      target:
        entity_id: number.sprsun_heating_setpoint
      data:
        value: 25  # Zwiększ do 25°C gdy < 0°C na zewnątrz

- alias: "SPRSUN Auto Adjust Heating Warmer"
  trigger:
    - platform: numeric_state
      entity_id: sensor.sprsun_ambient_temperature
      above: 10
  action:
    - service: number.set_value
      target:
        entity_id: number.sprsun_heating_setpoint
      data:
        value: 20  # Zmniejsz do 20°C gdy > 10°C
```

### Alert na wysoki COP (efektywność)
```yaml
- alias: "SPRSUN High Efficiency Alert"
  trigger:
    - platform: numeric_state
      entity_id: sensor.sprsun_cop
      above: 4
  action:
    - service: notify.mobile_app
      data:
        title: "SPRSUN Running Efficiently!"
        message: "COP = {{ states('sensor.sprsun_cop') }}"
```

---

Gotowe! 🎉 Masz teraz pełną integrację SPRSUN z Home Assistant.
