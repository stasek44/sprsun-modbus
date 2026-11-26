# SPRSUN Heat Pump Modbus Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
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
| **Enable Derived / Calculated Sensors** | `boolean` | `False` | **Opt-in (Configure):** Adds `13` virtual calculated sensors (filtered ambient temp, operating state, ECO curve target & delta, cycle durations, defrost interval, coil-ambient delta, water delta T, condenser approach, superheats, experimental power estimate) |
| **Enable Expert Settings** | `boolean` | `False` | **Advanced / Risky (Opt-in):** Exposes CHICO engineering/factory parameters (`H`/`A`/`B`/`D`/`F`/`R`, Timebands, control bits) as both read-only **Diagnostic** sensors (`353`) and writable **Configuration** controls (`337`, `box` input mode). Keep disabled unless you understand each parameter |

> Settings such as **Scan Interval**, **Temperature Step**, **Enable Derived / Calculated Sensors**, and **Enable Expert Settings** can also be adjusted at any time via **Configure** on the integration card (changes trigger an automatic integration reload).

---

## Features & Entity Organization

- **Single Home Assistant Device (`SPRSUN Heat Pump`):** All controls, telemetry sensors, diagnostics, and optional expert configuration entities are grouped under one device.
- **Polling Architecture:**
  - **Polling Architecture:**
  - **Fast Telemetry (`0x0000–0x0031`):** 1 contiguous read every `scan_interval` (49 sensors + 49 binary status/alarm sensors), with automatic exponential backoff up to `300s` when the gateway/unit is offline and instant recovery on the first successful poll.
  - **RW & Expert Batches (`0x0032–0x01BB`):** Read at startup and refreshed every 20 poll cycles using batched reads that skip unmapped `Invalid` gaps.
- **Clean Default Device (`149` Core Entities):** Fresh setups expose only the `149` core entities (`49` sensors, `49` binary sensors, `42` numbers, `3` selects, `3` switches, `1` button, `2` climate entities). Integration diagnostics download (`diagnostics.py`) still captures all polled parameters regardless of UI entity toggles.
- **Opt-In Expert Settings (`enable_expert_writes`, default `False`):** When enabled in **Configure**, adds both the `353` read-only **Diagnostic** entities (`336` sensors + `17` binary sensors for `H`, `A`, `B`, `D`, `F`, `R`, Timebands, hidden by default in the registry to avoid duplicating writable controls) and `337` writable **Configuration** entities (`322` numeric parameters in `box` mode, `2` selects, `13` switches with read-modify-write masking). Previously existing `CORE` controls (`P01–P07`, `E01–E24`, `G01–G11`, Antilegionella, `Power Switch`, `Failure Reset`, `2x Climate`) remain enabled and untouched. Dangerous factory reset bits (`parameters_reset_flag`, `0x0033` bit 6) and unconfirmed registers stay read-only.
- **Opt-In Derived / Calculated Sensors (`enable_derived_sensors`, default `False`):** When enabled in **Configure**, adds `13` virtual calculated sensors (each carrying `description` and `formula` attributes in HA):
  - **Filtered Ambient Temperature (`ambient_temp_filtered`):** Freezes outdoor temperature during defrost and for up to 7 minutes afterward so coil heat spikes do not distort outdoor temperature readings.
  - **Operating State (`operating_state`):** Human-readable summary (`off`, `idle`, `heating`, `cooling`, `hot_water`, `heating_hot_water`, `cooling_hot_water`, `defrost`, `antilegionella`, `alarm`).
  - **ECO Curve Target & Delta (`eco_active_setpoint`, `eco_setpoint_delta`):** Interpolated target temperature from `E01–E24` using the filtered ambient temperature and active mode, plus live `outlet_temp - eco_active_setpoint` offset.
  - **Cycle Durations & Defrost Tracking (`compressor_last_run_duration`, `defrost_last_duration`, `defrost_last_interval`, `coil_ambient_delta`):** Live and last-completed cycle durations and defrost interval in minutes (tracked since HA startup), plus `ambient_temp_filtered - coil_temp` frost buildup tracking.
  - **Heat Exchanger & Refrigerant Diagnostics:** `water_delta_t` (`outlet - inlet`), `condenser_approach_temp` (`cond - outlet`), `suction_superheat` (`suction - evap`), and `discharge_superheat` (`exhaust - cond`).
  - **Estimated Electrical Power (`estimated_power`, Experimental):** Empirical 2-state approximation from compressor frequency, condensation-to-ambient temperature lift, and chassis heater state. Marked `experimental: true` with a disclaimer — calibrated on a 3-phase unit without backup immersion heaters and **not** a substitute for a dedicated power meter.
- **Pre-release Debug Logging:** Beta/test versions (`alpha`/`beta`/`rc`/`dev`) automatically default the integration logger level to `DEBUG` for diagnostics.

---

## Documentation

- 🎛️ **[Ready-to-Use Native HA Dashboards (EN)](docs/DASHBOARD.md)** / **[Polski przewodnik (PL)](docs/DASHBOARD_PL.md)**: 100% native Home Assistant 4-view Lovelace dashboards (`Default`, `Detailed`, `Diagnostics`, `Optimization` with energy & defrost tuning), compact control card, and optional 24h helper templates.
- 📖 **[CHICO Parameters & Settings Guide](docs/CHICO_PARAMETERS_GUIDE.md)**: Detailed explanations of all parameters (`P`, `E`, `G`, and `H`/`A`/`B`/`D`/`F`/`R`/Timeband expert series), weather curves, safety limits, and practical tips.
- 📚 **[CHICO Modbus Protocol Reference](docs/CHICO_MODBUS_REFERENCE.md)**: Complete `0x0000–0x01BB` register map with live hardware observations, data types, scales, batching layout, and bitfield definitions.
- 🧩 **[Multi-Controller Architecture Guide](docs/CONTROLLER_ARCHITECTURE.md)**: Package layout, `ControllerBase` driver interface, polling/batching model, masked writes, and safety architecture.

---

## Development & Testing

```bash
# Run unit tests locally
python3 -m unittest discover tests

# Or run with pytest and ruff
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
