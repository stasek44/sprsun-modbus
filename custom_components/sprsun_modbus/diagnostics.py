"""Diagnostics support for SPRSUN Heat Pump Modbus integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .controllers import extract_cache_value, resolve_controller, resolve_coordinator

TO_REDACT = {CONF_HOST}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a SPRSUN Modbus config entry."""
    coordinator = resolve_coordinator(hass, entry, DOMAIN)
    controller = resolve_controller(coordinator)
    data = getattr(coordinator, "data", None) or {}
    update_interval = getattr(coordinator, "update_interval", None)

    return {
        "entry": {
            "entry_id": entry.entry_id,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "controller": {
            "name": controller.name,
            "manufacturer": controller.manufacturer,
            "sensor_count": len(controller.get_sensors()),
            "binary_sensor_count": len(controller.get_binary_sensors()),
            "number_count": len(controller.get_numbers()),
            "select_count": len(controller.get_selects()),
            "switch_count": len(controller.get_switches()),
        },
        "coordinator": {
            "last_update_success": getattr(coordinator, "last_update_success", None),
            "rw_loaded": getattr(coordinator, "_rw_loaded", None),
            "poll_count": getattr(coordinator, "_poll_count", None),
            "consecutive_failures": getattr(coordinator, "_consecutive_failures", None),
            "current_update_interval_seconds": (
                update_interval.total_seconds() if update_interval is not None else None
            ),
        },
        "values": {
            key: extract_cache_value(data, key)
            for key in sorted(data)
        },
    }
