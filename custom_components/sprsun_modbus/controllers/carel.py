"""CAREL controller implementation (SPRSUN CGK0x0V2 / CGK025-060V3L)."""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
import logging
from typing import TYPE_CHECKING, Any

from .base import ControllerBase
from .carel_registers import (
    CAREL_ALARM_BATCH,
    CAREL_ALARM_MAP,
    CAREL_ALARM_START_DI,
    CAREL_BUTTONS,
    CAREL_CORE_BINARY_SENSORS,
    CAREL_CORE_SENSORS,
    CAREL_EXPERT_NUMBERS,
    CAREL_EXPERT_SELECTS,
    CAREL_EXPERT_SWITCHES,
    CAREL_NUMBERS,
    CAREL_OPTIONAL_RO_BATCHES,
    CAREL_OPTIONAL_RW_BATCHES,
    CAREL_RO_BATCHES,
    CAREL_RW_BATCHES,
    CAREL_SELECTS,
    CAREL_SWITCHES,
)
from .modbus_helpers import (
    ModbusBatchError,
    ModbusDesyncError,
    decode_batch_into_data,
    read_modbus_batch,
)
from .models import (
    BinarySensorSpec,
    ButtonSpec,
    ClimateCapabilities,
    DataType,
    DerivedSensorSpec,
    ModbusBatchSpec,
    NumberSpec,
    SelectSpec,
    SensorSpec,
    SwitchSpec,
    encode_registers,
    extract_cache_value,
)

if TYPE_CHECKING:
    from homeassistant.components.climate import HVACAction, HVACMode
    from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)

_CAREL_ALL_READ_SPECS = (
    CAREL_CORE_SENSORS
    + CAREL_CORE_BINARY_SENSORS
    + CAREL_NUMBERS
    + CAREL_SELECTS
    + CAREL_SWITCHES
    + CAREL_EXPERT_NUMBERS
    + CAREL_EXPERT_SELECTS
    + CAREL_EXPERT_SWITCHES
)

_CAREL_VALID_UNIT_MODES = frozenset({0, 1, 2, 3, 4})
_CAREL_VALID_STATUSES = frozenset(range(0, 11))
_CAREL_VALID_RUN_MODES = frozenset({0, 1, 2})

_CAREL_FAN_MODE_TO_RAW: dict[str, int] = {
    "daytime": 0,
    "night": 1,
    "eco": 2,
    "pressure": 3,
}
_CAREL_RAW_TO_FAN_MODE: dict[int, str] = {v: k for k, v in _CAREL_FAN_MODE_TO_RAW.items()}


def _as_float(data: Mapping[str, Any] | None, key: str) -> float | None:
    """Safely extract float from coordinator data."""
    raw = extract_cache_value(data, key)
    if raw is None or isinstance(raw, bool):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _compute_water_delta_t(data: Mapping[str, Any] | None) -> float | None:
    """Compute outlet - inlet water temperature delta."""
    inlet = _as_float(data, "inlet_temp")
    outlet = _as_float(data, "outlet_temp")
    if inlet is None or outlet is None:
        return None
    return round(outlet - inlet, 1)


def _interpolate_eco_curve(
    data: Mapping[str, Any] | None,
    prefix: str,
) -> float | None:
    """Linearly interpolate a 4-point CAREL ECO curve (X1..X4, Y1..Y4) at ambient_temp."""
    ambient = _as_float(data, "ambient_temp")
    if ambient is None:
        return None

    points: list[tuple[float, float]] = []
    for idx in range(1, 5):
        x_val = _as_float(data, f"{prefix}_x{idx}")
        y_val = _as_float(data, f"{prefix}_y{idx}")
        if x_val is None or y_val is None:
            return None
        points.append((x_val, y_val))

    points.sort(key=lambda pt: pt[0])

    if ambient <= points[0][0]:
        return round(points[0][1], 1)
    if ambient >= points[-1][0]:
        return round(points[-1][1], 1)

    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if ambient <= x1:
            if x1 == x0:
                return round(y1, 1)
            ratio = (ambient - x0) / (x1 - x0)
            return round(y0 + ratio * (y1 - y0), 1)

    return round(points[-1][1], 1)


