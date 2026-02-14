# Installation Guide

## Prerequisites

1. **SPRSUN Heat Pump** with Modbus RTU (RS485)
2. **Elfin W11 Gateway** (RS485 to Ethernet/WiFi converter)
3. **Home Assistant** 2024.1.0 or newer
4. **Network connectivity** between HA and Elfin W11

## Hardware Setup

### 1. Connect RS485 Cable

**Heat Pump Side:**
- Locate Modbus terminals (usually A, B, GND)
- Check your pump's manual for exact pinout

**Elfin EW11 Side:**
```
A (or D+)  → Heat pump A/D+
B (or D-)  → Heat pump B/D-
GND        → Heat pump GND
```

**RS485 Wiring:**
- Use twisted pair cable for A/B
- Maximum distance: ~1000m
- Add 120Ω termination resistor if needed (check manual)

### 2. Configure Elfin W11

#### Via Web Interface

1. Connect to Elfin:
   - Ethernet: Direct cable connection
   - WiFi: Connect to Elfin_XXXXXX AP (default)

2. Open browser: `http://192.168.X.X` (check Elfin's IP)
   - Default login: `admin` / `admin`

3. **Serial Port Settings:**
   ```
   Baud rate: 9600
   Data bits: 8
   Stop bits: 1
   Parity: None (or Even - check your pump!)
   Flow control: None
   ```

4. **Network Settings:**
   ```
   Protocol: Modbus TCP
   Port: 502
   Timeout: 30s          ← IMPORTANT!
   Keep alive: 65s
   Max accept: 2
   ```

5. **Save & Restart** Elfin

#### Verify Connection

```bash
# From any PC on the network:
telnet 192.168.1.234 502
```

If connection successful → gateway is working!

### 3. Test Modbus Communication

Use a Modbus client to verify:

**Option A: modpoll (command line)**
```bash
modpoll -m tcp -a 1 -r 0 -c 10 192.168.1.234
# Should return values from registers 0-9
```

**Option B: Python script (included in repo)**
```bash
cd /path/to/sprsun-modbus
source .venv/bin/activate
python modbus_debug_poller.py
# Should print values to console and CSV
```

## Software Installation

### Method 1: HACS (Recommended)

1. **Install HACS** (if not already):
   - Follow: https://hacs.xyz/docs/setup/download

2. **Add Custom Repository:**
   - HACS → Integrations → ⋮ (menu) → Custom repositories
   - Repository: `https://github.com/stasek44/sprsun-modbus`
   - Category: `Integration`
   - Click "Add"

3. **Install Integration:**
   - Search for "SPRSUN Heat Pump Modbus"
   - Click "Download"
   - Restart Home Assistant

### Method 2: Manual Installation

1. **Download Integration:**
   ```bash
   cd /config
   mkdir -p custom_components
   cd custom_components
   git clone https://github.com/stasek44/sprsun-modbus.git
   mv sprsun-modbus/custom_components/sprsun_modbus .
   rm -rf sprsun-modbus
   ```

2. **Restart Home Assistant**

3. **Verify Installation:**
   - Check logs for errors: Settings → System → Logs
   - Filter: "sprsun"

## Configuration

### Via UI (Recommended)

1. **Add Integration:**
   - Settings → Devices & Services
   - Click "+ Add Integration"
   - Search: "SPRSUN"

2. **Fill Form:**
   ```
   Name: SPRSUN Heat Pump (or your choice)
   Host: 192.168.1.234 (Elfin W11 IP)
   Port: 502
   Device Address: 1 (usually 1, check pump manual)
   Scan Interval: 10 (seconds, recommended)
   ```

3. **Submit** → Integration should appear with device

4. **Verify Entities:**
   - Click on device
   - Should see ~92 entities (50+6+36)
   - Check if values are realistic

### Via Configuration.yaml (Not Supported)

This integration uses **Config Flow only**. Manual YAML configuration is not available.

## Post-Installation

### 1. Verify Data

Check entity values make sense:
- Temperatures: 0-100°C range
- COP: 2-5 range (typical)
- Pressures: positive values
- Binary sensors: logical states

### 2. Create Dashboards

Example Lovelace card:

```yaml
type: entities
title: SPRSUN Heat Pump
entities:
  - entity: sensor.sprsun_heat_pump_inlet_water_temperature
  - entity: sensor.sprsun_heat_pump_outlet_water_temperature
  - entity: sensor.sprsun_heat_pump_ambient_temperature
  - entity: sensor.sprsun_heat_pump_cop
  - entity: binary_sensor.sprsun_heat_pump_hotwater_demand
  - entity: binary_sensor.sprsun_heat_pump_heating_demand
  - entity: number.sprsun_heat_pump_heating_setpoint
```

### 3. Configure Scan Interval

**To change scan interval after installation:**

1. Settings → Devices & Services
2. Find SPRSUN integration
3. Click "Configure"
4. Adjust "Scan Interval" (5-300 seconds)
5. Submit → **Integration auto-reloads!** (no HA restart needed)

**Recommended values:**
- 10s: Default, good balance
- 5s: Responsive, more load
- 30s: Conservative, less network traffic

**Remember:** Elfin timeout should be ≥ scan_interval + 20s

### 4. Set Up Automations

Example: Turn on auxiliary heating when outdoor temp drops

```yaml
automation:
  - alias: "Enable Aux Heating Cold Weather"
    trigger:
      - platform: numeric_state
        entity_id: sensor.sprsun_heat_pump_ambient_temperature
        below: -5
    action:
      - service: number.set_value
        target:
          entity_id: number.sprsun_heat_pump_heating_heater_ambient_temp
        data:
          value: -3
```

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues.

**Quick checks:**
1. Elfin W11 reachable? `ping 192.168.1.234`
2. Port open? `telnet 192.168.1.234 502`
3. Heat pump ON? (Modbus only works when powered)
4. Check HA logs: Settings → System → Logs → Filter "sprsun"

## Next Steps

- [Configuration Guide](configuration.md)
- [Elfin W11 Detailed Setup](elfin_configuration.md)
- [Troubleshooting](troubleshooting.md)
- [Integration Architecture](../BATCH_READ_EXPLANATION.md)
