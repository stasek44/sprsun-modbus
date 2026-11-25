"""Select platform for SPRSUN Heat Pump."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, is_expert_writes_enabled
from .controllers import (
    build_device_info,
    extract_cache_value,
    resolve_controller,
    resolve_coordinator,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SPRSUN select entities."""
    coordinator = resolve_coordinator(hass, config_entry, DOMAIN)
    controller = resolve_controller(coordinator)

    specs = controller.get_selects()
    if is_expert_writes_enabled(config_entry, getattr(coordinator, "config_entry", None)):
        specs = specs + controller.get_expert_selects()

    entities = [
        SPRSUNSelect(
            coordinator,
            config_entry,
            spec.key,
            spec.name,
            spec.address,
            spec.options,
            is_config=spec.is_config,
        )
        for spec in specs
    ]

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
        is_config: bool | None = None,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)

        self._key = key
        self._address = address
        self._options_dict = options
        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_options = list(options.values())

        config_entity = is_config if is_config is not None else (key in {"fan_mode", "pump_mode"})
        if config_entity:
            self._attr_entity_category = EntityCategory.CONFIG

        controller = resolve_controller(coordinator)
        self._attr_device_info = build_device_info(controller, config_entry)

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        value = extract_cache_value(self.coordinator.data, self._key)
        if value is not None:
            return self._options_dict.get(int(value))
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
        value = None
        for val, opt in self._options_dict.items():
            if opt == option:
                value = val
                break

        if value is None:
            _LOGGER.error("Invalid option: %s", option)
            return

        await self.coordinator.async_write_register(
            address=self._address,
            value=float(value),
            key=self._key,
            scale=1,
        )

        self.async_write_ha_state()