CAREL_DERIVED_SENSORS: tuple[DerivedSensorSpec, ...] = (
    DerivedSensorSpec(
        key="water_delta_t",
        name="Water Delta T",
        value_fn=_compute_water_delta_t,
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        suggested_display_precision=1,
        description="Temperature difference between outlet and inlet water.",
        formula="outlet_temp - inlet_temp",
    ),
    DerivedSensorSpec(
        key="eco_heating_setpoint",
        name="ECO Heating Target Setpoint",
        value_fn=lambda data: _interpolate_eco_curve(data, "eco_heat"),
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        suggested_display_precision=1,
        description="Interpolated heating target from the 4-point CAREL ECO weather curve.",
        formula="piecewise_linear(ambient_temp, eco_heat_x1..x4, eco_heat_y1..y4)",
    ),
    DerivedSensorSpec(
        key="eco_cooling_setpoint",
        name="ECO Cooling Target Setpoint",
        value_fn=lambda data: _interpolate_eco_curve(data, "eco_cool"),
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        suggested_display_precision=1,
        description="Interpolated cooling target from the 4-point CAREL ECO weather curve.",
        formula="piecewise_linear(ambient_temp, eco_cool_x1..x4, eco_cool_y1..y4)",
    ),
    DerivedSensorSpec(
        key="eco_hotwater_setpoint",
        name="ECO Hot Water Target Setpoint",
        value_fn=lambda data: _interpolate_eco_curve(data, "eco_hw"),
        unit="°C",
        device_class="temperature",
        state_class="measurement",
        suggested_display_precision=1,
        description="Interpolated hot water target from the 4-point CAREL ECO weather curve.",
        formula="piecewise_linear(ambient_temp, eco_hw_x1..x4, eco_hw_y1..y4)",
    ),
)


def _decode_alarm_bits(bits: list[bool]) -> tuple[bool, str, list[str]]:
    """Decode DI 13..177 alarm bit vector into (alarm_active, summary_text, active_list)."""
    active: list[str] = []
    for offset, is_active in enumerate(bits):
        if not is_active:
            continue
        di_addr = CAREL_ALARM_START_DI + offset
        code_info = CAREL_ALARM_MAP.get(di_addr)
        if code_info is not None:
            code, label = code_info
            active.append(f"{code}: {label}")
        else:
            active.append(f"DI{di_addr}: Unknown alarm")

    if not active:
        return False, "None", []

    summary = active[0] if len(active) == 1 else f"{active[0]} (+{len(active) - 1} more)"
    # Keep state under Home Assistant's 255-character limit
    return True, summary[:255], active


