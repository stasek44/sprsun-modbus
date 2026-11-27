"""Base class for heat pump controller drivers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping
from typing import TYPE_CHECKING, Any

from .models import (
    BinarySensorSpec,
    ButtonSpec,
    ClimateCapabilities,
    DerivedSensorSpec,
    NumberSpec,
    SelectSpec,
    SensorSpec,
    SwitchSpec,
)

if TYPE_CHECKING:
    from homeassistant.components.climate import HVACAction, HVACMode
    from pymodbus.client import ModbusTcpClient


class ControllerBase(ABC):
    """Abstract base class for heat pump controllers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return controller type name."""

    @property
    @abstractmethod
    def manufacturer(self) -> str:
        """Return controller manufacturer."""

    @abstractmethod
    def read_all_registers(
        self,
        client: ModbusTcpClient,
        device_address: int,
        initial_read: bool = False,
    ) -> dict[str, Any]:
        """Read all relevant registers/points from the device."""

    @abstractmethod
    def write_register(
        self,
        client: ModbusTcpClient,
        device_address: int,
        address: int,
        value: int,
    ) -> bool:
        """Write a single holding register value."""

    @abstractmethod
    def get_platforms(self) -> list[str]:
        """Return list of supported Home Assistant platform names."""

    @abstractmethod
    def get_device_info(self, entry_id: str) -> dict[str, Any]:
        """Return device info dict for Home Assistant."""

    @classmethod
    @abstractmethod
    def detect(cls, client: ModbusTcpClient, device_address: int) -> bool:
        """Detect if this controller type is present at the given device address."""

    @classmethod
    def probe_connection(cls, client: ModbusTcpClient, device_address: int) -> bool:
        """Verify basic Modbus connectivity for this controller type."""
        return cls.detect(client, device_address)

    def has_rw_data(self, data: Mapping[str, Any]) -> bool:
        """Return True if read-write configuration data is present in fresh poll data."""
        return any(spec.key in data for spec in self.get_numbers()) or any(
            spec.key in data for spec in self.get_selects()
        )

    # ------------------------------------------------------------------
    # Declarative entity specifications (override per controller)
    # ------------------------------------------------------------------

    def get_sensors(self) -> tuple[SensorSpec, ...]:
        """Return core read-only sensor specifications for this controller."""
        return ()

    def get_expert_sensors(self) -> tuple[SensorSpec, ...]:
        """Return opt-in expert read-only sensor specifications."""
        return ()

    def get_derived_sensors(self) -> tuple[DerivedSensorSpec, ...]:
        """Return controller-derived/calculated sensor specifications."""
        return ()

    def compute_derived_data(
        self,
        data: Mapping[str, Any],
        now: float | None = None,
    ) -> dict[str, Any]:
        """Compute derived sensor values from current coordinator data."""
        return {}

    def get_binary_sensors(self) -> tuple[BinarySensorSpec, ...]:
        """Return core read-only binary sensor specifications for this controller."""
        return ()

    def get_expert_binary_sensors(self) -> tuple[BinarySensorSpec, ...]:
        """Return opt-in expert read-only binary sensor specifications."""
        return ()

    def get_numbers(self) -> tuple[NumberSpec, ...]:
        """Return read-write number specifications for this controller."""
        return ()

    def get_selects(self) -> tuple[SelectSpec, ...]:
        """Return read-write select specifications for this controller."""
        return ()

    def get_switches(self) -> tuple[SwitchSpec, ...]:
        """Return read-write switch specifications for this controller."""
        return ()

    def get_buttons(self) -> tuple[ButtonSpec, ...]:
        """Return momentary button specifications for this controller."""
        return ()

    def get_expert_numbers(self) -> tuple[NumberSpec, ...]:
        """Return opt-in engineering/expert read-write number specifications."""
        return ()

    def get_expert_selects(self) -> tuple[SelectSpec, ...]:
        """Return opt-in engineering/expert read-write select specifications."""
        return ()

    def get_expert_switches(self) -> tuple[SwitchSpec, ...]:
        """Return opt-in engineering/expert read-write switch specifications."""
        return ()

    # ------------------------------------------------------------------
    # Climate abstraction (override if controller supports climate)
    # ------------------------------------------------------------------

    def get_space_climate_capabilities(self) -> ClimateCapabilities:
        """Return climate capabilities for space heating/cooling and optional DHW."""
        return ClimateCapabilities(enabled=False, supports_dhw=False)

    def get_space_min_temp(self, hvac_mode: HVACMode | str | None) -> float:
        """Return minimum space target temperature for the active HVAC mode."""
        return self.get_space_climate_capabilities().min_temp

    def get_space_max_temp(self, hvac_mode: HVACMode | str | None) -> float:
        """Return maximum space target temperature for the active HVAC mode."""
        return self.get_space_climate_capabilities().max_temp

    def get_space_hvac_mode(self, data: Mapping[str, Any] | None) -> HVACMode | None:
        """Resolve current space HVAC mode from coordinator data."""
        raise NotImplementedError

    def get_space_hvac_action(self, data: Mapping[str, Any] | None) -> HVACAction | None:
        """Resolve current space HVAC action from coordinator data."""
        raise NotImplementedError

    def get_space_current_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Resolve current water/space temperature from coordinator data."""
        return None

    def get_space_target_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Resolve target space temperature from coordinator data."""
        return None

    def get_space_fan_mode(self, data: Mapping[str, Any] | None) -> str | None:
        """Resolve current fan mode from coordinator data."""
        return None

    def get_space_preset_mode(self, data: Mapping[str, Any] | None) -> str:
        """Resolve current preset mode from coordinator data."""
        return "none"

    async def async_set_space_hvac_mode(
        self,
        coordinator: Any,
        hvac_mode: HVACMode | str,
        data: Mapping[str, Any] | None,
        write_power_fn: Callable[[bool], Awaitable[None]] | None = None,
    ) -> None:
        """Apply a new space HVAC mode to the controller."""
        raise NotImplementedError

    async def async_set_space_temperature(
        self,
        coordinator: Any,
        temperature: float,
        data: Mapping[str, Any] | None,
    ) -> None:
        """Write target space temperature to the controller."""
        raise NotImplementedError

    async def async_set_space_fan_mode(
        self,
        coordinator: Any,
        fan_mode: str,
    ) -> None:
        """Write fan mode to the controller."""
        raise NotImplementedError

    async def async_set_space_preset_mode(
        self,
        coordinator: Any,
        preset_mode: str,
    ) -> None:
        """Write preset mode to the controller."""
        raise NotImplementedError

    async def async_write_power(self, coordinator: Any, state: bool) -> None:
        """Turn the unit power ON or OFF."""
        raise NotImplementedError

    def get_dhw_hvac_mode(self, data: Mapping[str, Any] | None) -> HVACMode | None:
        """Resolve current DHW HVAC mode from coordinator data."""
        raise NotImplementedError

    def get_dhw_hvac_action(self, data: Mapping[str, Any] | None) -> HVACAction | None:
        """Resolve current DHW HVAC action from coordinator data."""
        raise NotImplementedError

    def get_dhw_current_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Resolve current DHW tank temperature from coordinator data."""
        return None

    def get_dhw_target_temp(self, data: Mapping[str, Any] | None) -> float | None:
        """Resolve target DHW temperature from coordinator data."""
        return None

    async def async_set_dhw_hvac_mode(
        self,
        coordinator: Any,
        hvac_mode: HVACMode | str,
        data: Mapping[str, Any] | None,
        write_power_fn: Callable[[bool], Awaitable[None]] | None = None,
    ) -> None:
        """Apply a new DHW HVAC mode to the controller."""
        raise NotImplementedError

    async def async_set_dhw_temperature(
        self,
        coordinator: Any,
        temperature: float,
    ) -> None:
        """Write target DHW temperature to the controller."""
        raise NotImplementedError
