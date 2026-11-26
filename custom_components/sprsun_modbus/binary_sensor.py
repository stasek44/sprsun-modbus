"""Binary sensor platform for SPRSUN Heat Pump."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, is_expert_writes_enabled
from .controllers import (
    BinarySensorSpec,
    build_device_info,
    extract_cache_value,
    resolve_controller,
    resolve_coordinator,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN binary sensors."""
    coordinator = resolve_coordinator(hass, config_entry, DOMAIN)
    controller = resolve_controller(coordinator)

    specs = controller.get_binary_sensors()
    if is_expert_writes_enabled(config_entry, getattr(coordinator, "config_entry", None)):
        specs = specs + controller.get_expert_binary_sensors()

    entities = [
        SPRSUNBinarySensor(
            coordinator,
            config_entry,
            spec.key,
            spec.name,
            spec=spec,
        )
        for spec in specs
    ]

    async_add_entities(entities)


class SPRSUNBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a SPRSUN binary sensor (bitfield or discrete/coil boolean)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        spec: BinarySensorSpec | None = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)

        controller = resolve_controller(coordinator)
        if spec is None:
            all_specs = controller.get_binary_sensors() + controller.get_expert_binary_sensors()
            spec = next(
                (item for item in all_specs if item.key == key),
                None,
            )

        self._key = key
        self._spec = spec
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"

        is_diagnostic = (
            spec.diagnostic
            if spec is not None
            else (key.startswith("error_") or key == "alarm_stop")
        )
        if is_diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

        if spec is not None and not spec.enabled_default:
            self._attr_entity_registry_enabled_default = False

        if spec is not None and spec.device_class:
            dc_val = getattr(BinarySensorDeviceClass, spec.device_class.upper(), None)
            if dc_val is not None:
                self._attr_device_class = dc_val

        self._attr_device_info = build_device_info(controller, config_entry)

    def _data_lookup_key(self) -> str:
        """Return coordinator cache key holding this binary sensor's value or bitfield word."""
        if self._spec is not None and self._spec.bit is not None and self._spec.source_key:
            return self._spec.source_key
        if self._spec is not None and self._spec.source_key:
            return self._spec.source_key
        return self._key

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return False

        lookup_key = self._data_lookup_key()
        if self._spec is not None and self._spec.bit is not None:
            register_value = int(extract_cache_value(self.coordinator.data, lookup_key, 0) or 0)
            state = bool(register_value & (1 << self._spec.bit))
        else:
            state = bool(extract_cache_value(self.coordinator.data, lookup_key, False))

        if self._spec is not None and self._spec.inverted:
            return not state
        return state

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        lookup_key = self._data_lookup_key()
        return bool(
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and lookup_key in self.coordinator.data
        )
