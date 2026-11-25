"""Number platform for SPRSUN Heat Pump."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, get_temp_step
from .controllers import (
    DataType,
    NumberSpec,
    build_device_info,
    encode_registers,
    extract_cache_value,
    resolve_controller,
    resolve_coordinator,
)
from .controllers.models import registers_per_value

PRIMARY_SETPOINTS = {"heating_setpoint", "cooling_setpoint", "hotwater_setpoint"}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN numbers."""
    coordinator = resolve_coordinator(hass, config_entry, DOMAIN)
    controller = resolve_controller(coordinator)
    temp_step = get_temp_step(config_entry, getattr(coordinator, "config_entry", None))

    entities = []
    for spec in controller.get_numbers():
        initial_step = temp_step if spec.supports_temp_step_override else spec.step
        entities.append(
            SPRSUNNumber(
                coordinator,
                config_entry,
                spec.key,
                spec.name,
                spec.address,
                spec.scale,
                spec.unit,
                spec.min_value,
                spec.max_value,
                initial_step,
                spec.device_class,
                orig_step=spec.step,
                spec=spec,
            )
        )

    async_add_entities(entities)


def _round_to_step(value: float, step: float) -> float:
    """Round value to the nearest step (e.g. 0.5 or 1.0)."""
    if step <= 0:
        return value
    return float(round(value / step + 1e-9) * step)


class SPRSUNNumber(CoordinatorEntity, NumberEntity):
    """Representation of a SPRSUN number."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        scale: float,
        unit: str | None,
        min_val: float,
        max_val: float,
        step: float,
        device_class: str | None,
        orig_step: float | None = None,
        spec: NumberSpec | None = None,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._spec = spec
        self._orig_step = orig_step if orig_step is not None else step
        self._key = key
        self._address = address
        self._scale = scale
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = step

        is_primary = spec.is_primary if spec is not None else (key in PRIMARY_SETPOINTS)
        if not is_primary:
            self._attr_entity_category = EntityCategory.CONFIG

        if device_class == "temperature":
            self._attr_device_class = NumberDeviceClass.TEMPERATURE
        else:
            self._attr_device_class = None

        controller = resolve_controller(coordinator)
        self._attr_device_info = build_device_info(controller, config_entry)

    @property
    def native_step(self) -> float:
        """Return the step for the number value."""
        supports_override = (
            self._spec.supports_temp_step_override
            if self._spec is not None
            else (
                getattr(self, "_attr_device_class", None) == NumberDeviceClass.TEMPERATURE
                and self._orig_step == 0.5
            )
        )
        if supports_override:
            return get_temp_step(self._config_entry, getattr(self.coordinator, "config_entry", None))
        return self._attr_native_step

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return extract_cache_value(self.coordinator.data, self._key)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._key in self.coordinator.data
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        value = _round_to_step(float(value), self.native_step)

        if self._spec is not None and (
            registers_per_value(self._spec.data_type) > 1
            or self._spec.data_type == DataType.FLOAT32
        ):
            registers = encode_registers(
                value,
                self._spec.data_type,
                scale=self._scale,
                word_order=self._spec.word_order,
            )
            await self.coordinator.async_write_registers(
                address=self._address,
                registers=registers,
                key=self._key,
                value=value,
            )
        else:
            await self.coordinator.async_write_register(
                address=self._address,
                value=value,
                key=self._key,
                scale=(1 / self._scale),
            )

        self.async_write_ha_state()
