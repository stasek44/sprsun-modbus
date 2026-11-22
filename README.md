<div align="center">
  <img src="https://raw.githubusercontent.com/stasek44/sprsun-modbus/main/images/banner.png" alt="SPRSUN Heat Pump Modbus Integration" width="100%">
</div>

# SPRSUN Heat Pump Modbus Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/stasek44/sprsun-modbus.svg)](https://github.com/stasek44/sprsun-modbus/releases)
[![License](https://img.shields.io/github/license/stasek44/sprsun-modbus.svg)](LICENSE)

Home Assistant integration for SPRSUN heat pumps via Modbus TCP (e.g. using an Elfin-EW11 / W11 RS485-to-WiFi/Ethernet gateway).

> ⚠️ **Controller Compatibility:** Tested on model **CGK-025V3L-B** with the **CHICO** controller. This integration exclusively supports SPRSUN heat pumps equipped with **CHICO** controllers.

---

## Features

- **Climate Platform**: Standard HVAC controls for target temperature, modes (Heating, Cooling, DHW), and presets.
- **100+ Diagnostic & Control Entities**:
  - **Sensors**: Flow & return temperatures, DHW cylinder, outdoor ambient, refrigerant pressures, COP, thermal capacity, voltage, current, and compressor frequency.
  - **Binary Sensors**: Operational flags, compressor/fan/pump relays, 3-way/4-way valves, defrost status, and error indicators.
  - **Numbers & Selects**: Heating/cooling/DHW setpoints, hysteresis differentials, weather compensation curve points, fan modes, and circulation pump modes.
  - **Switches & Buttons**: Master power switch, antilegionella switch, two/three-function mode, and single-click alarm reset.
- **Fast Batch Reading**: Reads all 50 monitoring registers in a single Modbus TCP request (~200ms) with persistent connection handling.
- **Safe Writes**: Turnaround delay between writes to allow the heat pump MCU EEPROM commit time, protecting against bus collisions.

---

## Hardware Setup

### Wiring (Heat Pump to Gateway)
Connect the heat pump RS485 terminals to your Modbus bridge (e.g., Elfin EW11):
- **A/+** (Heat pump) → **A** (Gateway)
- **B/-** (Heat pump) → **B** (Gateway)
- **GND** (Heat pump) → **GND** (Gateway, strongly recommended for signal integrity)

### Recommended Gateway Settings (Elfin EW11)
- **Protocol:** TCP Server
- **Port:** `502`
- **Baud Rate:** `19200`
- **Data Bits:** `8`
- **Stop Bits:** `2`
- **Parity:** `None`
- **Timeout:** `30s` (must be greater than scan interval + cycle time)
- **Max Accept:** `1` (prevents socket contention)

---

## Installation

### Via HACS (Recommended)
1. Open **HACS** → **Integrations** → Three dots menu (top right) → **Custom repositories**.
2. Add URL: `https://github.com/stasek44/sprsun-modbus` with category **Integration**.
3. Search for **SPRSUN Modbus**, click **Download**, and restart Home Assistant.

### Manual Installation
Copy the directory `custom_components/sprsun_modbus` into your Home Assistant `<config>/custom_components/` directory and restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **SPRSUN Heat Pump (Modbus)**.
3. Configure the connection parameters:
   - **Host:** IP address of your Modbus bridge (e.g. `192.168.1.200`)
   - **Port:** `502`
   - **Device Address:** Modbus slave address (typically `1`)
   - **Scan Interval:** `10`–`30` seconds
4. Save. Entities will be discovered and created automatically.

Options can be updated at any time under **Configure** on the integration card.

---

## Documentation

- 📖 **[CHICO Parameters & Settings Guide](docs/CHICO_PARAMETERS_GUIDE.md)**: Detailed explanations of all parameters (P, E, G series), curves, safety limits, and practical tips.
- 📚 **[CHICO Modbus Protocol Reference](docs/CHICO_MODBUS_REFERENCE.md)**: Complete register map, data types, scales, and bitfield definitions.
- ❄️ **[Climate Entity Options](docs/CLIMATE_ENTITY_OPTIONS.md)**: Architecture notes regarding HVAC climate entity mappings.

---

## Development & Testing

Run unit tests locally (no external hardware or Home Assistant instance required):

```bash
# Run test suite
python3 -m unittest discover tests

# Or run with pytest and coverage
pytest tests/ -v --cov=custom_components/sprsun_modbus
```

Automated CI workflows (`.github/workflows/`) run test matrices and code validation on every pull request.

---

## Contributing & Agent Guidelines

See **[AGENTS.md](AGENTS.md)** for development guidelines and required steps after every change:
1. Update tests.
2. Run tests to ensure 100% pass rate.
3. Keep documentation updated.
4. Maintain English as the primary language (Polish only in `translations/pl.json`).

---

## License

MIT License — see [LICENSE](LICENSE).
