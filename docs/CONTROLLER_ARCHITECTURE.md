# Multi-Controller Architecture Guide

This integration isolates all heat pump protocol details behind `ControllerBase` so Home Assistant platforms and the Modbus coordinator remain controller-agnostic.

## Package Layout

```text
custom_components/sprsun_modbus/
├── __init__.py                     # SPRSUNDataUpdateCoordinator (FC 0x03/0x06/0x10/0x05 + masked RMW + auto-DEBUG)
├── config_flow.py                  # Auto-detection, options flow (enable_expert_writes), selector coercion
├── const.py                        # Integration defaults, is_expert_writes_enabled(), legacy aliases
├── dashboard.py                    # Built-in Lovelace strategy registration, static serving & WS entity context API
├── diagnostics.py                  # Redacted coordinator cache, poll stats, and entity diagnostics export
├── frontend/                       # Single-source Lovelace strategy JS, per-controller JSON templates & i18n/{en,pl}.json
├── sensor.py                       # Consumes get_sensors() + opt-in get_derived_sensors() (SPRSUNDerivedSensor)
├── binary_sensor.py                # Consumes ControllerBase.get_binary_sensors() (bitfields, alarms, control bits)
├── number.py                       # Consumes get_numbers() + opt-in get_expert_numbers() (NumberMode.BOX)
├── select.py                       # Consumes get_selects() + opt-in get_expert_selects()
├── switch.py                       # Consumes get_switches() + opt-in get_expert_switches()
├── button.py                       # Consumes ControllerBase.get_buttons() (bitfield, coil, or register pulse)
├── climate.py                      # Delegates HVAC/DHW capabilities, state, and writes to ControllerBase
├── strings.json & translations/    # En/Pl UI labels & expert write warnings
└── controllers/
    ├── __init__.py                 # CONTROLLER_REGISTRY, get_controller, detect_controller_type, helpers
    ├── base.py                     # ControllerBase abstract class, climate, derived & opt-in expert interfaces
    ├── models.py                   # RegisterSpace, DataType, WordOrder, entity specs (`DerivedSensorSpec`, `is_expert`), codecs
    ├── modbus_helpers.py           # Shared batch reader (FC 0x01/0x02/0x03/0x04) and spec decoder
    ├── chico_derived.py            # CHICO derived sensor specs & ChicoDerivedTracker (defrost filter, durations)
    ├── chico_registers.py          # Declarative CHICO register map (core + 336 expert sensors + opt-in writes)
    ├── chico.py                    # ChicoController driver & batched RW polling (`CHICO_RW_BATCHES`)
    ├── carel_registers.py          # Declarative CAREL register/DI/coil/alarm map (core + opt-in expert)
    └── carel.py                    # CarelController driver, Coil 40 mode-switch safety & ECO derived sensors
```

## Supported Modbus Spaces & Types

- **Address Spaces (`RegisterSpace`):**
  - `HOLDING_REGISTER` (`4xxxx`, FC `0x03` read / `0x06` & `0x10` write)
  - `INPUT_REGISTER` (`3xxxx`, FC `0x04` read)
  - `DISCRETE_INPUT` (`1xxxx`, FC `0x02` read)
  - `COIL` (`0xxxx`, FC `0x01` read / `0x05` write)
- **Data Types (`DataType`) & Word Ordering (`WordOrder`):**
  - `INT16`, `UINT16`, `INT32`, `UINT32`, `FLOAT32`, `BOOL`
  - `WordOrder.BIG_ENDIAN` (`AB CD`) and `WordOrder.LITTLE_ENDIAN` (`CD AB`)
  - Shared `decode_registers()` and `encode_registers()` helpers handle scaling, `raw_offset`, `bit_mask`, and clamping.

## Expert Settings, Polling & Safety Architecture

- **Single-Device Entity Categorization & Opt-In Gating:** Core controls and telemetry (`149` entities) remain under the single `SPRSUN Heat Pump` device and are always registered. Expert settings (`enable_expert_writes`, default `False`) and derived sensors (`enable_derived_sensors`, default `False`) are gated cleanly in **Configure**:
  - `ControllerBase` defines `get_expert_sensors()`, `get_expert_binary_sensors()`, `get_expert_numbers()`, `get_expert_selects()`, `get_expert_switches()`, and `get_derived_sensors()`, returning `()` by default so non-CHICO drivers need no boilerplate.
  - When `enable_expert_writes=False` (default), `sensor.py`, `binary_sensor.py`, `number.py`, `select.py`, and `switch.py` register only the `149` core entities — zero expert RO or RW entities clutter the entity registry.
  - When `enable_expert_writes=True`, `sensor.py` and `binary_sensor.py` add the `353` RO expert diagnostics (`336` sensors + `17` binary sensors, keeping `enabled_default=False` to avoid duplicating writable controls), while `number.py`, `select.py`, and `switch.py` add the `337` confirmed writable `Config` controls (`322` numbers in `NumberMode.BOX`, `2` selects, `13` switches). Dangerous registers/bits (e.g. `parameters_reset_flag` at `0x0033` bit 6) and unconfirmed PDF `Invalid` gaps (`writable=False`) remain non-writable.
  - When `enable_derived_sensors=True`, `sensor.py` registers the `17` controller-calculated `SPRSUNDerivedSensor` entities (enabled by default once opted in), with rolling 24h interval state persisted across restarts via `Store`.
