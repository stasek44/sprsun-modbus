"""Number platform for SPRSUN Heat Pump."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_NUMBER

PRIMARY_SETPOINTS = {"heating_setpoint", "cooling_setpoint", "hotwater_setpoint"}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN numbers."""
    coordinator = getattr(config_entry, "runtime_data", None) or hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for address, config in REGISTERS_NUMBER.items():
        key, name, scale, unit, min_val, max_val, step, device_class = config
        entities.append(
            SPRSUNNumber(
                coordinator,
                config_entry,
                key,
                name,
                address,
                scale,
                unit,
                min_val,
                max_val,
                step,
                device_class,
            )
        )
    
    async_add_entities(entities)


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
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        
        self._key = key
        self._address = address
        self._scale = scale
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = step
        
        # All non-primary setpoints are configuration entities
        if key not in PRIMARY_SETPOINTS:
            self._attr_entity_category = EntityCategory.CONFIG
        
        # Set device class
        if device_class == "temperature":
            self._attr_device_class = NumberDeviceClass.TEMPERATURE
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.data[CONF_NAME],
            manufacturer="SPRSUN",
            model="Heat Pump",
        )
    
    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data:
            return None
        cache_entry = self.coordinator.data.get(self._key)
        if cache_entry is not None:
            # Handle new format (dict with value/timestamp)
            if isinstance(cache_entry, dict):
                return cache_entry.get("value")
            # Handle old format (raw float) for backwards compatibility
            return cache_entry
        return None
    
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
        # Use coordinator's write helper (handles cache + timestamp automatically)
        await self.coordinator.async_write_register(
            address=self._address,
            value=value,
            key=self._key,
            scale=(1 / self._scale)  # Convert scale factor for coordinator
        )
        
        # Trigger UI update immediately
        self.async_write_ha_state()
