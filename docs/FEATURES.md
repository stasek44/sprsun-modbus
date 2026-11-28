# Features & Entity Organization

This document describes the polling architecture, entity grouping, opt-in derived sensors, and expert settings available in the SPRSUN Heat Pump Modbus integration.

---

## Single Home Assistant Device (`SPRSUN Heat Pump`)

All controls, telemetry sensors, diagnostics, and optional expert configuration entities are grouped under a single Home Assistant device. Integration diagnostics download (**Device** → **Download diagnostics**) captures all polled parameters regardless of optional UI entity toggles.

---

## Two-Tier Polling & Backoff

- **Fast Telemetry (every `scan_interval`):**
  - **CHICO:** 1 contiguous read (`0x0000–0x0031`, 49 sensors + 49 binary status/alarm sensors).
  - **CAREL:** Fast RO batches (`DI 0..12`, `DI 178..183`, `Holding 188..217`, optional `Holding 333..335`, `Coil 40`, and aggregated alarms `DI 13..177`).
  - Automatic exponential backoff up to `300s` when the gateway or unit is offline, with instant recovery on the first successful poll.
- **RW & Expert Batches (startup + every 20 cycles):**
  - Batched reads skip unmapped `Invalid` gaps (`<= 62` registers per batch) and use `INTER_WRITE_DELAY` (`0.08s`) between writes for safe EEPROM commits.
- **Pre-release Debug Logging:**
  - Beta/pre-release builds (`alpha`/`beta`/`rc`/`dev`) automatically default the integration logger to `DEBUG` for easier troubleshooting.

---

## Clean Default Entity Set vs Opt-In Modes

### Default Setup (Clean UI)
- **CHICO:** `149` core entities (`49` sensors, `49` binary sensors, `42` numbers, `3` selects, `3` switches, `1` button, `2` climate entities).
- **CAREL:** Core telemetry, water/refrigerant sensors, BLDC inverter telemetry, relays/digital inputs, aggregated active alarms (`alarm_active` + `active_alarms`), primary setpoints & differentials, unit/pump/fan modes, power/auxiliary/schedule switches, `Reset Alarm` button (`Coil 41`), and `2` climate entities (`Heating/Cooling` + `DHW`).

### Opt-In Derived / Calculated Sensors (`enable_derived_sensors`, default `False`)

Enable in **Configure** to expose virtual calculated sensors (each includes `description` and `formula` attributes):

#### CHICO (`17` derived sensors)
- **Filtered Ambient Temperature (`ambient_temp_filtered`):** Freezes outdoor temperature during defrost and holds post-defrost for up to 7 minutes of outdoor fan runtime (capped at 45 minutes if idle) or until the air cools back down.
- **Operating State (`operating_state`):** Human-readable summary (`off`, `idle`, `heating`, `cooling`, `hot_water`, `heating_hot_water`, `cooling_hot_water`, `defrost`, `antilegionella`, `alarm`).
- **ECO Curve Target & Delta (`eco_active_setpoint`, `eco_setpoint_delta`):** Interpolated target temperature from `E01–E24` using the filtered ambient temperature and active mode, plus `outlet_temp - eco_active_setpoint`.
- **Cycle Durations, 24h Rolling Counters & Defrost Tracking (`compressor_last_run_duration`, `defrost_last_duration`, `defrost_last_interval`, `coil_ambient_delta`, `defrost_count_24h`, `defrost_time_24h`, `compressor_starts_24h`, `heaters_time_24h`):** Live and last-completed cycle durations (with `last_completed_minutes`), defrost interval, non-negative `max(0, ambient_temp_filtered - coil_temp)` frost buildup tracking (`0.0 °C` during defrost), and rolling 24h counters persisted across Home Assistant restarts.
- **Heat Exchanger & Refrigerant Diagnostics:** `water_delta_t` (`outlet - inlet`), `condenser_approach_temp` (`cond - outlet`), `suction_superheat` (`suction - evap`), and `discharge_superheat` (`exhaust - cond`).
- **Estimated Electrical Power (`estimated_power`, Experimental):** Empirical 2-state approximation from compressor frequency, condensation-to-ambient lift, and chassis heater state (`experimental: true`; not a substitute for a dedicated power meter).

#### CAREL (`4` derived sensors)
- **Water Delta T (`water_delta_t`):** `outlet_temp - inlet_temp`.
- **ECO Curve Targets (`eco_heating_setpoint`, `eco_cooling_setpoint`, `eco_hotwater_setpoint`):** Piecewise linear interpolation of the 4-point CAREL ECO weather curves (`X1–X4`, `Y1–Y4`) at current `ambient_temp`.

### Opt-In Expert Settings (`enable_expert_writes`, default `False`)

Enable in **Configure** only if you know what each factory parameter controls:
- **CHICO:** Adds `353` read-only **Diagnostic** entities (`336` sensors + `17` binary sensors for `H`, `A`, `B`, `D`, `F`, `R`, Timebands, disabled by default in registry) and `337` writable **Configuration** entities (`322` numbers in `box` mode, `2` selects, `13` switches with read-modify-write masking). `parameters_reset_flag` (`0x0033` bit 6) and unconfirmed registers remain permanently locked.
- **CAREL:** Adds PID tuning (`Kp`/`Ti`/`Td`), auxiliary delay, night-mode compressor/fan speed caps, 4-point ECO weather curves (`276–296`, `336–338`), defrost parameters (`77–91`), heater type (`323`), and `A/C Linkage NO` / `Defrost Enable` coils. Factory reset targets (`Coil 57`, `Holding 332`) remain permanently locked.
