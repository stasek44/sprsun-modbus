"""Climate platform for SPRSUN Heat Pump."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_temp_step
from .controllers import build_device_info, resolve_controller, resolve_coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN climate entities based on controller capabilities."""
    coordinator = resolve_coordinator(hass, config_entry, DOMAIN)
    controller = resolve_controller(coordinator)
    capabilities = controller.get_space_climate_capabilities()

    entities: list[ClimateEntity] = []
    if capabilities.enabled:
        entities.append(SPRSUNClimate(coordinator, config_entry))
    if capabilities.supports_dhw:
        entities.append(SPRSUNDHWClimate(coordinator, config_entry))

    if entities:
        async_add_entities(entities)


def _round_to_step(value: float, step: float) -> float:
    """Round value to the nearest step (e.g. 0.5 or 1.0)."""
    if step <= 0:
        return value
    return float(round(value / step + 1e-9) * step)


class SPRSUNClimate(CoordinatorEntity, ClimateEntity):
    """Controller-agnostic Heat Pump Climate Entity for Heating/Cooling Control."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._controller = resolve_controller(coordinator)
        caps = self._controller.get_space_climate_capabilities()

        features = ClimateEntityFeature(0)
        if caps.supports_target_temperature:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if caps.supports_fan_mode:
            features |= ClimateEntityFeature.FAN_MODE
        if caps.supports_preset_mode:
            features |= ClimateEntityFeature.PRESET_MODE

        self._attr_supported_features = features
        self._attr_hvac_modes = [HVACMode(mode) for mode in caps.hvac_modes]
        self._attr_fan_modes = list(caps.fan_modes)
        self._attr_preset_modes = list(caps.preset_modes)

        self._attr_name = "Heating/Cooling"
        self._attr_unique_id = f"{config_entry.entry_id}_climate"
        self._attr_device_info = build_device_info(self._controller, config_entry)

    @property
    def target_temperature_step(self) -> float:
        """Return the target temperature step."""
        return get_temp_step(self._config_entry, getattr(self.coordinator, "config_entry", None))

    @property
    def precision(self) -> float:
        """Return the precision of the system."""
        return self.target_temperature_step

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(self.coordinator.last_update_success and self.coordinator.data is not None)

    @property
    def min_temp(self) -> float:
        """Return dynamic minimum temperature based on mode."""
        return self._controller.get_space_min_temp(self.hvac_mode)

    @property
    def max_temp(self) -> float:
        """Return dynamic maximum temperature based on mode."""
        return self._controller.get_space_max_temp(self.hvac_mode)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        return self._controller.get_space_hvac_mode(self.coordinator.data)

    @property
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action."""
        return self._controller.get_space_hvac_action(self.coordinator.data)

    @property
    def native_current_temperature(self) -> float | None:
        """Return inlet water temperature."""
        return self._controller.get_space_current_temp(self.coordinator.data)

    @property
    def native_target_temperature(self) -> float | None:
        """Return target temperature based on current mode."""
        return self._controller.get_space_target_temp(self.coordinator.data)

    @property
    def fan_mode(self) -> str | None:
        """Return current fan mode."""
        return self._controller.get_space_fan_mode(self.coordinator.data)

    @property
    def preset_mode(self) -> str:
        """Return current preset mode."""
        return self._controller.get_space_preset_mode(self.coordinator.data)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        await self._controller.async_set_space_hvac_mode(
            self.coordinator,
            hvac_mode,
            self.coordinator.data,
            write_power_fn=self._write_power,
        )
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs) -> None:
        """Set target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        temperature = _round_to_step(float(temperature), self.target_temperature_step)
        await self._controller.async_set_space_temperature(
            self.coordinator,
            temperature,
            self.coordinator.data,
        )
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan mode."""
        await self._controller.async_set_space_fan_mode(self.coordinator, fan_mode)
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        await self._controller.async_set_space_preset_mode(self.coordinator, preset_mode)
        self.async_write_ha_state()

    async def _write_power(self, state: bool) -> None:
        """Write power switch state via the active controller."""
        await self._controller.async_write_power(self.coordinator, state)


class SPRSUNDHWClimate(CoordinatorEntity, ClimateEntity):
    """Controller-agnostic Heat Pump DHW (Domestic Hot Water) Climate Entity."""

    _attr_has_entity_name = True
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, config_entry: ConfigEntry) -> None:
        """Initialize the DHW climate entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._controller = resolve_controller(coordinator)
        caps = self._controller.get_space_climate_capabilities()

        self._attr_hvac_modes = [HVACMode(mode) for mode in caps.dhw_hvac_modes]
        self._attr_min_temp = caps.dhw_min_temp
        self._attr_max_temp = caps.dhw_max_temp

        self._attr_name = "DHW"
        self._attr_unique_id = f"{config_entry.entry_id}_dhw_climate"
        self._attr_device_info = build_device_info(self._controller, config_entry)

    @property
    def target_temperature_step(self) -> float:
        """Return the target temperature step."""
        return get_temp_step(self._config_entry, getattr(self.coordinator, "config_entry", None))

    @property
    def precision(self) -> float:
        """Return the precision of the system."""
        return self.target_temperature_step

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(self.coordinator.last_update_success and self.coordinator.data is not None)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode for DHW."""
        return self._controller.get_dhw_hvac_mode(self.coordinator.data)

    @property
    def hvac_action(self) -> HVACAction:
        """Return current HVAC action for DHW."""
        return self._controller.get_dhw_hvac_action(self.coordinator.data)

    @property
    def native_current_temperature(self) -> float | None:
        """Return hot water temperature."""
        return self._controller.get_dhw_current_temp(self.coordinator.data)

    @property
    def native_target_temperature(self) -> float | None:
        """Return hot water setpoint."""
        return self._controller.get_dhw_target_temp(self.coordinator.data)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode for DHW."""
        await self._controller.async_set_dhw_hvac_mode(
            self.coordinator,
            hvac_mode,
            self.coordinator.data,
            write_power_fn=self._write_power,
        )
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs) -> None:
        """Set hot water target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        temperature = _round_to_step(float(temperature), self.target_temperature_step)
        await self._controller.async_set_dhw_temperature(self.coordinator, temperature)
        self.async_write_ha_state()

    async def _write_power(self, state: bool) -> None:
        """Write power switch state via the active controller."""
        await self._controller.async_write_power(self.coordinator, state)
