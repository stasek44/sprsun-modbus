# Multi-Controller Architecture Guide

This integration isolates all heat pump protocol details behind `ControllerBase` so Home Assistant platforms and the Modbus coordinator remain controller-agnostic.

## Package Layout

```text
custom_components/sprsun_modbus/
├── __init__.py                     # SPRSUNDataUpdateCoordinator (FC 0x03/0x06/0x10/0x05 + reconnect/mutex)
├── config_flow.py                  # Auto-detection & controller-specific connection probing
├── const.py                        # Integration defaults + legacy CHICO tuple aliases
├── sensor.py                       # Consumes ControllerBase.get_sensors()
├── binary_sensor.py                # Consumes ControllerBase.get_binary_sensors() (bitfields & discrete/coil booleans)
├── number.py                       # Consumes ControllerBase.get_numbers() (16-bit & multi-register 32-bit writes)
├── select.py                       # Consumes ControllerBase.get_selects()
├── switch.py                       # Consumes ControllerBase.get_switches() (bitfield registers & Modbus coils)
├── button.py                       # Consumes ControllerBase.get_buttons() (bitfield, coil, or register pulse)
├── climate.py                      # Delegates HVAC/DHW capabilities, state, and writes to ControllerBase
└── controllers/
    ├── __init__.py                 # CONTROLLER_REGISTRY, get_controller, detect_controller_type, helpers
    ├── base.py                     # ControllerBase abstract class and climate interface
    ├── models.py                   # RegisterSpace, DataType, WordOrder, entity specs, binary codecs
    ├── modbus_helpers.py           # Shared batch reader (FC 0x01/0x02/0x03/0x04) and spec decoder
    ├── chico_registers.py          # Declarative CHICO register map
    └── chico.py                    # ChicoController driver
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
  - Shared `decode_registers()` and `encode_registers()` helpers handle scaling and clamping.

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
