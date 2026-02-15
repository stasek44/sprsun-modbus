# SPRSUN Heat Pump Modbus Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/stasek44/sprsun-modbus.svg)](https://github.com/stasek44/sprsun-modbus/releases)
[![License](https://img.shields.io/github/license/stasek44/sprsun-modbus.svg)](LICENSE)

Home Assistant integration for SPRSUN heat pumps via Modbus TCP (using Elfin-EW11/W11 gateway).

> ⚠️ **Important:** This integration has been tested on **one heat pump model only - CGK-025V3L-B**, not all parameters have been verified. SPRSUN heat pumps use at least **two different controller types** - this integration currently supports only one. If you have a different model and would like to contribute, please open an issue!

## Features

- **100+ Entities**: 50 read-only sensors, 43 binary sensors, 45 number entities, 3 select controls, 3 switches, 1 button
- **Comprehensive Monitoring**: All temperature sensors, pressures, power metrics, COP, status flags, error codes
- **Full Control**: Operating modes, setpoints, economic mode curves, antilegionella, pump modes
- **Batch Reading**: All read-only parameters in ONE request (~200ms) for optimal performance
- **Safe Writes**: Optimized write operations with bit manipulation protection
- **Documentation**: Comprehensive [parameter guide](docs/PARAMETERS_GUIDE.md) and [Modbus reference](docs/MODBUS_REFERENCE.md)

## Quick Start

### Hardware Setup

**Requirements:**
- SPRSUN heat pump with Modbus RTU interface
- Elfin-EW11 or W11 RS485 to TCP/WiFi gateway
- Ethernet or WiFi network connection

**Wiring:**

Connect RS485 from heat pump to Elfin gateway:
- **A/+** (heat pump) → **A** (Elfin terminal)
- **B/-** (heat pump) → **B** (Elfin terminal)
- **GND** (heat pump) → **GND** (Elfin terminal, recommended for noise reduction)

**Elfin W11 Configuration:**

1. Connect to Elfin web interface: `http://192.168.1.234` (default IP, check router DHCP if needed)
2. Configure serial port settings:
   - **Mode:** TCP Server
   - **Baud Rate:** 19200
   - **Data Bits:** 8
   - **Stop Bits:** 2
   - **Parity:** None
   - **Port:** 502 (Modbus TCP standard)
   - **Timeout:** 30s (recommended)
   - **Max Accept:** 1 (important - prevents connection conflicts)
3. Save and reboot gateway

### Installation

#### Via HACS (Recommended)
1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the three dots (⋮) in the top right
4. Select "Custom repositories"
5. Add repository: `https://github.com/stasek44/sprsun-modbus`
6. Category: "Integration"
7. Click "Add"
8. Find "SPRSUN Modbus" in HACS and click "Download"
9. Restart Home Assistant

#### Manual Installation
```bash
cd /config/custom_components/
git clone https://github.com/stasek44/sprsun-modbus.git sprsun_modbus
# Restart Home Assistant
```

### Add Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for "SPRSUN"
3. Enter connection details:
   - **Host**: Elfin W11 IP address (e.g., `192.168.1.234`)
   - **Port**: `502` (Modbus TCP standard)
   - **Device Address**: `1` (only address #1 can write parameters!)
   - **Name**: Your heat pump name (e.g., "Heat Pump")
   - **Scan Interval**: `30` seconds (recommended balance between responsiveness and load)
4. Click "Submit"
5. Integration will create 100+ entities automatically

## Entities

The integration provides 100+ entities organized into 6 platforms:

### Sensors (50 read-only)
- **Temperatures**: Inlet, outlet, hot water, ambient, evaporator, condenser, coil, suction gas, discharge gas, driving temp
- **Pressures**: Suction (low side), discharge (high side) - note: register labels are swapped in documentation!
- **Power Metrics**: Heating/cooling capacity (W), AC voltage (V), AC current (A), compressor current (A)
- **Performance**: COP (Coefficient of Performance), compressor runtime (hours)
- **Operating State**: Compressor frequency, target frequency, fan speeds, pump flow
- **Diagnostics**: EEV valve positions, DC bus voltage, software versions

### Binary Sensors (43)
Decoded from 11 bitfield registers:

**Switching Inputs (7):**
- A/C linkage, linkage switch, heating/cooling linkage
- Flow switch, high pressure switch, phase sequence

**Working Status (6):**
- Hot water demand, heating demand, cooling demand
- Defrost active, antilegionella active, alarm stop

**Outputs (12):**
- Compressor, fans, 4-way valve, 3-way valve
- Heaters (chassis, heating, hot water, crank)
- Pumps (A/C, circulation), solenoid valve

**Failures (18):**
- Temperature sensor failures (6 sensors)
- Pressure protections (low/high)
- Flow failure, antifreeze protections
- Exhaust overheat, coil overheat
- DC fan failures, inverter faults

### Number Entities (45 read-write)

**Basic Setpoints (P01-P07):**
- P01: Heating setpoint (10-55°C)
- P02: Cooling setpoint (12-30°C)
- P03: Heating/cooling differential (2-18°C)
- P04: Hot water setpoint (10-55°C)
- P05: Hot water differential (2-18°C)

**Economic Mode (E01-E24):**
- E01-E04: Heating curve ambient temps (-30 to 50°C, signed!)
- E05-E08: DHW curve ambient temps (-30 to 50°C, signed!)
- E09-E12: Cooling curve ambient temps (-30 to 50°C, signed!)
- E13-E16: Heating curve target temps (10-55°C)
- E17-E20: DHW curve target temps (10-55°C)
- E21-E24: Cooling curve target temps (12-30°C)

**General Settings (G01-G11):**
- G03: Start interval (1-120 min)
- G04: Delta temp for DC pump (5-30°C)
- G05/G07: External heater activation temps (-30 to 30°C, signed!)
- G06/G08: Compressor delays (1-60 min)
- G10: Ambient switch setpoint (-20 to 30°C, signed!)
- G11: Ambient switch differential (1-10°C)

**Antilegionella:**
- Temperature setpoint (30-70°C)
- Weekday (0=Sunday to 6=Saturday)
- Start hour (0-23)
- End hour (0-23)

### Select Entities (3)
- **P06 Unit Mode**: DHW / Heating / Cooling / Heating+DHW / Cooling+DHW
- **P07 Fan Mode**: Normal / Economic / Night / Test
- **G02 Pump Work Mode**: Interval / Normal / Demand
- **G09 Mode Control**: NO linkage / YES amb (auto mode switching)

### Switch Entities (3)
- **Power**: Main ON/OFF switch (register 0x0032 bit 0)
- **Antilegionella Enable**: Enable/disable Legionella protection (0x0034 bit 0)
- **Two/Three Function**: Switch between 2-function and 3-function mode (0x0034 bit 1)

### Button Entity (1)
- **Failure Reset**: Reset all alarms after resolving the cause (register 0x0033 bit 7)

> 📖 **For detailed explanations of what each parameter does, see [PARAMETERS_GUIDE.md](docs/PARAMETERS_GUIDE.md)** (Polish language guide with examples and troubleshooting)

## Testing

### Local Hardware Test (No Home Assistant Required)

```bash
# Test batch read consistency with your device
python scripts/test_local.py

# Customize connection
MODBUS_HOST=192.168.1.100 python scripts/test_local.py
```

Expected output:
```
✅ PASSED: connection
✅ PASSED: batch_read  (50 registers in ~200ms)
✅ PASSED: batch_vs_individual  ← Validates no value mismatches
✅ PASSED: consistency
✅ PASSED: performance

Results: 5/5 tests passed
CSV outputs saved to: tests/output/
```

**Key test**: `batch_vs_individual` - validates batch read returns identical values to individual reads (no offset/misalignment).

[See full testing guide →](docs/testing.md)

### Unit Tests

```bash
pip install -r requirements_dev.txt
pytest tests/ -v --cov
```

## Performance

- **Read-Only (50 registers)**: ONE batch request ~200ms
- **Binary Sensors (43 from 11 bitfields)**: Read in RO batch (no extra requests)
- **Total per scan**: ~250ms for all monitoring
- **RW Parameters (45)**: Read individually at startup (~4500ms once)
- **Write Operations**: No immediate refresh - cache updated locally, verified on next scan

Network efficiency: **20x faster** than individual reads (250ms vs 5000ms)

## Configuration Examples

### Lovelace Dashboard

```yaml
type: entities
entities:
  - entity: sensor.sprsun_inlet_temp
  - entity: sensor.sprsun_outlet_temp
  - entity: sensor.sprsun_hotwater_temp
  - entity: sensor.sprsun_cop
  - entity: sensor.sprsun_heating_capacity
  - entity: binary_sensor.sprsun_heating_mode
```

### Automations

```yaml
# Low COP Alert
automation:
  - alias: "Heat Pump Low COP Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.sprsun_cop
        below: 2.0
    action:
      - service: notify.mobile_app
        data:
          message: "Heat pump COP dropped to {{ states('sensor.sprsun_cop') }}"
```

[See more examples →](docs/configuration.md)

## Documentation

### User Guides
- 📖 **[PARAMETERS_GUIDE.md](docs/PARAMETERS_GUIDE.md)** - Comprehensive guide (Polish) explaining what each parameter controls, with practical examples and troubleshooting tips
- 📚 **[MODBUS_REFERENCE.md](docs/MODBUS_REFERENCE.md)** - Complete Modbus protocol reference with all register addresses, data types, scales, and communication details

### Technical Notes
- **Signed Integers**: 5 RO + 15 RW temperature registers use signed int16 (can be negative for winter outdoor temps)
- **Pressure Scale**: Values reported in 0.1 PSI, converted to bar (multiply by 0.0069)
- **Register Swap**: Pressure registers 0x002F/0x0030 labels are swapped in original documentation
- **Batch Reading**: All 50 RO registers + 11 bitfield status registers read in one request
- **Write Protection**: Only device address #1 can modify parameters (per Modbus protocol spec)
- **Connection Management**: Single persistent connection prevents Elfin max_accept=1 conflicts

## Troubleshooting

### Connection Issues

```bash
# Test Modbus connection
telnet 192.168.1.234 502

# Run diagnostics
python scripts/test_local.py
```

### Parameter Values Seem Wrong

1. Check if register uses signed integers (temperatures can be negative)
2. Verify pressure scale (values in 0.1 PSI, not bar)
3. Note: Pressure registers 0x002F/0x0030 are swapped in documentation
4. Run test script to validate Modbus communication:
   ```bash
   python scripts/test_local.py
   ```

### Values Not Updating

Check:
- Scan interval in integration options (default: 30s)
- Home Assistant logs for errors
- Elfin W11 web interface shows active connection

## To Do

Contributions welcome! Priority development tasks:

### Core Improvements
- [ ] **Options flow** - Allow changing integration settings (host, port, scan interval) without removing/re-adding
- [ ] **Verify all registers** - Test on multiple heat pump models to confirm register map accuracy
- [ ] **Multiple register write optimization** - Use Modbus command 10H (write multiple) for batch parameter updates
- [ ] **Unit tests** - Evaluate necessity and add test coverage for core functionality

### Documentation
- [ ] **Analyze pump manual** - Add Elfin settings for reference
- [ ] **Analyze pump manual** - Cross-reference with PARAMETERS_GUIDE for accuracy
- [ ] **English parameter guide** - Translate PARAMETERS_GUIDE.md to English

### Publishing & Branding
- [ ] **Integration logo** - Design and add custom logo
- [ ] **Publish to HACS** - Submit to HACS default repository
- [ ] **Add badges** - HACS install button, Buy Me a Coffee button
- [ ] **GitHub workflows** - Add HACS validation and automated tests

### Known Issues
- [ ] **RW field momentary revert** - After writing RW parameter in HA, value briefly reverts to old state before updating (cosmetic, resolved on next coordinator poll)
- [ ] **Batch read RW registers** - Investigate if RW registers can be batch-read (currently read individually due to sparse address space)

### Controller Support
- [ ] **Additional controller types** - SPRSUN uses at least 2 different controller types. This integration supports one. Looking for contributors with different models!

## Known Limitations

- **Controller compatibility**: Tested on one controller type only. SPRSUN heat pumps may have different register maps.
- **Parameter verification**: Not all parameters tested in real-world scenarios.
- **Climate entity**: Not implemented - use number/select entities with automations instead.
- **RW batch reading**: RW parameters read individually due to sparse address space (0x0036, 0x00C6-CC, 0x0169-019E).

## Contributing

Pull requests welcome!

## License

MIT License - see [LICENSE](LICENSE)

## Author

[@stasek44](https://github.com/stasek44)

## Acknowledgments

- SPRSUN heat pump Modbus reference documentation
- Elfin-EW11/W11 RS485 to WiFi gateway
- Home Assistant community

## Support

- **Issues**: [GitHub Issues](https://github.com/stasek44/sprsun-modbus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/stasek44/sprsun-modbus/discussions)

---
