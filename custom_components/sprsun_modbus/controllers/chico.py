"""CHICO controller implementation."""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
import logging
from typing import TYPE_CHECKING, Any

from .base import ControllerBase
from .chico_registers import (
    CHICO_BUTTONS,
    CHICO_BINARY_SENSORS,
    CHICO_NUMBERS,
    CHICO_RO_BATCH,
    CHICO_RW_BATCHES,
    CHICO_SELECTS,
    CHICO_SENSORS,
    CHICO_STATUS_REGISTER_KEYS,
    CHICO_SWITCHES,
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
    NumberSpec,
    RegisterSpace,
    SelectSpec,
    SensorSpec,
    SwitchSpec,
    extract_cache_value,
)

if TYPE_CHECKING:
    from homeassistant.components.climate import HVACAction, HVACMode
    from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)

_CHICO_RW_SPECS = CHICO_NUMBERS + CHICO_SELECTS + CHICO_SWITCHES
_CHICO_FAN_MODE_TO_RAW: dict[str, int] = {
    "normal": 0,
    "eco": 1,
    "night": 2,
    "test": 3,
}
_CHICO_RAW_TO_FAN_MODE: dict[int, str] = {v: k for k, v in _CHICO_FAN_MODE_TO_RAW.items()}


class ChicoController(ControllerBase):
    """CHICO controller (original SPRSUN controller)."""

    @property
    def name(self) -> str:
        """Return controller type name."""
        return "CHICO"

    @property
    def manufacturer(self) -> str:
        """Return controller manufacturer."""
        return "SPRSUN (CHICO Controller)"

    def get_sensors(self) -> tuple[SensorSpec, ...]:
        """Return CHICO read-only sensor specifications."""
        return CHICO_SENSORS

    def get_binary_sensors(self) -> tuple[BinarySensorSpec, ...]:
        """Return CHICO binary sensor specifications."""
        return CHICO_BINARY_SENSORS

    def get_numbers(self) -> tuple[NumberSpec, ...]:
        """Return CHICO read-write number specifications."""
        return CHICO_NUMBERS

    def get_selects(self) -> tuple[SelectSpec, ...]:
        """Return CHICO read-write select specifications."""
        return CHICO_SELECTS

    def get_switches(self) -> tuple[SwitchSpec, ...]:
        """Return CHICO read-write switch specifications."""
        return CHICO_SWITCHES

    def get_buttons(self) -> tuple[ButtonSpec, ...]:
        """Return CHICO momentary button specifications."""
        return CHICO_BUTTONS

    def has_rw_data(self, data: Mapping[str, Any]) -> bool:
        """Return True when primary RW setpoints have been loaded."""
        return "heating_setpoint" in data

    def read_all_registers(
        self,
        client: ModbusTcpClient,
        device_address: int,
        initial_read: bool = False,
    ) -> dict[str, Any]:
        """Read all CHICO registers."""
        data: dict[str, Any] = {}

        # Read all read-only registers in one batch (0x0000-0x0031 = 50 registers)
        try:
            ro_registers = [
                int(v)
                for v in read_modbus_batch(
                    client,
                    device_address,
                    CHICO_RO_BATCH,
                )
            ]

            # Sanity check: detect corrupt zero-filled frames from RS485 gateway
            is_all_zeros = not any(ro_registers)
            controller_ver = ro_registers[0x002C] if len(ro_registers) > 0x002C else 0
            water_temps_zero = (
                ro_registers[0x000E] == 0
                and ro_registers[0x000F] == 0
                and ro_registers[0x0012] == 0
            )

            if is_all_zeros or (controller_ver == 0 and water_temps_zero):
                raise ValueError(
                    f"Corrupt Modbus frame detected: all registers zero or key parameters invalid "
                    f"(all_zeros={is_all_zeros}, controller_version={controller_ver}, "
                    f"inlet={ro_registers[0x000E]}, hotwater={ro_registers[0x000F]}). Discarding."
                )

            decode_batch_into_data(
                CHICO_SENSORS,
                RegisterSpace.HOLDING_REGISTER,
                CHICO_RO_BATCH.start_address,
                ro_registers,
                data,
            )
            _LOGGER.debug("CHICO: Read %d read-only registers", len(data))

        except Exception as err:
            _LOGGER.debug("CHICO: Error reading RO registers: %s", err)
            raise

        # Store raw status words for binary sensor bitfield decoding
        for address, key in CHICO_STATUS_REGISTER_KEYS.items():
            index = address - CHICO_RO_BATCH.start_address
            if index < len(ro_registers):
                data[key] = ro_registers[index]

        if initial_read:
            _LOGGER.debug("CHICO: Reading RW registers in batches...")
            total_rw_read = 0
            for batch in CHICO_RW_BATCHES:
                try:
                    rw_registers = [
                        int(v)
                        for v in read_modbus_batch(
                            client,
                            device_address,
                            batch,
                            turnaround_delay=0.20,
                        )
                    ]
                    decoded = decode_batch_into_data(
                        _CHICO_RW_SPECS,
                        RegisterSpace.HOLDING_REGISTER,
                        batch.start_address,
                        rw_registers,
                        data,
                    )
                    total_rw_read += decoded
                    _LOGGER.debug("CHICO: Read batch %s (%d registers)", batch.description, batch.count)
                except ModbusDesyncError as err:
                    _LOGGER.error(
                        "CHICO: Batch size mismatch for %s! %s. "
                        "Resetting connection to prevent stream desynchronization.",
                        batch.description,
                        err,
                    )
                    try:
                        client.close()
                    except Exception:
                        pass
                    break
                except (ModbusBatchError, Exception) as err:
                    _LOGGER.debug(
                        "CHICO: Error/exception reading batch %s (0x%04X): %s",
                        batch.description,
                        batch.start_address,
                        err,
                    )
                    continue

            _LOGGER.debug(
                "CHICO: Batch RW read completed (%d registers in %d batches)",
                total_rw_read,
                len(CHICO_RW_BATCHES),
            )

        return data

    def write_register(
        self,
        client: ModbusTcpClient,
        device_address: int,
        address: int,
        value: int,
    ) -> bool:
        """Write a CHICO register."""
        if not client.connected:
            if not client.connect():
                raise ConnectionError("Cannot connect to Modbus device")

        result = client.write_register(
            address=address,
            value=value,
            device_id=device_address,
        )

        if result.isError():
            raise ValueError(f"Modbus write error: {result}")

        return True

    def get_platforms(self) -> list[str]:
        """Return supported platforms for CHICO."""
        return ["sensor", "binary_sensor", "number", "select", "switch", "button", "climate"]

    def get_device_info(self, entry_id: str) -> dict[str, Any]:
        """Return device info for CHICO controller."""
        return {
            "identifiers": {("sprsun_modbus", entry_id)},
            "name": "SPRSUN Heat Pump",
            "manufacturer": "SPRSUN",
            "model": "Heat Pump (CHICO Controller)",
        }

    @classmethod
    def probe_connection(cls, client: ModbusTcpClient, device_address: int) -> bool:
        """Verify CHICO Modbus connectivity by reading holding register 0x0000."""
        result = client.read_holding_registers(
            address=0x0000,
            count=1,
            device_id=device_address,
        )
        return not result.isError()

    @classmethod
    def detect(cls, client: ModbusTcpClient, device_address: int) -> bool:
        """Detect CHICO controller by reading version signature registers 0x002C/0x002D."""
        try:
            result = client.read_holding_registers(
                address=0x002C,
                count=2,
                device_id=device_address,
            )

            if result.isError():
                return False

            if len(result.registers) == 2:
                controller_ver = result.registers[0]
                display_ver = result.registers[1]

                if 0 <= controller_ver <= 999 and 0 <= display_ver <= 999:
                    _LOGGER.info(
                        "CHICO controller detected (Controller v%d, Display v%d)",
                        controller_ver,
                        display_ver,
                    )
                    return True

        except Exception as err:
            _LOGGER.debug("CHICO detection failed: %s", err)

        return False

    # ------------------------------------------------------------------
    # Climate support (CHICO P06 / P01 / P02 / P04 / P07 / G09 / 0x0032)
    # ------------------------------------------------------------------

    def get_space_climate_capabilities(self) -> ClimateCapabilities:
        """Return climate capabilities for CHICO."""
        return ClimateCapabilities(
            enabled=True,
            hvac_modes=("off", "heat", "cool", "heat_cool"),
            fan_modes=("normal", "eco", "night", "test"),
            preset_modes=("none", "eco", "boost"),
            supports_target_temperature=True,
            supports_fan_mode=True,
            supports_preset_mode=True,
            min_temp=10.0,
            max_temp=55.0,
            supports_dhw=True,
            dhw_hvac_modes=("off", "heat"),
            dhw_min_temp=10.0,
            dhw_max_temp=55.0,
        )

    @staticmethod
    def _is_power_on(data: Mapping[str, Any] | None) -> bool:
        reg_value = int(extract_cache_value(data, "_control_0032", 0) or 0)
        return bool(reg_value & 1)

    @staticmethod
    def _is_compressor_running(data: Mapping[str, Any] | None) -> bool:
        out1_val = int(extract_cache_value(data, "output_symbol_1", 0) or 0)
        return bool(out1_val & 1)

    def get_space_min_temp(self, hvac_mode: HVACMode | str | None) -> float:
        """Return dynamic minimum temperature based on cooling vs heating mode."""
        if str(hvac_mode) == "cool":
            return 12.0
        return 10.0

    def get_space_max_temp(self, hvac_mode: HVACMode | str | None) -> float:
        """Return dynamic maximum temperature based on cooling vs heating mode."""
        if str(hvac_mode) == "cool":
            return 30.0
        return 55.0

    def get_space_hvac_mode(self, data: Mapping[str, Any] | None) -> HVACMode:
        """Return current space HVAC mode for CHICO."""
        from homeassistant.components.climate import HVACMode

        if not self._is_power_on(data):
            return HVACMode.OFF

        auto_mode = extract_cache_value(data, "mode_control_enable", 0)
        if auto_mode == 1:
            return HVACMode.HEAT_COOL

        unit_mode = int(extract_cache_value(data, "unit_mode", 1))
        if unit_mode in (1, 3):
            return HVACMode.HEAT
        if unit_mode in (2, 4):
            return HVACMode.COOL
        return HVACMode.OFF

    def get_space_hvac_action(self, data: Mapping[str, Any] | None) -> HVACAction:
        """Return current space HVAC action for CHICO."""
        from homeassistant.components.climate import HVACAction

        if not self._is_power_on(data):
            return HVACAction.OFF
        if not self._is_compressor_running(data):
            return HVACAction.IDLE

        unit_mode = int(extract_cache_value(data, "unit_mode", 1))
        if unit_mode in (1, 3):
            return HVACAction.HEATING
        if unit_mode in (2, 4):
            return HVACAction.COOLING
        return HVACAction.IDLE

    def get_space_current_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Return inlet water temperature."""
        return extract_cache_value(data, "inlet_temp")

    def get_space_target_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Return heating or cooling setpoint depending on active CHICO unit mode."""
        unit_mode = int(extract_cache_value(data, "unit_mode", 1))
        if unit_mode in (1, 3):
            return extract_cache_value(data, "heating_setpoint")
        return extract_cache_value(data, "cooling_setpoint")

    def get_space_fan_mode(self, data: Mapping[str, Any] | None) -> str | None:
        """Return current fan mode string."""
        fan_mode_value = int(extract_cache_value(data, "fan_mode", 0))
        return _CHICO_RAW_TO_FAN_MODE.get(fan_mode_value, "normal")

    def get_space_preset_mode(self, data: Mapping[str, Any] | None) -> str:
        """Return current preset mode."""
        from homeassistant.components.climate import PRESET_BOOST, PRESET_ECO, PRESET_NONE

        if extract_cache_value(data, "mode_control_enable", 0) == 1:
            return PRESET_ECO
        if int(extract_cache_value(data, "fan_mode", 0)) == 0:
            return PRESET_BOOST
        return PRESET_NONE

    async def async_write_power(self, coordinator: Any, state: bool) -> None:
        """Write power switch state (bit 0 of register 0x0032)."""
        await coordinator.async_write_bit(0x0032, 0, state, reg_key="_control_0032")

    async def async_set_space_hvac_mode(
        self,
        coordinator: Any,
        hvac_mode: HVACMode | str,
        data: Mapping[str, Any] | None,
        write_power_fn: Callable[[bool], Awaitable[None]] | None = None,
    ) -> None:
        """Set CHICO space HVAC mode."""
        from homeassistant.components.climate import HVACMode

        power_writer = write_power_fn or (lambda st: self.async_write_power(coordinator, st))

        if hvac_mode == HVACMode.OFF:
            await power_writer(False)
        elif hvac_mode == HVACMode.HEAT:
            await power_writer(True)
            await coordinator.async_write_register(
                address=0x0191, value=0, key="mode_control_enable", scale=1
            )
            current_mode = int(extract_cache_value(data, "unit_mode", 1))
            new_mode = 3 if current_mode in (3, 4) else 1
            await coordinator.async_write_register(
                address=0x0036, value=new_mode, key="unit_mode", scale=1
            )
        elif hvac_mode == HVACMode.COOL:
            await power_writer(True)
            await coordinator.async_write_register(
                address=0x0191, value=0, key="mode_control_enable", scale=1
            )
            current_mode = int(extract_cache_value(data, "unit_mode", 1))
            new_mode = 4 if current_mode in (3, 4) else 2
            await coordinator.async_write_register(
                address=0x0036, value=new_mode, key="unit_mode", scale=1
            )
        elif hvac_mode == HVACMode.HEAT_COOL:
            await power_writer(True)
            await coordinator.async_write_register(
                address=0x0191, value=1, key="mode_control_enable", scale=1
            )

    async def async_set_space_temperature(
        self,
        coordinator: Any,
        temperature: float,
        data: Mapping[str, Any] | None,
    ) -> None:
        """Write CHICO heating or cooling setpoint (scale 0.5°C -> x2)."""
        unit_mode = int(extract_cache_value(data, "unit_mode", 1))
        if unit_mode in (1, 3):
            await coordinator.async_write_register(
                address=0x00CC,
                value=temperature,
                key="heating_setpoint",
                scale=2,
            )
        else:
            await coordinator.async_write_register(
                address=0x00CB,
                value=temperature,
                key="cooling_setpoint",
                scale=2,
            )

    async def async_set_space_fan_mode(self, coordinator: Any, fan_mode: str) -> None:
        """Write CHICO P07 fan mode."""
        value = _CHICO_FAN_MODE_TO_RAW.get(fan_mode)
        if value is not None:
            await coordinator.async_write_register(
                address=0x0190,
                value=value,
                key="fan_mode",
                scale=1,
            )

    async def async_set_space_preset_mode(self, coordinator: Any, preset_mode: str) -> None:
        """Write CHICO preset mode."""
        from homeassistant.components.climate import PRESET_BOOST, PRESET_ECO

        if preset_mode == PRESET_ECO:
            await coordinator.async_write_register(
                address=0x0191,
                value=1,
                key="mode_control_enable",
                scale=1,
            )
        elif preset_mode == PRESET_BOOST:
            await self.async_set_space_fan_mode(coordinator, "normal")
        else:
            await coordinator.async_write_register(
                address=0x0191,
                value=0,
                key="mode_control_enable",
                scale=1,
            )

    def get_dhw_hvac_mode(self, data: Mapping[str, Any] | None) -> HVACMode:
        """Return current DHW HVAC mode for CHICO."""
        from homeassistant.components.climate import HVACMode

        if not self._is_power_on(data):
            return HVACMode.OFF
        unit_mode = int(extract_cache_value(data, "unit_mode", 1))
        if unit_mode in (0, 3, 4):
            return HVACMode.HEAT
        return HVACMode.OFF

    def get_dhw_hvac_action(self, data: Mapping[str, Any] | None) -> HVACAction:
        """Return current DHW HVAC action for CHICO."""
        from homeassistant.components.climate import HVACAction, HVACMode

        if self.get_dhw_hvac_mode(data) == HVACMode.OFF:
            return HVACAction.OFF

        compressor_running = self._is_compressor_running(data)
        status_val = int(extract_cache_value(data, "working_status_register", 0) or 0)
        hw_demand = bool(status_val & 1)
        unit_mode = int(extract_cache_value(data, "unit_mode", 1))

        if compressor_running and (unit_mode == 0 or (unit_mode in (3, 4) and hw_demand)):
            return HVACAction.HEATING
        return HVACAction.IDLE

    def get_dhw_current_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Return DHW tank water temperature."""
        return extract_cache_value(data, "hotwater_temp")

    def get_dhw_target_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Return DHW setpoint."""
        return extract_cache_value(data, "hotwater_setpoint")

    async def async_set_dhw_hvac_mode(
        self,
        coordinator: Any,
        hvac_mode: HVACMode | str,
        data: Mapping[str, Any] | None,
        write_power_fn: Callable[[bool], Awaitable[None]] | None = None,
    ) -> None:
        """Set CHICO DHW HVAC mode."""
        from homeassistant.components.climate import HVACMode

        power_writer = write_power_fn or (lambda st: self.async_write_power(coordinator, st))
        current_mode = int(extract_cache_value(data, "unit_mode", 1))

        if hvac_mode == HVACMode.OFF:
            if current_mode == 0:
                await power_writer(False)
            elif current_mode == 3:
                await coordinator.async_write_register(
                    address=0x0036, value=1, key="unit_mode", scale=1
                )
            elif current_mode == 4:
                await coordinator.async_write_register(
                    address=0x0036, value=2, key="unit_mode", scale=1
                )
        elif hvac_mode == HVACMode.HEAT:
            await power_writer(True)
            if current_mode == 1:
                await coordinator.async_write_register(
                    address=0x0036, value=3, key="unit_mode", scale=1
                )
            elif current_mode == 2:
                await coordinator.async_write_register(
                    address=0x0036, value=4, key="unit_mode", scale=1
                )
            elif current_mode not in (0, 3, 4):
                await coordinator.async_write_register(
                    address=0x0036, value=0, key="unit_mode", scale=1
                )

    async def async_set_dhw_temperature(self, coordinator: Any, temperature: float) -> None:
        """Write CHICO DHW setpoint (P04 at 0x00CA, scale 0.5°C -> x2)."""
        await coordinator.async_write_register(
            address=0x00CA,
            value=temperature,
            key="hotwater_setpoint",
            scale=2,
        )
