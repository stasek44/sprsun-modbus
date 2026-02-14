# Configuration Example

## Basic Example

Minimal working configuration via UI:

```yaml
# This is NOT configuration.yaml!
# Use UI: Settings → Devices & Services → Add Integration

Name: SPRSUN Heat Pump
Host: 192.168.1.234
Port: 502
Device Address: 1
Scan Interval: 10
```

## Advanced Configuration

### Lovelace Dashboard Card

```yaml
type: vertical-stack
cards:
  - type: entities
    title: SPRSUN Heat Pump - Status
    entities:
      - entity: sensor.sprsun_heat_pump_cop
        name: COP
        icon: mdi:gauge
      - entity: sensor.sprsun_heat_pump_compressor_runtime
        name: Runtime
      - entity: binary_sensor.sprsun_heat_pump_hotwater_demand
        name: Hot Water Mode
      - entity: binary_sensor.sprsun_heat_pump_heating_demand
        name: Heating Mode
      - entity: binary_sensor.sprsun_heat_pump_alarm_stop
        name: Alarm Status
  
  - type: entities
    title: Temperatures
    entities:
      - entity: sensor.sprsun_heat_pump_inlet_water_temperature
      - entity: sensor.sprsun_heat_pump_outlet_water_temperature
      - entity: sensor.sprsun_heat_pump_hot_water_temperature
      - entity: sensor.sprsun_heat_pump_ambient_temperature
  
  - type: entities
    title: Control
    entities:
      - entity: number.sprsun_heat_pump_heating_setpoint
      - entity: number.sprsun_heat_pump_cooling_setpoint
      - entity: number.sprsun_heat_pump_hot_water_setpoint
      - entity: number.sprsun_heat_pump_unit_mode
```

### Automation Examples

#### 1. Antilegionella Weekly Schedule

```yaml
automation:
  - alias: "SPRSUN: Antilegionella Monday 2am"
    description: Run antilegionella cycle every Monday at 2am
    trigger:
      - platform: time
        at: "01:55:00"
    condition:
      - condition: time
        weekday:
          - mon
    action:
      - service: number.set_value
        target:
          entity_id: number.sprsun_heat_pump_antilegionella_weekday
        data:
          value: 1  # Monday
      - service: number.set_value
        target:
          entity_id: number.sprsun_heat_pump_antilegionella_start_hour
        data:
          value: 2
      - service: number.set_value
        target:
          entity_id: number.sprsun_heat_pump_antilegionella_end_hour
        data:
          value: 3
      - service: number.set_value
        target:
          entity_id: number.sprsun_heat_pump_antilegionella_temperature
        data:
          value: 60
```

#### 2. Economic Mode - Temperature Based

```yaml
automation:
  - alias: "SPRSUN: Economic Mode Adjust"
    description: Adjust heating setpoint based on outdoor temp
    trigger:
      - platform: state
        entity_id: sensor.sprsun_heat_pump_ambient_temperature
    action:
      - choose:
          # Very cold: < 0°C → 50°C setpoint
          - conditions:
              - condition: numeric_state
                entity_id: sensor.sprsun_heat_pump_ambient_temperature
                below: 0
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.sprsun_heat_pump_heating_setpoint
                data:
                  value: 50
          
          # Cold: 0-10°C → 45°C setpoint  
          - conditions:
              - condition: numeric_state
                entity_id: sensor.sprsun_heat_pump_ambient_temperature
                above: 0
                below: 10
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.sprsun_heat_pump_heating_setpoint
                data:
                  value: 45
          
          # Mild: 10-15°C → 40°C setpoint
          - conditions:
              - condition: numeric_state
                entity_id: sensor.sprsun_heat_pump_ambient_temperature
                above: 10
                below: 15
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.sprsun_heat_pump_heating_setpoint
                data:
                  value: 40
          
          # Warm: > 15°C → 35°C setpoint
          - conditions:
              - condition: numeric_state
                entity_id: sensor.sprsun_heat_pump_ambient_temperature
                above: 15
            sequence:
              - service: number.set_value
                target:
                  entity_id: number.sprsun_heat_pump_heating_setpoint
                data:
                  value: 35
```

