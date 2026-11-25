"""Button platform for SPRSUN Heat Pump."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .controllers import (
    RegisterSpace,
    build_device_info,
    resolve_controller,
    resolve_coordinator,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN buttons."""
    coordinator = resolve_coordinator(hass, config_entry, DOMAIN)
    controller = resolve_controller(coordinator)

    entities = [
        SPRSUNButton(
            coordinator,
            config_entry,
            spec.key,
            spec.name,
            spec.address,
            spec.bit,
            spec.description,
            space=spec.space,
            write_value=spec.write_value,
            diagnostic=spec.diagnostic,
        )
        for spec in controller.get_buttons()
    ]

    async_add_entities(entities)


class SPRSUNButton(CoordinatorEntity, ButtonEntity):
    """Representation of a SPRSUN momentary action button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        bit: int | None,
        description: str,
        space: RegisterSpace = RegisterSpace.HOLDING_REGISTER,
        write_value: bool | int = True,
        diagnostic: bool = True,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)

        self._key = key
        self._address = address
        self._bit = bit
        self._space = space
        self._write_value = write_value
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        if diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

        self.entity_description = ButtonEntityDescription(
            key=key,
            translation_key=key,
        )

        controller = resolve_controller(coordinator)
        self._attr_device_info = build_device_info(controller, config_entry)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(self.coordinator.last_update_success and self.coordinator.data is not None)

    async def async_press(self) -> None:
        """Handle the button press."""
        if self._space == RegisterSpace.COIL:
            await self.coordinator.async_write_coil(self._address, bool(self._write_value), key=None)
        elif self._bit is not None:
            await self.coordinator.async_write_bit(self._address, self._bit, bool(self._write_value))
        else:
            await self.coordinator.async_write_register(
                self._address, float(self._write_value), key=self._key, scale=1
            )
