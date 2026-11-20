"""Switch platform for SPRSUN Heat Pump."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_SWITCH


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN switches."""
    coordinator = getattr(config_entry, "runtime_data", None) or hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for key, (address, bit, name, _) in REGISTERS_SWITCH.items():
        entities.append(
            SPRSUNSwitch(
                coordinator,
                config_entry,
                key,
                name,
                address,
                bit,
            )
        )
    
    async_add_entities(entities)


class SPRSUNSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a SPRSUN switch."""
    
    _attr_has_entity_name = True
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        bit: int,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        
        self._key = key
        self._address = address
        self._bit = bit
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        
        if key in {"antilegionella_enable", "two_three_function"}:
            self._attr_entity_category = EntityCategory.CONFIG
        
        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=config_entry.data[CONF_NAME],
            manufacturer="SPRSUN",
            model="Heat Pump",
        )
    
    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        if not self.coordinator.data:
            return False
            
        # Read current register value from cache using register-based key
        reg_key = f"_control_{self._address:04x}"
        cache_entry = self.coordinator.data.get(reg_key)
        if cache_entry is not None:
            # Handle new format (dict with value/timestamp)
            if isinstance(cache_entry, dict):
                value = int(cache_entry.get("value", 0))
            else:
                # Handle old format
                value = int(cache_entry)
        else:
            value = 0
        
        # Check if our bit is set
        return bool(value & (1 << self._bit))
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # For switches, we need to check if the REGISTER (not switch key) exists in cache
        reg_key = f"_control_{self._address:04x}"
        return bool(
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and reg_key in self.coordinator.data
        )
    
    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self.coordinator.async_write_bit(
            self._address, self._bit, True, reg_key=f"_control_{self._address:04x}"
        )
        self.async_write_ha_state()
    
    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self.coordinator.async_write_bit(
            self._address, self._bit, False, reg_key=f"_control_{self._address:04x}"
        )
        self.async_write_ha_state()