#### 3. Low COP Alert

```yaml
automation:
  - alias: "SPRSUN: Low COP Alert"
    description: Notify when COP drops below 2.5
    trigger:
      - platform: numeric_state
        entity_id: sensor.sprsun_heat_pump_cop
        below: 250  # COP 2.5 (raw value 250)
        for:
          minutes: 10
    action:
      - service: notify.mobile_app
        data:
          title: "Heat Pump Low Efficiency"
          message: "COP dropped to {{ states('sensor.sprsun_heat_pump_cop') | float / 100 }}"
```

### Template Sensors

#### Human-Readable Unit Mode

```yaml
template:
  - sensor:
      - name: "SPRSUN Unit Mode Text"
        state: >
          {% set mode = states('number.sprsun_heat_pump_unit_mode') | int %}
          {% set modes = {
            0: 'Hot Water Only',
            1: 'Heating Only',
            2: 'Cooling Only',
            3: 'Heating + Hot Water',
            4: 'Cooling + Hot Water'
          } %}
          {{ modes.get(mode, 'Unknown') }}
        icon: mdi:heat-pump
```

#### Temperature Delta

```yaml
template:
  - sensor:
      - name: "SPRSUN Water Temperature Delta"
        unit_of_measurement: "°C"
        device_class: temperature
        state: >
          {{ (states('sensor.sprsun_heat_pump_outlet_water_temperature') | float - 
              states('sensor.sprsun_heat_pump_inlet_water_temperature') | float) | round(1) }}
```

#### Real COP (Scaled)

```yaml
template:
  - sensor:
      - name: "SPRSUN COP Real"
        unit_of_measurement: ""
        state: >
          {{ (states('sensor.sprsun_heat_pump_cop') | float / 100) | round(2) }}
        icon: mdi:gauge
```

### Energy Dashboard Integration

```yaml
# configuration.yaml

homeassistant:
  customize:
    sensor.sprsun_heat_pump_heating_cooling_capacity:
      state_class: measurement
    sensor.sprsun_heat_pump_ac_voltage:
      state_class: measurement
```

Then add to Energy Dashboard:
- Settings → Dashboards → Energy
- Add "Heating" source → sensor.sprsun_heat_pump_heating_cooling_capacity

### History Graph

```yaml
type: history-graph
title: Heat Pump Performance
hours_to_show: 24
entities:
  - entity: sensor.sprsun_heat_pump_cop
    name: COP
  - entity: sensor.sprsun_heat_pump_inlet_water_temperature
    name: Inlet
  - entity: sensor.sprsun_heat_pump_outlet_water_temperature
    name: Outlet
  - entity: sensor.sprsun_heat_pump_ambient_temperature
    name: Outdoor
```

## Scan Interval Tuning

### Recommended Settings

| Use Case | Scan Interval | Elfin Timeout | Notes |
|----------|---------------|---------------|-------|
| Default | 10s | 30s | Balanced |
| Responsive | 5s | 20s | More load |
| Conservative | 30s | 60s | Low traffic |
| Debug | 2s | 10s | Testing only |

### Change Scan Interval

1. Settings → Devices & Services
2. Find SPRSUN integration
3. Click "Configure"
4. Set "Scan Interval" (5-300s)
5. Submit → **Auto-reloads** (no HA restart!)

## Multiple Heat Pumps

To add multiple heat pumps:

1. Add integration multiple times
2. Use different names:
   - "SPRSUN Ground Floor"
   - "SPRSUN First Floor"
3. Each needs unique Elfin W11 gateway
4. Or one gateway with different Modbus addresses (if supported)

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues.
