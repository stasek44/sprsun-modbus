"""Switch platform for SPRSUN Heat Pump."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .controllers import (
    RegisterSpace,
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
    """Set up SPRSUN switches."""
    coordinator = resolve_coordinator(hass, config_entry, DOMAIN)
    controller = resolve_controller(coordinator)

    entities = [
        SPRSUNSwitch(
            coordinator,
            config_entry,
            spec.key,
            spec.name,
            spec.address,
            spec.bit,
            space=spec.space,
            cache_key=spec.cache_key,
            is_config=spec.is_config,
            inverted=spec.inverted,
        )
        for spec in controller.get_switches()
    ]

    async_add_entities(entities)


class SPRSUNSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a SPRSUN switch (bitfield holding register or Modbus coil)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        key: str,
        name: str,
        address: int,
        bit: int | None,
        space: RegisterSpace = RegisterSpace.HOLDING_REGISTER,
        cache_key: str | None = None,
        is_config: bool | None = None,
        inverted: bool = False,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._key = key
        self._address = address
        self._bit = bit
        self._space = space
        self._inverted = inverted
        if cache_key is not None:
            self._cache_key = cache_key
        elif space == RegisterSpace.COIL or bit is None:
            self._cache_key = key
        else:
            self._cache_key = f"_control_{address:04x}"

        self._attr_name = name
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"

        config_entity = (
            is_config
            if is_config is not None
            else (key in {"antilegionella_enable", "two_three_function"})
        )
        if config_entity:
            self._attr_entity_category = EntityCategory.CONFIG

        controller = resolve_controller(coordinator)
        self._attr_device_info = build_device_info(controller, config_entry)

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        if not self.coordinator.data:
            return False

        if self._space == RegisterSpace.COIL or self._bit is None:
            state = bool(extract_cache_value(self.coordinator.data, self._cache_key, False))
        else:
            value = int(extract_cache_value(self.coordinator.data, self._cache_key, 0) or 0)
            state = bool(value & (1 << self._bit))

        return (not state) if self._inverted else state

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return bool(
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._cache_key in self.coordinator.data
        )

    async def _async_set_state(self, state: bool) -> None:
        """Write target switch state to coil or holding register bitfield."""
        hw_state = (not state) if self._inverted else state
        if self._space == RegisterSpace.COIL or self._bit is None:
            await self.coordinator.async_write_coil(
                self._address,
                hw_state,
                key=self._cache_key,
            )
        else:
            await self.coordinator.async_write_bit(
                self._address,
                self._bit,
                hw_state,
                reg_key=self._cache_key,
            )
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self._async_set_state(False)
