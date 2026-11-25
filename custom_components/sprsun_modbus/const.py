"""Constants for the SPRSUN Heat Pump Modbus integration."""
from collections.abc import Mapping
from typing import Any

from homeassistant.const import Platform

from .controllers.chico_registers import (
    CHICO_BUTTONS,
    CHICO_CORE_BINARY_SENSORS,
    CHICO_CORE_SENSORS,
    CHICO_EXPERT_BINARY_SENSORS,
    CHICO_EXPERT_SENSORS,
    CHICO_NUMBERS,
    CHICO_SELECTS,
    CHICO_SWITCHES,
)

DOMAIN = "sprsun_modbus"

# Default values
DEFAULT_NAME = "SPRSUN Heat Pump"
DEFAULT_PORT = 502
DEFAULT_DEVICE_ADDRESS = 1
DEFAULT_SCAN_INTERVAL = 10  # seconds - balance between responsiveness and load
DEFAULT_TIMEOUT = 30  # seconds - Elfin W11 timeout (must be >= scan_interval + cycle_time)
DEFAULT_TEMP_STEP = 1.0  # °C - temperature step for target temperature setpoints (1.0°C default for compatibility)
INTER_WRITE_DELAY = 0.08  # seconds - safe turnaround delay for heat pump MCU EEPROM commit

# Configuration keys
CONF_DEVICE_ADDRESS = "device_address"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_CONTROLLER_TYPE = "controller_type"
CONF_TEMP_STEP = "temp_step"


def get_temp_step(entry: Any, fallback_entry: Any = None) -> float:
    """Extract configured temperature step from entry options or data.

    Supports MappingProxyType (used by Home Assistant ConfigEntry), standard dicts,
    and handles fallback lookup.
    """
    for e in (entry, fallback_entry):
        if e is None:
            continue
        raw_options = getattr(e, "options", None)
        raw_data = getattr(e, "data", None)
        options = raw_options if isinstance(raw_options, Mapping) else {}
        data = raw_data if isinstance(raw_data, Mapping) else {}
        if CONF_TEMP_STEP in options:
            try:
                return float(options[CONF_TEMP_STEP])
            except (ValueError, TypeError):
                pass
        if CONF_TEMP_STEP in data:
            try:
                return float(data[CONF_TEMP_STEP])
            except (ValueError, TypeError):
                pass
    return DEFAULT_TEMP_STEP


# Platforms
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.CLIMATE,
]

# Legacy CHICO register views derived from controllers.chico_registers for backward compatibility
REGISTERS_READ_ONLY = {
    spec.address: (spec.key, spec.name, spec.scale, spec.unit, spec.device_class)
    for spec in CHICO_CORE_SENSORS
}

REGISTERS_EXPERT = {
    spec.address: (spec.key, spec.name, spec.scale, spec.unit, spec.device_class)
    for spec in CHICO_EXPERT_SENSORS
}

BINARY_SENSOR_BITS = {
    spec.key: (spec.address, spec.bit, spec.name)
    for spec in CHICO_CORE_BINARY_SENSORS
    if spec.bit is not None
}

EXPERT_BINARY_SENSOR_BITS = {
    spec.key: (spec.address, spec.bit, spec.name)
    for spec in CHICO_EXPERT_BINARY_SENSORS
    if spec.bit is not None
}

REGISTERS_SWITCH = {
    spec.key: (spec.address, spec.bit, spec.name, spec.coil_address)
    for spec in CHICO_SWITCHES
    if spec.bit is not None
}

REGISTERS_BUTTON = {
    spec.key: (spec.address, spec.bit, spec.name, spec.description)
    for spec in CHICO_BUTTONS
    if spec.bit is not None
}

REGISTERS_SELECT = {
    spec.address: (spec.key, spec.name, spec.options)
    for spec in CHICO_SELECTS
}

REGISTERS_NUMBER = {
    spec.address: (
        spec.key,
        spec.name,
        spec.scale,
        spec.unit,
        spec.min_value,
        spec.max_value,
        spec.step,
        spec.device_class,
    )
    for spec in CHICO_NUMBERS
}

# Weekday mapping for antilegionella
WEEKDAY_MAP = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
}
