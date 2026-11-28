# SPRSUN Heat Pump Modbus Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/release/stasek44/sprsun-modbus.svg)](https://github.com/stasek44/sprsun-modbus/releases)
[![License](https://img.shields.io/github/license/stasek44/sprsun-modbus.svg)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow.svg?logo=buy-me-a-coffee)](https://buymeacoffee.com/stasek44)

Local Home Assistant integration for SPRSUN heat pumps over Modbus TCP (via an RS485-to-WiFi/Ethernet gateway such as Elfin EW11). Provides real-time telemetry, full climate/DHW control, built-in native dashboards, and optional optimization diagnostics — with zero cloud dependency.

**Controller Compatibility:**
- **CHICO Controller:** Tested on my own **CGK-025V3L-B** unit (and compatible V3L-B touch-panel models).
- **CAREL Controller (Experimental / Beta):** Added for **CGK0x0V2** and **CGK025–060V3L** units (auto-detected or selectable during setup). I do not own a CAREL pump myself, so live feedback, logs, and diagnostic exports via GitHub Issues are greatly appreciated!

---

## Installation

### Via HACS (Recommended)
1. In Home Assistant, open **HACS** (or **Settings** → **Marketplace**).
2. Search for **SPRSUN Heat Pump (Modbus)**, click **Download**, and restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=stasek44&repository=sprsun-modbus&category=integration)

<details>
<summary>Alternative: Custom Repository in HACS (beta / pre-release) or Manual Install</summary>

1. **HACS Custom Repository:** Open HACS menu → **Custom repositories** → add `https://github.com/stasek44/sprsun-modbus` (**Integration**), download, and restart Home Assistant.
2. **Manual Installation:** Copy `custom_components/sprsun_modbus` into `<config>/custom_components/` and restart Home Assistant.

</details>

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

## Configuration

Go to **Settings** → **Devices & Services** → **Add Integration** → **SPRSUN Heat Pump (Modbus)**.

| Parameter | Default | Description |
| :--- | :---: | :--- |
| **Host / Port / Device Address** | `—` / `502` / `1` | Modbus TCP gateway IP, port, and slave ID |
| **Controller Type** | `Auto-detect` | Automatically detects `CHICO` first, then `CAREL` (or choose manually) |
| **Scan Interval** | `10s` | Fast telemetry polling interval (`10–30s` recommended) |
| **Temperature Step** | `1.0°C` | Target setpoint step (`1.0°C`, `0.5°C`, or `0.1°C` for CAREL) |
| **Enable Derived Sensors** | `False` | Opt-in virtual sensors (filtered ambient, Delta T, ECO targets, defrost/24h counters) |
| **Enable Expert Settings** | `False` | Opt-in factory/engineering parameters (`box` mode; dangerous reset bits locked) |

> Options can be changed anytime via **Configure** on the integration card (reloads automatically).

---

## Key Features

- **Full Local Control & Telemetry:** Heating/Cooling + DHW thermostats, setpoints, operating/fan/pump modes, temperatures, pressures, inverter telemetry, relays, and fault diagnostics under a single Home Assistant device.
- **Multi-Controller Support:** Dedicated drivers for **CHICO** and **CAREL** (Holding Registers, Discrete Inputs, Coils, safe mode-switching, masked bitfield writes, exponential reconnect backoff).
- **Built-in Native Dashboards:** Zero-YAML Lovelace strategies (`custom:sprsun` and `custom:sprsun-control`) with automatic entity mapping and 10-language UI support (`EN`/`PL`/`FR`/`DE`/`ES`/`CS`/`SK`/`HU`/`LT`/`UK`) for both CHICO and CAREL.
- **Opt-In Diagnostics & Tuning:** Optional derived/calculated sensors (24h persistent counters, ECO curve tracking, frost/defrost analysis) and opt-in expert parameters with safety locks.

👉 See **[Features & Entity Organization](docs/FEATURES.md)** for full entity counts, polling tiers, derived sensor formulas, and expert settings details.

---

## Documentation

| Guide | Description |
| :--- | :--- |
| **[Features & Entity Organization](docs/FEATURES.md)** | Polling tiers, default vs opt-in entities, derived sensors, and expert settings |
| **[Built-in Native HA Dashboards](docs/DASHBOARD.md)** | Setup guide for built-in Lovelace dashboards and quick-control section (10 languages) |
| **[CHICO Parameters Guide](docs/CHICO_PARAMETERS_GUIDE.md)** | Explanations of CHICO `P`, `E`, `G`, and expert `H`/`A`/`B`/`D`/`F`/`R` parameters |
| **[CHICO Modbus Reference](docs/CHICO_MODBUS_REFERENCE.md)** | Complete `0x0000–0x01BB` register map, data types, scales, and bitfields |
| **[CAREL Modbus Reference](docs/CAREL_MODBUS_REFERENCE.md)** | OEM-verified CAREL registers, discrete inputs, coils, alarms, and safety locks |
| **[Multi-Controller Architecture](docs/CONTROLLER_ARCHITECTURE.md)** | Developer guide: `ControllerBase` driver interface, batching, and safety invariants |

---

## Development & Testing

```bash
pytest tests/ -v
ruff check custom_components/
```

---

## Support

If this integration helped you or saved you time, you can buy me a coffee:

<a href="https://buymeacoffee.com/stasek44" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="42"></a>

---

## License

MIT License — see [LICENSE](LICENSE).
