"""Button platform for SPRSUN Heat Pump."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REGISTERS_BUTTON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN buttons."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    for key, (address, bit, name, description) in REGISTERS_BUTTON.items():
        entities.append(
            SPRSUNButton(
                coordinator,
                config_entry,
                key,
                name,
                address,
                bit,
                description,
            )
        )
    
    async_add_entities(entities)


class SPRSUNButton(CoordinatorEntity, ButtonEntity):
    """Representation of a SPRSUN button."""
    
    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        bit: int,
        description: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        
        self._key = key
        self._address = address
        self._bit = bit
        self._attr_name = f"{config_entry.data[CONF_NAME]} {name}"
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_entity_description = description
        
        # Device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": config_entry.data[CONF_NAME],
            "manufacturer": "SPRSUN",
            "model": "Heat Pump",
        }
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_write_bit(self._address, self._bit, True)
