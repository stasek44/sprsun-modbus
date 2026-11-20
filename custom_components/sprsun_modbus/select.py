"""Select platform for SPRSUN Heat Pump."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_SELECT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN select entities."""
    coordinator = getattr(config_entry, "runtime_data", None) or hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for address, (key, name, options) in REGISTERS_SELECT.items():
        entities.append(
            SPRSUNSelect(
                coordinator,
                config_entry,
                key,
                name,
                address,
                options,
            )
        )
    
    async_add_entities(entities)


class SPRSUNSelect(CoordinatorEntity, SelectEntity):
    """Representation of a SPRSUN select entity."""
    
    _attr_has_entity_name = True
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        options: dict[int, str],
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        
        self._key = key
        self._address = address
        self._options_dict = options
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_options = list(options.values())
        
        if key in {"fan_mode", "pump_mode"}:
            self._attr_entity_category = EntityCategory.CONFIG
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.data[CONF_NAME],
            manufacturer="SPRSUN",
            model="Heat Pump",
        )
    
    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        if not self.coordinator.data:
            return None
        cache_entry = self.coordinator.data.get(self._key)
        if cache_entry is not None:
            # Handle new format (dict with value/timestamp)
            if isinstance(cache_entry, dict):
                value = cache_entry.get("value")
            else:
                # Handle old format
                value = cache_entry
            
            if value is not None:
                # Convert scaled value back to raw integer
                raw_value = int(value)
                return self._options_dict.get(raw_value)
        return None
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._key in self.coordinator.data
        )
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # Find the value for this option
        value = None
        for val, opt in self._options_dict.items():
            if opt == option:
                value = val
                break
        
        if value is None:
            _LOGGER.error("Invalid option: %s", option)
            return
        
        # Use coordinator's write helper
        await self.coordinator.async_write_register(
            address=self._address,
            value=float(value),
            key=self._key,
            scale=1  # No scaling for select entities
        )
        
        # Trigger UI update immediately
        self.async_write_ha_state()
