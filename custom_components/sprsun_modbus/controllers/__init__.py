"""Controller abstraction and registry for heat pump controller drivers."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import ControllerBase
from .chico import ChicoController
from .models import (
    BinarySensorSpec,
    ButtonSpec,
    ClimateCapabilities,
    DataType,
    ModbusBatchSpec,
    NumberSpec,
    RegisterSpace,
    SelectSpec,
    SensorSpec,
    SwitchSpec,
    WordOrder,
    decode_registers,
    encode_registers,
    extract_cache_value,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.helpers.device_registry import DeviceInfo
    from pymodbus.client import ModbusTcpClient

__all__ = [
    "BinarySensorSpec",
    "ButtonSpec",
    "ChicoController",
    "ClimateCapabilities",
    "CONTROLLER_REGISTRY",
    "ControllerBase",
    "DataType",
    "ModbusBatchSpec",
    "NumberSpec",
    "RegisterSpace",
    "SelectSpec",
    "SensorSpec",
    "SwitchSpec",
    "WordOrder",
    "build_device_info",
    "decode_registers",
    "detect_controller_type",
    "encode_registers",
    "extract_cache_value",
    "get_controller",
    "get_supported_controllers",
    "resolve_controller",
    "resolve_coordinator",
]

# Registry of supported controller drivers (detection runs in insertion order)
CONTROLLER_REGISTRY: dict[str, type[ControllerBase]] = {
    "chico": ChicoController,
}


def get_supported_controllers() -> tuple[str, ...]:
    """Return tuple of registered controller type identifiers."""
    return tuple(CONTROLLER_REGISTRY.keys())


def detect_controller_type(
    client: ModbusTcpClient,
    device_address: int,
) -> str | None:
    """Auto-detect controller type by querying registered controller drivers."""
    for controller_key, controller_cls in CONTROLLER_REGISTRY.items():
        try:
            if controller_cls.detect(client, device_address):
                return controller_key
        except Exception:
            continue

    return None


def get_controller(controller_type: str = "chico") -> ControllerBase:
    """Instantiate controller driver by type identifier."""
    controller_class = CONTROLLER_REGISTRY.get(controller_type.lower())
    if controller_class is None:
        raise ValueError(f"Unknown controller type: {controller_type}")

    return controller_class()


def resolve_controller(coordinator: Any) -> ControllerBase:
    """Return coordinator's ControllerBase instance, falling back to CHICO for unit test mocks."""
    controller = getattr(coordinator, "controller", None)
    if isinstance(controller, ControllerBase):
        return controller
    return ChicoController()


def resolve_coordinator(hass: Any, config_entry: Any, domain: str) -> Any:
    """Resolve coordinator from runtime_data or hass.data cleanly."""
    runtime_data = getattr(config_entry, "runtime_data", None)
    if runtime_data is not None and isinstance(getattr(runtime_data, "controller", None), ControllerBase):
        return runtime_data
    domain_data = getattr(hass, "data", {}).get(domain, {})
    if config_entry.entry_id in domain_data:
        return domain_data[config_entry.entry_id]
    return runtime_data


def build_device_info(controller: ControllerBase, config_entry: ConfigEntry) -> DeviceInfo:
    """Build Home Assistant DeviceInfo from controller metadata and config entry."""
    from homeassistant.const import CONF_NAME
    from homeassistant.helpers.device_registry import DeviceInfo

    raw_info = controller.get_device_info(config_entry.entry_id)
    entry_data = getattr(config_entry, "data", None) or {}
    return DeviceInfo(
        identifiers=raw_info.get("identifiers", {("sprsun_modbus", config_entry.entry_id)}),
        name=entry_data.get(CONF_NAME, raw_info.get("name", "SPRSUN Heat Pump")),
        manufacturer=raw_info.get("manufacturer", "SPRSUN"),
        model=raw_info.get("model", "Heat Pump"),
    )
