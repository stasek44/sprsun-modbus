# SPRSUN Heat Pump Modbus Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Default-blue.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/stasek44/sprsun-modbus.svg)](https://github.com/stasek44/sprsun-modbus/releases)
[![License](https://img.shields.io/github/license/stasek44/sprsun-modbus.svg)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow.svg?logo=buy-me-a-coffee)](https://buymeacoffee.com/stasek44)

Home Assistant integration for SPRSUN heat pumps via Modbus TCP (using an RS485-to-WiFi/Ethernet bridge such as Elfin EW11). The integration allows reading parameters in real-time and fully managing heat pump operations.

> ⚠️ **Controller Compatibility:**
> - Currently tested on model **CGK-025V3L-B** with the **CHICO** controller.
> - **Carel Controllers:** Support for Carel controllers can be added if anyone is willing to test and provide Modbus registers/logs.

---

## Hardware Setup

### Wiring (Heat Pump to Gateway)

| Heat Pump Terminal | Gateway Terminal | Description |
| :--- | :--- | :--- |
| **A / +** | **A** | RS485 Data + |
| **B / -** | **B** | RS485 Data - |
| **GND** | **GND** | Signal ground (*strongly recommended for signal integrity*) |

### Recommended Gateway Settings (e.g. Elfin EW11 / W11)

| Category | Parameter | Recommended Value | Notes |
| :--- | :--- | :--- | :--- |
| **Network / Socket** | Protocol | `TCP Server` | Standard Modbus TCP server mode |
| | Port | `502` | Default Modbus TCP port |
| | Timeout | `5s` – `10s` | Quickly clears stale sockets; avoid 60s+ |
| | Max Accept | `1` | **Critical:** prevents socket contention & bus frame interleaving |
| | Buffer Size | `512` | Sufficient for full register batch frames |
| | Keep Alive | `60s` | Keeps socket connection alive |
| **Serial (RS485)** | Baud Rate | `19200` | Standard SPRSUN baud rate |
| | Data Bits | `8` | |
| | Stop Bits | `2` (or `1`) | Depends on specific pump unit firmware |
| | Parity | `None` | |
| | Flow Control | `Half Duplex` | |
| | Gap Time | `20ms` – `50ms` | Minimum inter-frame delay |
| | CLI Settings | `Disable` | **Critical:** prevents binary data from triggering CLI command mode |
| | Protocol | `Modbus` | Automatic Modbus RTU ↔ Modbus TCP framing |

---

## Installation

### One-Click Install (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=stasek44&repository=sprsun-modbus&category=integration)

### Via HACS / Marketplace
1. In Home Assistant, open **Settings** → **Marketplace** (or **HACS** in older installations) → Menu (top right) → **Custom repositories**.
2. Add repository URL: `https://github.com/stasek44/sprsun-modbus` with category **Integration**.
3. Search for **SPRSUN Heat Pump Modbus**, click **Download**, and restart Home Assistant.

### Manual Installation
Copy `custom_components/sprsun_modbus` into your Home Assistant directory under `<config>/custom_components/` and restart Home Assistant.

---

## Configuration

In Home Assistant, go to **Settings** → **Devices & Services** → **Add Integration** and search for **SPRSUN Heat Pump (Modbus)**.

### Connection & Options Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **Host** | `string` | *Required* | IP address or hostname of the Modbus bridge (e.g. `192.168.1.200`) |
| **Port** | `integer` | `502` | Modbus TCP port |
| **Device Address** | `integer` | `1` | Modbus slave ID |
| **Scan Interval** | `integer` | `10` | Polling interval in seconds (recommended: `10`–`30`) |
| **Temperature Step** | `float` | `1.0` | Step size for target temperatures (`1.0°C` or `0.5°C`). `1.0°C` is default and recommended; `0.5°C` can be set if supported by your firmware |

> Settings such as **Scan Interval** and **Temperature Step** can also be adjusted at any time via **Configure** on the integration card.

---

## Documentation

- 📖 **[CHICO Parameters & Settings Guide](docs/CHICO_PARAMETERS_GUIDE.md)**: Detailed explanations of all parameters (P, E, G series), weather curves, safety limits, and practical tips.
- 📚 **[CHICO Modbus Protocol Reference](docs/CHICO_MODBUS_REFERENCE.md)**: Complete register map, data types, scales, and bitfield definitions.

---

## Development & Testing

```bash
# Run unit tests locally
python3 -m unittest discover tests

# Or run with pytest and coverage
pytest tests/ -v
```

See **[AGENTS.md](AGENTS.md)** for architecture principles and contribution guidelines.

---

## Support

If this integration helped you or saved you time, you can buy me a coffee:

<a href="https://buymeacoffee.com/stasek44" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="42"></a>

---

## License

MIT License — see [LICENSE](LICENSE).