class CarelController(ControllerBase):
    """CAREL controller driver for SPRSUN DC Inverter heat pumps (CGK0x0V2 / CGK025-060V3L)."""

    @property
    def name(self) -> str:
        """Return controller type name."""
        return "CAREL"

    @property
    def manufacturer(self) -> str:
        """Return controller manufacturer."""
        return "SPRSUN (CAREL Controller)"

    def get_platforms(self) -> list[str]:
        """Return list of supported Home Assistant platforms."""
        return ["sensor", "binary_sensor", "number", "select", "switch", "button", "climate"]

    def get_device_info(self, entry_id: str) -> dict[str, Any]:
        """Return device info for Home Assistant."""
        return {
            "identifiers": {("sprsun_modbus", entry_id)},
            "name": "SPRSUN Heat Pump",
            "manufacturer": "SPRSUN",
            "model": "Heat Pump (CAREL Controller)",
        }

    def get_sensors(self) -> tuple[SensorSpec, ...]:
        """Return CAREL core read-only sensor specifications."""
        return CAREL_CORE_SENSORS

    def get_binary_sensors(self) -> tuple[BinarySensorSpec, ...]:
        """Return CAREL core read-only binary sensor specifications."""
        return CAREL_CORE_BINARY_SENSORS

    def get_numbers(self) -> tuple[NumberSpec, ...]:
        """Return CAREL core read-write number specifications."""
        return CAREL_NUMBERS

    def get_selects(self) -> tuple[SelectSpec, ...]:
        """Return CAREL core read-write select specifications."""
        return CAREL_SELECTS

    def get_switches(self) -> tuple[SwitchSpec, ...]:
        """Return CAREL core read-write switch specifications."""
        return CAREL_SWITCHES

    def get_buttons(self) -> tuple[ButtonSpec, ...]:
        """Return CAREL momentary button specifications."""
        return CAREL_BUTTONS

    def get_expert_numbers(self) -> tuple[NumberSpec, ...]:
        """Return opt-in CAREL engineering/expert number specifications."""
        return CAREL_EXPERT_NUMBERS

    def get_expert_selects(self) -> tuple[SelectSpec, ...]:
        """Return opt-in CAREL engineering/expert select specifications."""
        return CAREL_EXPERT_SELECTS

    def get_expert_switches(self) -> tuple[SwitchSpec, ...]:
        """Return opt-in CAREL engineering/expert switch specifications."""
        return CAREL_EXPERT_SWITCHES

    def get_derived_sensors(self) -> tuple[DerivedSensorSpec, ...]:
        """Return CAREL calculated/derived sensor specifications."""
        return CAREL_DERIVED_SENSORS

    def compute_derived_data(
        self,
        data: Mapping[str, Any],
        now: float | None = None,
    ) -> dict[str, Any]:
        """Compute CAREL derived sensor values from coordinator data."""
        return {
            spec.key: spec.value_fn(data)
            for spec in CAREL_DERIVED_SENSORS
        }

    def has_rw_data(self, data: Mapping[str, Any]) -> bool:
        """Verify core CAREL RW registers and power coil were loaded."""
        return (
            "unit_mode" in data
            and "heating_setpoint" in data
            and "power" in data
        )

    @classmethod
    def detect(cls, client: ModbusTcpClient, device_address: int) -> bool:
        """Detect CAREL controller via signature registers while rejecting all-zero frames."""
        try:
            # 1. Holding 0..3: CoolHeat_Mode (0..4) + at least one realistic setpoint (5.0..70.0 °C => 50..700)
            core_res = client.read_holding_registers(
                address=0,
                count=4,
                device_id=device_address,
            )
            if core_res.isError() or not getattr(core_res, "registers", None) or len(core_res.registers) < 4:
                return False

            mode, heat_sp, cool_sp, dhw_sp = core_res.registers[:4]
            if mode not in _CAREL_VALID_UNIT_MODES:
                return False
            # Reject all-zero dummy frames: at least one setpoint must be in realistic 5.0..70.0 °C range
            if not any(50 <= sp <= 700 for sp in (heat_sp, cool_sp, dhw_sp)):
                return False

            # 2. Holding 215..217: unit_run_mode (0..2) and unit_status (0..10)
            status_res = client.read_holding_registers(
                address=215,
                count=3,
                device_id=device_address,
            )
            if status_res.isError() or not getattr(status_res, "registers", None) or len(status_res.registers) < 3:
                return False

            run_mode = status_res.registers[0]
            unit_status = status_res.registers[2]
            if run_mode not in _CAREL_VALID_RUN_MODES or unit_status not in _CAREL_VALID_STATUSES:
                return False

            # 3. Discrete Input 0 (FC 0x02): CAREL uses DI space (CHICO only uses Holding Registers)
            di_res = client.read_discrete_inputs(
                address=0,
                count=1,
                device_id=device_address,
            )
            if di_res.isError() or not getattr(di_res, "bits", None):
                return False

            _LOGGER.info(
                "CAREL controller detected (mode=%d, status=%d, setpoints=%s)",
                mode,
                unit_status,
                (heat_sp / 10, cool_sp / 10, dhw_sp / 10),
            )
            return True
        except Exception as err:
            _LOGGER.debug("CAREL detection failed: %s", err)
            return False

    @classmethod
    def probe_connection(cls, client: ModbusTcpClient, device_address: int) -> bool:
        """Verify basic Modbus connectivity for a manually selected CAREL controller."""
        try:
            status_res = client.read_holding_registers(
                address=217,
                count=1,
                device_id=device_address,
            )
            if status_res.isError() or not getattr(status_res, "registers", None):
                return False
            if status_res.registers[0] not in _CAREL_VALID_STATUSES:
                return False

            di_res = client.read_discrete_inputs(
                address=0,
                count=1,
                device_id=device_address,
            )
            return not di_res.isError() and bool(getattr(di_res, "bits", None))
        except Exception as err:
            _LOGGER.debug("CAREL probe failed: %s", err)
            return False

    def _read_batch_into(
        self,
        client: ModbusTcpClient,
        device_address: int,
        batch: ModbusBatchSpec,
        data: dict[str, Any],
        *,
        optional: bool = False,
        turnaround_delay: float = 0.05,
    ) -> bool:
        """Read and decode a single CAREL Modbus batch into ``data``."""
        try:
            raw_values = read_modbus_batch(
                client,
                device_address,
                batch,
                turnaround_delay=turnaround_delay,
            )
            decode_batch_into_data(
                _CAREL_ALL_READ_SPECS,
                batch.space,
                batch.start_address,
                raw_values,
                data,
            )
            return True
        except ModbusDesyncError:
            raise
        except ModbusBatchError as err:
            if optional:
                _LOGGER.debug("Optional CAREL batch '%s' skipped: %s", batch.description, err)
                return False
            raise

    def read_all_registers(
        self,
        client: ModbusTcpClient,
        device_address: int,
        initial_read: bool = False,
    ) -> dict[str, Any]:
        """Read CAREL registers, discrete inputs, and coils using two-tier batching."""
        data: dict[str, Any] = {}

        # Tier 1: Core fast RO telemetry (required)
        for idx, batch in enumerate(CAREL_RO_BATCHES):
            self._read_batch_into(
                client,
                device_address,
                batch,
                data,
                optional=False,
                turnaround_delay=0.0 if idx == 0 else 0.05,
            )

        # Tier 1b: Optional RO batches (component status DI 178..183, BLDC 333..335, power coil 40)
        for batch in CAREL_OPTIONAL_RO_BATCHES:
            self._read_batch_into(
                client,
                device_address,
                batch,
                data,
                optional=True,
                turnaround_delay=0.05,
            )

        # Tier 1c: Optional alarm block DI 13..177 (1 FC 0x02 read -> aggregated alarm state)
        try:
            alarm_bits = read_modbus_batch(
                client,
                device_address,
                CAREL_ALARM_BATCH,
                turnaround_delay=0.05,
            )
            alarm_active, summary, active_list = _decode_alarm_bits([bool(b) for b in alarm_bits])
            data["alarm_active"] = alarm_active
            data["active_alarms"] = summary
            data["active_alarms_list"] = active_list
        except ModbusDesyncError:
            raise
        except ModbusBatchError as err:
            _LOGGER.debug("Optional CAREL alarm batch skipped: %s", err)

        # Tier 2: RW configuration & optional expert parameters (startup + periodic refresh)
        if initial_read:
            for batch in CAREL_RW_BATCHES:
                try:
                    self._read_batch_into(
                        client,
                        device_address,
                        batch,
                        data,
                        optional=False,
                        turnaround_delay=0.05,
                    )
                except ModbusDesyncError:
                    raise
                except Exception as err:
                    _LOGGER.warning("Failed to read CAREL RW batch '%s': %s", batch.description, err)

            for batch in CAREL_OPTIONAL_RW_BATCHES:
                try:
                    self._read_batch_into(
                        client,
                        device_address,
                        batch,
                        data,
                        optional=True,
                        turnaround_delay=0.05,
                    )
                except ModbusDesyncError:
                    raise
                except Exception as err:
                    _LOGGER.debug("Failed to read optional CAREL RW batch '%s': %s", batch.description, err)

        return data

    def write_register(
        self,
        client: ModbusTcpClient,
        device_address: int,
        address: int,
        value: int,
    ) -> bool:
        """Write a single CAREL holding register (FC 0x06)."""
        try:
            result = client.write_register(
                address=address,
                value=value & 0xFFFF,
                device_id=device_address,
            )
            return not result.isError()
        except Exception as err:
            _LOGGER.error("CAREL write_register error at %d: %s", address, err)
            return False

    # ------------------------------------------------------------------
    # Safe live reads & CAREL mode-switch sequence
    # ------------------------------------------------------------------

    async def _async_read_live_unit_mode(self, coordinator: Any) -> int:
        """Read Holding 0 (CoolHeat_Mode) live before writes; raise HomeAssistantError on failure."""
        from homeassistant.exceptions import HomeAssistantError

        try:
            raw_val = await coordinator.async_read_register(
                address=0,
                key="unit_mode",
                scale=1,
            )
            mode = int(raw_val)
        except Exception as err:
            raise HomeAssistantError(
                f"Cannot read live CAREL unit_mode (Holding 0) before write: {err}"
            ) from err

        if mode not in _CAREL_VALID_UNIT_MODES:
            raise HomeAssistantError(
                f"Invalid live CAREL unit_mode value {mode} read from Holding 0"
            )
        return mode

    async def _async_read_live_power(self, coordinator: Any) -> bool:
        """Read Coil 40 (OnOffUnitMng.KeybOnOff) live; raise HomeAssistantError on failure."""
        from homeassistant.exceptions import HomeAssistantError

        try:
            return bool(await coordinator.async_read_coil(address=40, key="power"))
        except Exception as err:
            raise HomeAssistantError(
                f"Cannot read live CAREL power coil (Coil 40) before write: {err}"
            ) from err

    async def _async_write_unit_mode(
        self,
        coordinator: Any,
        target_mode: int,
        *,
        current_mode: int | None = None,
        current_power: bool | None = None,
        desired_power: bool | None = None,
        write_power_fn: Callable[[bool], Awaitable[None]] | None = None,
    ) -> None:
        """Safely change Holding 0 (CoolHeat_Mode) with CAREL Coil 40 off/on sequence if running."""
        power_writer = write_power_fn or (lambda st: self.async_write_power(coordinator, st))

        if current_mode is None:
            current_mode = await self._async_read_live_unit_mode(coordinator)
        if current_power is None:
            current_power = await self._async_read_live_power(coordinator)

        mode_changed = target_mode != current_mode
        final_power = current_power if desired_power is None else desired_power

        if mode_changed:
            if current_power:
                await power_writer(False)
            await coordinator.async_write_register(
                address=0,
                value=float(target_mode),
                key="unit_mode",
                scale=1,
            )
            if final_power:
                await power_writer(True)
        elif desired_power is not None and desired_power != current_power:
            await power_writer(desired_power)

    async def async_write_select(
        self,
        coordinator: Any,
        address: int,
        value: int,
        key: str,
    ) -> None:
        """Route unit_mode (Holding 0) through the safe CAREL mode-switch sequence."""
        if address == 0 and key == "unit_mode":
            await self._async_write_unit_mode(coordinator, int(value))
            return
        await super().async_write_select(coordinator, address, value, key)

    async def async_write_power(self, coordinator: Any, state: bool) -> None:
        """Turn CAREL unit ON or OFF via Coil 40 (OnOffUnitMng.KeybOnOff)."""
        await coordinator.async_write_coil(address=40, value=bool(state), key="power")

    # ------------------------------------------------------------------
    # Climate abstraction (Space Heating/Cooling + DHW)
    # ------------------------------------------------------------------

    def get_space_climate_capabilities(self) -> ClimateCapabilities:
        """Return CAREL climate capabilities."""
        return ClimateCapabilities(
            enabled=True,
            hvac_modes=("off", "heat", "cool"),
            fan_modes=("daytime", "night", "eco", "pressure"),
            preset_modes=(),
            supports_target_temperature=True,
            supports_fan_mode=True,
            supports_preset_mode=False,
            min_temp=10.0,
            max_temp=55.0,
            supports_dhw=True,
            dhw_hvac_modes=("off", "heat"),
            dhw_min_temp=10.0,
            dhw_max_temp=60.0,
        )

    def get_space_min_temp(self, hvac_mode: HVACMode | str | None) -> float:
        """Return dynamic min temperature for active CAREL space mode."""
        return 12.0 if str(hvac_mode) == "cool" else 10.0

    def get_space_max_temp(self, hvac_mode: HVACMode | str | None) -> float:
        """Return dynamic max temperature for active CAREL space mode."""
        return 40.0 if str(hvac_mode) == "cool" else 55.0

    @staticmethod
    def _is_unit_powered(data: Mapping[str, Any] | None) -> bool | None:
        """Return power state from Coil 40 (falling back to DI 0 unit_on)."""
        power = extract_cache_value(data, "power")
        if power is not None:
            return bool(power)
        unit_on = extract_cache_value(data, "unit_on")
        if unit_on is not None:
            return bool(unit_on)
        return None

    def get_space_hvac_mode(self, data: Mapping[str, Any] | None) -> HVACMode | None:
        """Resolve current CAREL space HVAC mode."""
        from homeassistant.components.climate import HVACMode

        powered = self._is_unit_powered(data)
        if powered is None:
            return None
        if not powered:
            return HVACMode.OFF

        unit_mode = extract_cache_value(data, "unit_mode")
        if unit_mode is None:
            return None

        mode_int = int(unit_mode)
        if mode_int in (0, 3):
            return HVACMode.COOL
        if mode_int in (1, 4):
            return HVACMode.HEAT
        # mode_int == 2 is DHW-only
        return HVACMode.OFF

    def get_space_hvac_action(self, data: Mapping[str, Any] | None) -> HVACAction | None:
        """Resolve current CAREL space HVAC action."""
        from homeassistant.components.climate import HVACAction, HVACMode

        hvac_mode = self.get_space_hvac_mode(data)
        if hvac_mode is None:
            return None
        if hvac_mode == HVACMode.OFF:
            return HVACAction.OFF

        comp_on = bool(extract_cache_value(data, "compressor_running", False))
        if not comp_on:
            speed = _as_float(data, "compressor_speed")
            comp_on = speed is not None and speed > 0.0

        if not comp_on:
            return HVACAction.IDLE

        run_mode = extract_cache_value(data, "unit_run_mode")
        if run_mode is not None:
            run_int = int(run_mode)
            if run_int == 2:
                # Currently heating DHW tank, space circuit is idle
                return HVACAction.IDLE
            if run_int == 0:
                return HVACAction.COOLING
            if run_int == 1:
                return HVACAction.HEATING

        return HVACAction.COOLING if hvac_mode == HVACMode.COOL else HVACAction.HEATING

    def get_space_current_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Return inlet water temperature."""
        return _as_float(data, "inlet_temp")

    def get_space_target_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Return target temperature for current CAREL space mode."""
        unit_mode = extract_cache_value(data, "unit_mode")
        if unit_mode is None:
            return None
        if int(unit_mode) in (0, 3):
            return _as_float(data, "cooling_setpoint")
        return _as_float(data, "heating_setpoint")

    def get_space_fan_mode(self, data: Mapping[str, Any] | None) -> str | None:
        """Return current CAREL fan mode."""
        raw = extract_cache_value(data, "fan_mode")
        if raw is None:
            return None
        return _CAREL_RAW_TO_FAN_MODE.get(int(raw))

    async def async_set_space_hvac_mode(
        self,
        coordinator: Any,
        hvac_mode: HVACMode | str,
        data: Mapping[str, Any] | None,
        write_power_fn: Callable[[bool], Awaitable[None]] | None = None,
    ) -> None:
        """Apply space HVAC mode using live Holding 0 & Coil 40 reads."""
        from homeassistant.components.climate import HVACMode

        current_mode = await self._async_read_live_unit_mode(coordinator)
        current_power = await self._async_read_live_power(coordinator)
        dhw_active = current_power and current_mode in (2, 3, 4)

        if hvac_mode == HVACMode.OFF:
            if dhw_active and current_mode in (3, 4):
                # Keep DHW running, switch to DHW-only mode (2)
                await self._async_write_unit_mode(
                    coordinator,
                    2,
                    current_mode=current_mode,
                    current_power=current_power,
                    desired_power=True,
                    write_power_fn=write_power_fn,
                )
            else:
                writer = write_power_fn or (lambda st: self.async_write_power(coordinator, st))
                await writer(False)
            return

        if hvac_mode == HVACMode.COOL:
            target_mode = 3 if dhw_active else 0
        elif hvac_mode == HVACMode.HEAT:
            target_mode = 4 if dhw_active else 1
        else:
            return

        await self._async_write_unit_mode(
            coordinator,
            target_mode,
            current_mode=current_mode,
            current_power=current_power,
            desired_power=True,
            write_power_fn=write_power_fn,
        )

    async def async_set_space_temperature(
        self,
        coordinator: Any,
        temperature: float,
        data: Mapping[str, Any] | None,
    ) -> None:
        """Write CAREL space heating (Holding 1) or cooling (Holding 2) setpoint."""
        current_mode = await self._async_read_live_unit_mode(coordinator)
        if current_mode in (0, 3):
            address, key = 2, "cooling_setpoint"
        else:
            address, key = 1, "heating_setpoint"

        raw_word = encode_registers(temperature, DataType.INT16, scale=0.1)[0]
        await coordinator.async_write_register(
            address=address,
            value=float(raw_word),
            key=key,
            scale=1,
            cached_value=temperature,
        )

    async def async_set_space_fan_mode(
        self,
        coordinator: Any,
        fan_mode: str,
    ) -> None:
        """Write CAREL fan mode (Holding 12)."""
        raw = _CAREL_FAN_MODE_TO_RAW.get(fan_mode)
        if raw is None:
            _LOGGER.warning("Unsupported CAREL fan mode: %s", fan_mode)
            return
        await coordinator.async_write_register(
            address=12,
            value=float(raw),
            key="fan_mode",
            scale=1,
        )

    def get_dhw_hvac_mode(self, data: Mapping[str, Any] | None) -> HVACMode | None:
        """Resolve current CAREL DHW HVAC mode."""
        from homeassistant.components.climate import HVACMode

        powered = self._is_unit_powered(data)
        if powered is None:
            return None
        if not powered:
            return HVACMode.OFF

        unit_mode = extract_cache_value(data, "unit_mode")
        if unit_mode is None:
            return None

        return HVACMode.HEAT if int(unit_mode) in (2, 3, 4) else HVACMode.OFF

    def get_dhw_hvac_action(self, data: Mapping[str, Any] | None) -> HVACAction | None:
        """Resolve current CAREL DHW HVAC action."""
        from homeassistant.components.climate import HVACAction, HVACMode

        dhw_mode = self.get_dhw_hvac_mode(data)
        if dhw_mode is None:
            return None
        if dhw_mode == HVACMode.OFF:
            return HVACAction.OFF

        comp_on = bool(extract_cache_value(data, "compressor_running", False))
        if not comp_on:
            speed = _as_float(data, "compressor_speed")
            comp_on = speed is not None and speed > 0.0

        run_mode = extract_cache_value(data, "unit_run_mode")
        three_way = bool(extract_cache_value(data, "three_way_valve", False))
        if comp_on and (run_mode is not None and int(run_mode) == 2 or three_way):
            return HVACAction.HEATING
        return HVACAction.IDLE

    def get_dhw_current_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Return hot water tank temperature."""
        return _as_float(data, "hotwater_temp")

    def get_dhw_target_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Return hot water setpoint."""
        return _as_float(data, "hotwater_setpoint")

    async def async_set_dhw_hvac_mode(
        self,
        coordinator: Any,
        hvac_mode: HVACMode | str,
        data: Mapping[str, Any] | None,
        write_power_fn: Callable[[bool], Awaitable[None]] | None = None,
    ) -> None:
        """Apply DHW HVAC mode using live Holding 0 & Coil 40 reads."""
        from homeassistant.components.climate import HVACMode

        current_mode = await self._async_read_live_unit_mode(coordinator)
        current_power = await self._async_read_live_power(coordinator)

        if hvac_mode == HVACMode.OFF:
            if current_power and current_mode == 3:
                await self._async_write_unit_mode(
                    coordinator,
                    0,
                    current_mode=current_mode,
                    current_power=current_power,
                    desired_power=True,
                    write_power_fn=write_power_fn,
                )
            elif current_power and current_mode == 4:
                await self._async_write_unit_mode(
                    coordinator,
                    1,
                    current_mode=current_mode,
                    current_power=current_power,
                    desired_power=True,
                    write_power_fn=write_power_fn,
                )
            else:
                writer = write_power_fn or (lambda st: self.async_write_power(coordinator, st))
                await writer(False)
            return

        if hvac_mode == HVACMode.HEAT:
            if current_power and current_mode == 0:
                target_mode = 3
            elif current_power and current_mode == 1:
                target_mode = 4
            elif current_mode in (2, 3, 4):
                target_mode = current_mode
            else:
                target_mode = 2

            await self._async_write_unit_mode(
                coordinator,
                target_mode,
                current_mode=current_mode,
                current_power=current_power,
                desired_power=True,
                write_power_fn=write_power_fn,
            )

    async def async_set_dhw_temperature(
        self,
        coordinator: Any,
        temperature: float,
    ) -> None:
        """Write CAREL hot water setpoint (Holding 3)."""
        raw_word = encode_registers(temperature, DataType.INT16, scale=0.1)[0]
        await coordinator.async_write_register(
            address=3,
            value=float(raw_word),
            key="hotwater_setpoint",
            scale=1,
            cached_value=temperature,
        )
