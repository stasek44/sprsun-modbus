# SPRSUN Heat Pump Modbus Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/release/stasek44/sprsun-modbus.svg)](https://github.com/stasek44/sprsun-modbus/releases)
[![License](https://img.shields.io/github/license/stasek44/sprsun-modbus.svg)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-yellow.svg?logo=buy-me-a-coffee)](https://buymeacoffee.com/stasek44)

Local Home Assistant integration for SPRSUN heat pumps over Modbus TCP using an RS485-to-WiFi/Ethernet gateway such as Elfin EW11.

**Controller Compatibility:**
- **CHICO Controller:** Tested on **CGK-025V3L-B** and compatible V3L-B touch-panel models.
- **CAREL Controller:** Beta support for **CGK0x0V2** and **CGK025–060V3L** units, auto-detected or selectable during setup. I do not own a CAREL pump myself, so live feedback, logs, and diagnostic exports via GitHub Issues are welcome!

---

## Installation

### Via HACS
1. Open **HACS** in Home Assistant.
2. Search for **SPRSUN Heat Pump Modbus**, click **Download**, and restart Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=stasek44&repository=sprsun-modbus&category=integration)

<details>
<summary>Alternative: Custom Repository in HACS or Manual Install</summary>

1. **HACS Custom Repository:** Open HACS menu → **Custom repositories** → add `https://github.com/stasek44/sprsun-modbus` as **Integration**, download, and restart Home Assistant.
2. **Manual Installation:** Copy `custom_components/sprsun_modbus` into `<config>/custom_components/` and restart Home Assistant.

</details>

---

## Hardware Setup

See **[Hardware & Gateway Setup](docs/HARDWARE_SETUP.md)** for RS485 wiring and recommended Elfin EW11 / W11 settings.

---

## Configuration

Go to **Settings** → **Devices & Services** → **Add Integration** → **SPRSUN Heat Pump**.

| Parameter | Default | Description |
| :--- | :---: | :--- |
| **Host / Port / Device Address** | `—` / `502` / `1` | Modbus TCP gateway IP, port, and slave ID |
| **Controller Type** | `Auto-detect` | Detects `CHICO` first, then `CAREL`, or choose manually |
| **Scan Interval** | `10s` | Fast telemetry polling interval; `10–30s` recommended |
| **Temperature Step** | `1.0°C` | Target setpoint step: `1.0°C`, `0.5°C`, or `0.1°C` for CAREL |
| **Enable Derived Sensors** | `False` | Optional calculated sensors: filtered ambient, Delta T, ECO targets, defrost & 24h counters |
| **Enable Expert Settings** | `False` | Optional factory parameters in `box` mode; factory reset registers remain locked |

> Options can be changed anytime via **Configure** on the integration card.

---

## Key Features

- Full local Modbus TCP control & telemetry
- Heating/Cooling & DHW thermostats, modes, and setpoints
- CHICO & CAREL controller support
- Built-in native Lovelace dashboards in 10 languages
- Optional derived sensors, 24h counters, and defrost diagnostics
- Optional expert parameters with safety locks

👉 See **[Features & Entity Organization](docs/FEATURES.md)** for details.

---

## Support

If this integration helped you or saved you time, you can buy me a coffee:

<a href="https://buymeacoffee.com/stasek44" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="42"></a>

---

## Documentation

| Guide | Description |
| :--- | :--- |
| **[Hardware & Gateway Setup](docs/HARDWARE_SETUP.md)** | RS485 wiring and Elfin EW11 / W11 gateway configuration |
| **[Features & Entity Organization](docs/FEATURES.md)** | Polling tiers, default vs optional entities, derived sensors, and expert settings |
| **[Built-in Native HA Dashboards](docs/DASHBOARD.md)** | Built-in Lovelace dashboards and quick-control section in 10 languages |
| **[CHICO Parameters Guide](docs/CHICO_PARAMETERS_GUIDE.md)** | CHICO `P`, `E`, `G`, and expert `H`/`A`/`B`/`D`/`F`/`R` parameters |
| **[CHICO Modbus Reference](docs/CHICO_MODBUS_REFERENCE.md)** | Complete `0x0000–0x01BB` register map, data types, scales, and bitfields |
| **[CAREL Modbus Reference](docs/CAREL_MODBUS_REFERENCE.md)** | CAREL registers, discrete inputs, coils, alarms, and safety locks |
| **[Multi-Controller Architecture](docs/CONTROLLER_ARCHITECTURE.md)** | Developer guide: `ControllerBase` driver interface, batching, and safety invariants |

---

## Development & Testing

```bash
pytest tests/ -v
ruff check custom_components/
```

---

## License

MIT License — see [LICENSE](LICENSE).
