"""Built-in Lovelace dashboard strategy registration and context API."""
from __future__ import annotations

import inspect
import logging
from pathlib import Path
import re
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CONTROLLER_TYPE,
    DOMAIN,
    is_derived_sensors_enabled,
    is_expert_writes_enabled,
)
from .controllers import ControllerBase, get_controller

_LOGGER = logging.getLogger(__name__)

STATIC_URL_PATH = f"/api/{DOMAIN}/static"
STRATEGY_JS_FILENAME = "sprsun_dashboard_strategy.js"
_FRONTEND_DIR = Path(__file__).parent / "frontend"
_FRONTEND_REGISTERED_KEY = f"{DOMAIN}_frontend_registered"
_WS_REGISTERED_KEY = f"{DOMAIN}_ws_registered"
_DEFAULT_DEVICE_PREFIX = "sprsun_heat_pump"


def _slugify(value: str) -> str:
    """Convert an entity/device label into a Home Assistant object_id slug."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _collect_controller_specs(controller: ControllerBase) -> list[tuple[str, str, str]]:
    """Collect (domain, key, name) tuples for all specs exposed by a controller."""
    specs: list[tuple[str, str, str]] = []
    groups = (
        ("sensor", controller.get_sensors()),
        ("sensor", controller.get_expert_sensors()),
        ("sensor", controller.get_derived_sensors()),
        ("binary_sensor", controller.get_binary_sensors()),
        ("binary_sensor", controller.get_expert_binary_sensors()),
        ("number", controller.get_numbers()),
        ("number", controller.get_expert_numbers()),
        ("select", controller.get_selects()),
        ("select", controller.get_expert_selects()),
        ("switch", controller.get_switches()),
        ("switch", controller.get_expert_switches()),
        ("button", controller.get_buttons()),
    )
    for domain, items in groups:
        for item in items:
            specs.append((domain, item.key, item.name))

    caps = controller.get_space_climate_capabilities()
    if caps.enabled:
        specs.append(("climate", "climate", "Heating/Cooling"))
    if caps.supports_dhw:
        specs.append(("climate", "dhw_climate", "DHW"))
    return specs


def _infer_device_prefix(
    reg_entries: list[Any],
    entry_id: str,
    fallback_title: str,
) -> str:
    """Infer entity_id device prefix from registered entities or entry title."""
    unique_prefix = f"{entry_id}_"
    probes = (
        ("sensor", "inlet_temp", "_inlet_water_temperature"),
        ("switch", "power", "_power"),
        ("number", "heating_setpoint", "_heating_setpoint"),
    )
    by_identity = {
        (getattr(item, "domain", None), getattr(item, "unique_id", None)): getattr(
            item, "entity_id", ""
        )
        for item in reg_entries
    }
    for domain, key, expected_suffix in probes:
        entity_id = by_identity.get((domain, f"{unique_prefix}{key}"))
        if isinstance(entity_id, str) and entity_id.startswith(f"{domain}."):
            object_id = entity_id.split(".", 1)[1]
            if object_id.endswith(expected_suffix):
                prefix = object_id[: -len(expected_suffix)]
                if prefix:
                    return prefix

    slug = _slugify(fallback_title)
    return slug or _DEFAULT_DEVICE_PREFIX


def _resolve_controller_for_entry(
    hass: HomeAssistant,
    entry: Any,
    controller_type: str,
) -> ControllerBase:
    """Resolve active ControllerBase instance from coordinator or registry."""
    domain_data = hass.data.get(DOMAIN, {}) if isinstance(hass.data, dict) else {}
    coordinator = domain_data.get(entry.entry_id) if isinstance(domain_data, dict) else None
    controller = getattr(coordinator, "controller", None)
    if isinstance(controller, ControllerBase):
        return controller
    return get_controller(controller_type)


def build_dashboard_context(
    hass: HomeAssistant,
    entry_id: str | None = None,
) -> dict[str, Any]:
    """Build entity mapping and controller context for the Lovelace strategy."""
    entries_api = getattr(hass, "config_entries", None)
    raw_entries = entries_api.async_entries(DOMAIN) if entries_api else []
    config_entries = list(raw_entries) if isinstance(raw_entries, (list, tuple)) else []

    entries_summary = [
        {
            "entry_id": item.entry_id,
            "title": getattr(item, "title", None) or "SPRSUN Heat Pump",
            "controller_type": str(
                item.options.get(
                    CONF_CONTROLLER_TYPE,
                    item.data.get(CONF_CONTROLLER_TYPE, "chico"),
                )
            ).lower(),
        }
        for item in config_entries
    ]

    target_entry = None
    if entry_id:
        target_entry = next(
            (item for item in config_entries if item.entry_id == entry_id),
            None,
        )
    if target_entry is None and config_entries:
        target_entry = config_entries[0]

    if target_entry is None:
        return {
            "entry_id": None,
            "title": "SPRSUN Heat Pump",
            "controller_type": "chico",
            "enable_derived_sensors": False,
            "enable_expert_writes": False,
            "entities": {},
            "entries": [],
        }

    controller_type = str(
        target_entry.options.get(
            CONF_CONTROLLER_TYPE,
            target_entry.data.get(CONF_CONTROLLER_TYPE, "chico"),
        )
    ).lower()
    title = getattr(target_entry, "title", None) or "SPRSUN Heat Pump"
    controller = _resolve_controller_for_entry(hass, target_entry, controller_type)

    reg_entries: list[Any] = []
    try:
        from homeassistant.helpers import entity_registry as er

        ent_reg = er.async_get(hass)
        found = er.async_entries_for_config_entry(ent_reg, target_entry.entry_id)
        if isinstance(found, (list, tuple)):
            reg_entries = list(found)
    except Exception:
        reg_entries = []

    device_prefix = _infer_device_prefix(reg_entries, target_entry.entry_id, title)
    entities: dict[str, str] = {
        f"{domain}:{key}": f"{domain}.{device_prefix}_{_slugify(name)}"
        for domain, key, name in _collect_controller_specs(controller)
    }

    unique_prefix = f"{target_entry.entry_id}_"
    for reg_entry in reg_entries:
        uid = getattr(reg_entry, "unique_id", None)
        domain = getattr(reg_entry, "domain", None)
        entity_id = getattr(reg_entry, "entity_id", None)
        if (
            isinstance(uid, str)
            and uid.startswith(unique_prefix)
            and isinstance(domain, str)
            and isinstance(entity_id, str)
        ):
            key = uid[len(unique_prefix) :]
            entities[f"{domain}:{key}"] = entity_id

    return {
        "entry_id": target_entry.entry_id,
        "title": title,
        "controller_type": controller_type,
        "enable_derived_sensors": is_derived_sensors_enabled(target_entry),
        "enable_expert_writes": is_expert_writes_enabled(target_entry),
        "entities": entities,
        "entries": entries_summary,
    }


async def _register_static_path(hass: HomeAssistant) -> bool:
    """Serve frontend strategy assets via Home Assistant HTTP server."""
    http_srv = getattr(hass, "http", None)
    if http_srv is None or not _FRONTEND_DIR.is_dir():
        return False

    try:
        from homeassistant.components.http import StaticPathConfig
    except Exception:
        StaticPathConfig = None

    if hasattr(http_srv, "async_register_static_paths") and StaticPathConfig is not None:
        res = http_srv.async_register_static_paths(
            [
                StaticPathConfig(
                    url_path=STATIC_URL_PATH,
                    path=str(_FRONTEND_DIR),
                    cache_headers=False,
                )
            ]
        )
        if inspect.isawaitable(res):
            await res
        return True

    if hasattr(http_srv, "register_static_path"):
        http_srv.register_static_path(
            STATIC_URL_PATH,
            str(_FRONTEND_DIR),
            cache_headers=False,
        )
        return True

    return False


async def _register_lovelace_resource(hass: HomeAssistant, js_url: str) -> None:
    """Register strategy module as a Lovelace storage resource when available."""
    lovelace_data = hass.data.get("lovelace") if isinstance(hass.data, dict) else None
    resources = getattr(lovelace_data, "resources", None)
    if resources is None or not hasattr(resources, "async_create_item"):
        return
    if not getattr(resources, "loaded", True) and hasattr(resources, "async_load"):
        res = resources.async_load()
        if inspect.isawaitable(res):
            await res

    base_path = js_url.split("?", 1)[0]
    existing = resources.async_items() if hasattr(resources, "async_items") else []
    for item in existing:
        url = item.get("url", "") if isinstance(item, dict) else ""
        if url == js_url:
            return
        if url.split("?", 1)[0] == base_path and hasattr(resources, "async_update_item"):
            item_id = item.get("id")
            if item_id is not None:
                res = resources.async_update_item(item_id, {"url": js_url})
                if inspect.isawaitable(res):
                    await res
                return

    res = resources.async_create_item({"res_type": "module", "url": js_url})
    if inspect.isawaitable(res):
        await res


def _register_websocket_commands(hass: HomeAssistant) -> None:
    """Register WebSocket commands used by the Lovelace dashboard strategy."""
    if not isinstance(hass.data, dict) or hass.data.get(_WS_REGISTERED_KEY):
        return

    try:
        from homeassistant.components import websocket_api
    except Exception:
        return

    register_cmd = getattr(websocket_api, "async_register_command", None)
    if not callable(register_cmd):
        return

    schema = {
        "type": f"{DOMAIN}/get_dashboard_context",
        vol.Optional("entry_id"): str,
    }

    def _ws_handler(
        hass_inner: HomeAssistant,
        connection: Any,
        msg: dict[str, Any],
    ) -> None:
        context = build_dashboard_context(hass_inner, msg.get("entry_id"))
        connection.send_result(msg["id"], context)

    cmd_decorator = getattr(websocket_api, "websocket_command", None)
    if callable(cmd_decorator):
        decorated = cmd_decorator(schema)(_ws_handler)
        if callable(decorated):
            _ws_handler = decorated

    register_cmd(hass, _ws_handler)
    hass.data[_WS_REGISTERED_KEY] = True


async def async_register_dashboard(hass: HomeAssistant, version: str = "") -> None:
    """Idempotently register frontend static assets, strategy module, and WS endpoint."""
    if not isinstance(hass.data, dict):
        return

    _register_websocket_commands(hass)

    if hass.data.get(_FRONTEND_REGISTERED_KEY):
        return

    if not await _register_static_path(hass):
        return

    suffix = f"?v={version}" if version else ""
    js_url = f"{STATIC_URL_PATH}/{STRATEGY_JS_FILENAME}{suffix}"

    try:
        from homeassistant.components.frontend import add_extra_js_url

        if callable(add_extra_js_url):
            add_extra_js_url(hass, js_url)
    except Exception as err:
        _LOGGER.debug("Failed to register extra JS URL %s: %s", js_url, err)

    try:
        await _register_lovelace_resource(hass, js_url)
    except Exception as err:
        _LOGGER.debug("Skipping Lovelace storage resource registration: %s", err)

    hass.data[_FRONTEND_REGISTERED_KEY] = True
