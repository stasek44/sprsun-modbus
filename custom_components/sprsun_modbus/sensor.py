"""Sensor platform for SPRSUN Heat Pump."""
from __future__ import annotations

from collections.abc import Mapping

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, is_derived_sensors_enabled, is_expert_writes_enabled
from .controllers import (
    DerivedSensorSpec,
    build_device_info,
    extract_cache_value,
    resolve_controller,
    resolve_coordinator,
)
from .controllers.chico_registers import CHICO_DIAGNOSTIC_SENSOR_KEYS

DIAGNOSTIC_SENSOR_KEYS = set(CHICO_DIAGNOSTIC_SENSOR_KEYS)

_DEVICE_CLASS_MAP: dict[str, str] = {
    "temperature": "TEMPERATURE",
    "pressure": "PRESSURE",
    "power": "POWER",
    "current": "CURRENT",
    "frequency": "FREQUENCY",
    "voltage": "VOLTAGE",
    "energy": "ENERGY",
    "volume_flow_rate": "VOLUME_FLOW_RATE",
    "duration": "DURATION",
    "enum": "ENUM",
}

_MEASUREMENT_DEVICE_CLASSES = frozenset({
    "temperature",
    "pressure",
    "power",
    "current",
    "frequency",
    "voltage",
    "volume_flow_rate",
    "duration",
})


def _apply_sensor_metadata(
    entity: SensorEntity,
    device_class: str | None,
    state_class: str | None,
    diagnostic: bool,
    enabled_default: bool,
) -> None:
    """Apply shared category, visibility, device_class, and state_class attributes."""
    if not enabled_default:
        entity._attr_entity_registry_enabled_default = False

    if diagnostic:
        entity._attr_entity_category = EntityCategory.DIAGNOSTIC

    if device_class and device_class in _DEVICE_CLASS_MAP:
        dc_attr = _DEVICE_CLASS_MAP[device_class]
        dc_val = getattr(SensorDeviceClass, dc_attr, None)
        if dc_val is not None:
            entity._attr_device_class = dc_val

    if state_class == "total_increasing":
        entity._attr_state_class = SensorStateClass.TOTAL_INCREASING
    elif state_class == "total":
        entity._attr_state_class = SensorStateClass.TOTAL
    elif state_class == "none":
        pass
    elif state_class == "measurement" or (
        state_class is None and device_class in _MEASUREMENT_DEVICE_CLASSES
    ):
        entity._attr_state_class = SensorStateClass.MEASUREMENT


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN sensors."""
    coordinator = resolve_coordinator(hass, config_entry, DOMAIN)
    controller = resolve_controller(coordinator)
    fallback_entry = getattr(coordinator, "config_entry", None)

    specs = controller.get_sensors()
    if is_expert_writes_enabled(config_entry, fallback_entry):
        specs = specs + controller.get_expert_sensors()

    entities: list[SensorEntity] = [
        SPRSUNSensor(
            coordinator,
            config_entry,
            spec.key,
            spec.name,
            spec.unit,
            spec.device_class,
            state_class=spec.state_class,
            diagnostic=spec.diagnostic,
            options=spec.options,
            enabled_default=spec.enabled_default,
        )
        for spec in specs
    ]

    if is_derived_sensors_enabled(config_entry, fallback_entry):
        entities.extend(
            SPRSUNDerivedSensor(coordinator, config_entry, spec)
            for spec in controller.get_derived_sensors()
        )

    async_add_entities(entities)


class SPRSUNSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SPRSUN sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        unit: str | None,
        device_class: str | None,
        state_class: str | None = None,
        diagnostic: bool | None = None,
        options: Mapping[int, str] | None = None,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._key = key
        self._options = options
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit

        is_diagnostic = diagnostic if diagnostic is not None else (key in DIAGNOSTIC_SENSOR_KEYS)
        _apply_sensor_metadata(self, device_class, state_class, is_diagnostic, enabled_default)

        controller = resolve_controller(coordinator)
        self._attr_device_info = build_device_info(controller, config_entry)

    @property
    def native_value(self):
        """Return the state of the sensor."""
        value = extract_cache_value(self.coordinator.data, self._key)
        if value is not None and self._options is not None:
            try:
                int_value = int(value)
            except (TypeError, ValueError):
                return value
            return self._options.get(int_value, f"Unknown ({int_value})")
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._key in self.coordinator.data
        )


class SPRSUNDerivedSensor(CoordinatorEntity, SensorEntity):
    """Representation of a controller-derived/calculated virtual sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        spec: DerivedSensorSpec,
    ) -> None:
        """Initialize the derived sensor."""
        super().__init__(coordinator)

        self._spec = spec
        self._key = spec.key
        self._attr_name = spec.name
        self._attr_unique_id = f"{config_entry.entry_id}_{spec.key}"
        self._attr_native_unit_of_measurement = spec.unit

        if spec.options is not None:
            self._attr_options = list(spec.options)
            self._attr_translation_key = spec.key

        if spec.suggested_display_precision is not None:
            self._attr_suggested_display_precision = spec.suggested_display_precision

        _apply_sensor_metadata(
            self,
            spec.device_class,
            spec.state_class,
            spec.diagnostic,
            spec.enabled_default,
        )

        attrs: dict[str, str | bool] = {}
        if spec.description:
            attrs["description"] = spec.description
        if spec.formula:
            attrs["formula"] = spec.formula
        if spec.experimental:
            attrs["experimental"] = True
        if spec.disclaimer:
            attrs["disclaimer"] = spec.disclaimer
        self._static_extra_attributes = attrs

        controller = resolve_controller(coordinator)
        self._attr_device_info = build_device_info(controller, config_entry)

    @property
    def extra_state_attributes(self) -> dict[str, str | bool]:
        """Return static documentation and experimental disclaimer attributes."""
        return self._static_extra_attributes

    @property
    def native_value(self):
        """Return cached derived value or evaluate stateless fallback on demand."""
        cached = extract_cache_value(self.coordinator.data, self._key)
        if cached is not None:
            return cached
        return self._spec.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Return if derived sensor has a valid computed value."""
        return bool(
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.native_value is not None
        )