- **Masked Read-Modify-Write & Offset Codecs:**
  - Registers sharing a word with adjacent fields or upper-byte flags — including primary setpoints `P01`/`P02`/`P04` (`0x00CA–0x00CC`) and Timeband temperature setpoints (`0x01A4–0x01AC`) using `bit_mask=0xFF` (`0x00FF`) — route through `async_write_masked_register()` -> `_sync_write_masked_register()`, reading the live 16-bit word, masking only target bits, writing back with `INTER_WRITE_DELAY`, and storing the scaled `cached_value`.
  - Signed (`INT16`) and offset-encoded (`raw_offset`, such as `F02`/`F03` with `+250` raw offset) single-register writes encode via `encode_registers()` and pass explicit `cached_value`.
- **Two-Tier Batched Polling & Failure Backoff (`ChicoController` / Coordinator):**
  - Fast RO telemetry (`0x0000–0x0031`) runs every `scan_interval`. Repeated poll failures apply exponential backoff up to `300s` (`max(300, scan_interval)`) and reset immediately to `scan_interval` upon recovery.
  - RW & expert registers run at startup and every 20 cycles (`_rw_refresh_interval = 20`) across `CHICO_RW_BATCHES` (`<= 62` registers/batch, skipping PDF `Invalid` gaps; `optional=True` skips undocumented gaps cleanly if a firmware variant rejects them). `ChicoController.has_rw_data()` verifies `_control_0032`, `unit_mode`, and `heating_setpoint` are all present so a failed first RW batch triggers an automatic retry on the next poll.
- **Pre-Write Live Register Reads (`0x0036` / `unit_mode`):**
  - Climate mode and space temperature writes (`async_set_space_hvac_mode`, `async_set_space_temperature`, `async_set_dhw_hvac_mode`) read `0x0036` directly via `coordinator.async_read_register()` right before writing, raising `HomeAssistantError` if the register cannot be read rather than falling back to a default mode.
- **Climate Preset & HVAC Separation (`ChicoController`):**
  - `HVACMode.HEAT_COOL` exclusively controls `G09` ambient changeover (`0x0191`, `mode_control_enable`), while `preset_mode` (`none`/`eco`/`sleep`) maps bijectively to `P07` (`0x0190` `fan_mode`: `Normal`/`Economic`/`Night`).
- **Pre-release Logging & Selector Normalization:**
  - `_configure_prerelease_logging()` checks `manifest.json` asynchronously and sets package logger level to `DEBUG` automatically on pre-release builds (`alpha`/`beta`/`rc`/`dev`).
  - `_normalize_flow_input()` in `config_flow.py` and `int(...)` coercions in `SPRSUNDataUpdateCoordinator.__init__` ensure `NumberSelector` floats (`1.0`, `10.0`) never reach `pymodbus` as non-integers.

## Adding a New Controller Driver (e.g. CAREL)

1. Create a register map and driver class subclassing `ControllerBase` in `custom_components/sprsun_modbus/controllers/` (for example `carel_registers.py` and `carel.py`).
2. Implement `detect()`, `probe_connection()`, `read_all_registers()`, `write_register()`, `get_platforms()`, and `get_device_info()`.
   - Use `read_modbus_batch()` and `decode_batch_into_data()` from `modbus_helpers.py` for Holding Registers, Discrete Inputs, and Coils.
   - Note: `read_discrete_inputs` and `read_coils` in `pymodbus` return byte-padded bit lists; `read_modbus_batch()` automatically slices `bits[:count]`.
3. Return declarative specs from `get_sensors()`, `get_binary_sensors()`, `get_numbers()`, `get_selects()`, `get_switches()`, and `get_buttons()`.
4. If the controller exposes thermostat control, override `get_space_climate_capabilities()` and the `get_space_*` / `async_set_space_*` / `get_dhw_*` / `async_set_dhw_*` methods.
   - Return `ClimateCapabilities(enabled=False, supports_dhw=False)` if climate entities are not supported yet.
5. Register the driver in `CONTROLLER_REGISTRY` in `controllers/__init__.py` (keep `chico` first or ensure `detect()` checks non-zero/unique signature registers so `[0, 0, 0]` cannot false-match).
6. Add unit tests in `tests/` covering register decoding, batch reads, climate mapping, and detection.
7. Optionally add a controller-specific dashboard template `frontend/sprsun_dashboard_<controller>.json` (plus any new keys in `frontend/i18n/{en,pl}.json`). Until a dedicated template exists, the built-in Lovelace strategy automatically renders a clean fallback view of the controller's resolved entities.

### CAREL Controller Driver (`CarelController`)

Implemented in `controllers/carel.py` and `controllers/carel_registers.py` (registered in `CONTROLLER_REGISTRY` after `"chico"`). See [CAREL_MODBUS_REFERENCE.md](CAREL_MODBUS_REFERENCE.md) for the complete OEM-verified register map:

- **Detection & Manual Selection:** `CarelController.detect()` checks `Holding 0..3` (mode `0..4` + at least one realistic setpoint `50..700` to reject all-zero frames), `Holding 215..217` (valid run mode & status `0..10`), and `Discrete Input 0` (FC `0x02`). Users can also explicitly pick `chico` or `carel` in the Config Flow.
- **Power & Mode Switching Safety:** Power ON/OFF uses `Coil 40` (`async_read_coil()` / `async_write_coil()`). Mode changes on `Holding 0` (via either `climate` or `select` through `ControllerBase.async_write_select()`) perform the safe CAREL sequence `Coil 40 = False` → `Holding 0` → `Coil 40 = True` when the unit is running.
- **Alarms & Safety Locks:** `DI 13..177` (165 bits) is read in a single FC `0x02` batch and aggregated into `alarm_active` (`binary_sensor`) + `active_alarms` (`sensor` with `alarms` list attribute). `Coil 41` (`00042`) is exposed as a diagnostic `reset_alarm` button. Factory reset registers (`Coil 57`, `Holding 332`) are permanently locked in `tests/test_protocol_invariants.py`.
