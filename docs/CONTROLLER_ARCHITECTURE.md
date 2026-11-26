# Multi-Controller Architecture Guide

This integration isolates all heat pump protocol details behind `ControllerBase` so Home Assistant platforms and the Modbus coordinator remain controller-agnostic.

## Package Layout

```text
custom_components/sprsun_modbus/
├── __init__.py                     # SPRSUNDataUpdateCoordinator (FC 0x03/0x06/0x10/0x05 + masked RMW + auto-DEBUG)
├── config_flow.py                  # Auto-detection, options flow (enable_expert_writes), selector coercion
├── const.py                        # Integration defaults, is_expert_writes_enabled(), legacy aliases
├── diagnostics.py                  # Redacted coordinator cache, poll stats, and entity diagnostics export
├── sensor.py                       # Consumes ControllerBase.get_sensors() (core + read-only expert diagnostics)
├── binary_sensor.py                # Consumes ControllerBase.get_binary_sensors() (bitfields, alarms, control bits)
├── number.py                       # Consumes get_numbers() + opt-in get_expert_numbers() (NumberMode.BOX)
├── select.py                       # Consumes get_selects() + opt-in get_expert_selects()
├── switch.py                       # Consumes get_switches() + opt-in get_expert_switches()
├── button.py                       # Consumes ControllerBase.get_buttons() (bitfield, coil, or register pulse)
├── climate.py                      # Delegates HVAC/DHW capabilities, state, and writes to ControllerBase
├── strings.json & translations/    # En/Pl UI labels & expert write warnings
└── controllers/
    ├── __init__.py                 # CONTROLLER_REGISTRY, get_controller, detect_controller_type, helpers
    ├── base.py                     # ControllerBase abstract class, climate & opt-in expert interfaces
    ├── models.py                   # RegisterSpace, DataType, WordOrder, entity specs (`is_expert`), codecs
    ├── modbus_helpers.py           # Shared batch reader (FC 0x01/0x02/0x03/0x04) and spec decoder
    ├── chico_registers.py          # Declarative CHICO register map (core + 336 expert sensors + opt-in writes)
    └── chico.py                    # ChicoController driver & batched RW polling (`CHICO_RW_BATCHES`)
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

- **Single-Device Entity Categorization & Default Visibility:** All core controls, sensors, read-only expert diagnostics (`EntityCategory.DIAGNOSTIC`), and opt-in writable expert controls (`EntityCategory.CONFIG`) remain under the single `SPRSUN Heat Pump` device. All `353` RO expert entities (`336` sensors + `17` binary sensors) set `enabled_default=False` (`_attr_entity_registry_enabled_default = False`), hiding them by default in the Home Assistant entity registry while keeping all `149` core entities visible.
- **Opt-In Expert Write Gating (`enable_expert_writes`):**
  - `ControllerBase` defines `get_expert_numbers()`, `get_expert_selects()`, and `get_expert_switches()`, returning `()` by default so non-CHICO drivers need no boilerplate.
  - Confirmed CHICO expert promotion filters by `spec.writable` (independent of `spec.enabled_default`) so RO diagnostics stay hidden in HA by default while `enable_expert_writes=True` still promotes all `337` confirmed controls (`322` numbers, `2` selects, `13` switches).
  - `number.py`, `select.py`, and `switch.py` only register expert writable entities when `is_expert_writes_enabled(config_entry)` is `True` (default `False`).
  - Expert numeric entities enforce `NumberMode.BOX` (preventing accidental slider drags in the UI), while dangerous registers/bits (e.g. `parameters_reset_flag` at `0x0033` bit 6) and unconfirmed PDF `Invalid` gaps (`writable=False`) are kept non-writable.
- **Masked Read-Modify-Write & Offset Codecs:**
  - Registers sharing a word with adjacent fields or upper-byte flags — including primary setpoints `P01`/`P02`/`P04` (`0x00CA–0x00CC`) and Timeband temperature setpoints (`0x01A4–0x01AC`) using `bit_mask=0xFF` (`0x00FF`) — route through `async_write_masked_register()` -> `_sync_write_masked_register()`, reading the live 16-bit word, masking only target bits, writing back with `INTER_WRITE_DELAY`, and storing the scaled `cached_value`.
  - Signed (`INT16`) and offset-encoded (`raw_offset`, such as `F02`/`F03` with `+250` raw offset) single-register writes encode via `encode_registers()` and pass explicit `cached_value`.
- **Two-Tier Batched Polling & Failure Backoff (`ChicoController` / Coordinator):**
  - Fast RO telemetry (`0x0000–0x0031`) runs every `scan_interval`. Repeated poll failures apply exponential backoff up to `300s` (`max(300, scan_interval)`) and reset immediately to `scan_interval` upon recovery.
  - RW & expert registers run at startup and every 20 cycles (`_rw_refresh_interval = 20`) across `CHICO_RW_BATCHES` (`<= 62` registers/batch, skipping PDF `Invalid` gaps; `optional=True` skips undocumented gaps cleanly if a firmware variant rejects them).
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

### Note on Archived CAREL Reference (`24c99a3`)

Before enabling a CAREL driver in production, the following items from the archived `docs/CAREL_MODBUS_REFERENCE.md` (commit `24c99a3`) must be verified against a live CAREL heat pump or official OEM Modbus spec:

- **Power ON/OFF write address:** `10001` (`Unit On/OFF`) in the archived table is a read-only Discrete Input; the writable Coil or Holding Register for turning the unit ON/OFF (and error reset) was missing.
- **Scaling & word order:** Several `REAL` entries have `byte = 1` (likely scaled `INT16` / `UINT16`, but pressure/current/COP multipliers are missing), while others have `byte = 2` (32-bit `FLOAT32` or `UDINT`, requiring endianness verification).
- **Binary output polarity:** Discrete inputs `10006`–`10013` list `0:NO 1:OFF` in notes and must be checked for active-low (`inverted=True`) vs active-high behavior.
