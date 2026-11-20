"""Mock Home Assistant and dependencies when running in minimal environments.

This allows unit tests to execute cleanly both in full environments
(with Home Assistant and pymodbus installed) and minimal/offline dev environments.
"""
from __future__ import annotations

import sys
from enum import Enum, IntFlag
from unittest.mock import MagicMock


class StrEnum(str, Enum):
    """String enum for Python compatibility."""
    def __str__(self) -> str:
        return self.value


def setup_mocks():
    """Set up mocks for Home Assistant and external modules if not present."""
    # 1. Voluptuous mock
    if "voluptuous" not in sys.modules:
        try:
            import voluptuous
        except ImportError:
            class MockSchema:
                def __init__(self, schema):
                    self.schema = schema
                def __call__(self, data):
                    return data

            class MockVol:
                Schema = MockSchema
                @staticmethod
                def Required(key, default=None):
                    return key
                @staticmethod
                def Optional(key, default=None):
                    return key
                @staticmethod
                def All(*args):
                    return lambda v: v
                @staticmethod
                def Coerce(t):
                    return t
                @staticmethod
                def Range(min=None, max=None):
                    return lambda v: v

            sys.modules["voluptuous"] = MockVol()

    # 2. Pymodbus mock
    if "pymodbus" not in sys.modules:
        try:
            import pymodbus
        except ImportError:
            pm = MagicMock()
            class ModbusException(Exception):
                pass
            class ModbusTcpClient:
                def __init__(self, host=None, port=502, *args, **kwargs):
                    self.host = host
                    self.port = port
                    self.connected = False
                def connect(self):
                    self.connected = True
                    return True
                def close(self):
                    self.connected = False
                def read_holding_registers(self, *args, **kwargs):
                    return MagicMock(isError=lambda: False, registers=[])
                def write_register(self, *args, **kwargs):
                    return MagicMock(isError=lambda: False)

            pm.exceptions.ModbusException = ModbusException
            pm.client.ModbusTcpClient = ModbusTcpClient
            sys.modules["pymodbus"] = pm
            sys.modules["pymodbus.client"] = pm.client
            sys.modules["pymodbus.exceptions"] = pm.exceptions

    # 3. Home Assistant mock
    if "homeassistant" not in sys.modules:
        try:
            import homeassistant
        except ImportError:
            ha = MagicMock()
            sys.modules["homeassistant"] = ha

            # Core
            class MockHomeAssistant:
                def __init__(self):
                    self.data = {}
                    self.config_entries = MagicMock()
                async def async_add_executor_job(self, func, *args, **kwargs):
                    return func(*args, **kwargs)

            core = MagicMock()
            core.HomeAssistant = MockHomeAssistant
            core.callback = lambda f: f
            sys.modules["homeassistant.core"] = core

            # Constants
            class Platform(StrEnum):
                SENSOR = "sensor"
                BINARY_SENSOR = "binary_sensor"
                CLIMATE = "climate"
                NUMBER = "number"
                SELECT = "select"
                SWITCH = "switch"
                BUTTON = "button"

            class EntityCategory(StrEnum):
                CONFIG = "config"
                DIAGNOSTIC = "diagnostic"

            class UnitOfTemperature(StrEnum):
                CELSIUS = "°C"
                FAHRENHEIT = "°F"

            class UnitOfPressure(StrEnum):
                BAR = "bar"
                PSI = "psi"

            class UnitOfElectricPotential(StrEnum):
                VOLT = "V"

            class UnitOfElectricCurrent(StrEnum):
                AMPERE = "A"

            class UnitOfFrequency(StrEnum):
                HERTZ = "Hz"

            class UnitOfPower(StrEnum):
                WATT = "W"
                KILOWATT = "kW"

            class UnitOfTime(StrEnum):
                HOURS = "h"
                MINUTES = "min"
                SECONDS = "s"

            ha_const = MagicMock()
            ha_const.CONF_HOST = "host"
            ha_const.CONF_PORT = "port"
            ha_const.CONF_NAME = "name"
            ha_const.ATTR_TEMPERATURE = "temperature"
            ha_const.Platform = Platform
            ha_const.EntityCategory = EntityCategory
            ha_const.UnitOfTemperature = UnitOfTemperature
            ha_const.UnitOfPressure = UnitOfPressure
            ha_const.UnitOfElectricPotential = UnitOfElectricPotential
            ha_const.UnitOfElectricCurrent = UnitOfElectricCurrent
            ha_const.UnitOfFrequency = UnitOfFrequency
            ha_const.UnitOfPower = UnitOfPower
            ha_const.UnitOfTime = UnitOfTime
            sys.modules["homeassistant.const"] = ha_const

            # Base Entity & Coordinator
            class MockEntity:
                def __init__(self, *args, **kwargs):
                    if not hasattr(self, "_attr_name"):
                        self._attr_name = None
                    if not hasattr(self, "_attr_has_entity_name"):
                        self._attr_has_entity_name = False
                    if not hasattr(self, "_attr_unique_id"):
                        self._attr_unique_id = None
                    if not hasattr(self, "_attr_device_info"):
                        self._attr_device_info = None
                    if not hasattr(self, "_attr_native_unit_of_measurement"):
                        self._attr_native_unit_of_measurement = None
                    if not hasattr(self, "_attr_device_class"):
                        self._attr_device_class = None
                    if not hasattr(self, "_attr_state_class"):
                        self._attr_state_class = None
                    if not hasattr(self, "_attr_entity_category"):
                        self._attr_entity_category = None
                    if not hasattr(self, "_attr_entity_description"):
                        self._attr_entity_description = None

                @property
                def name(self):
                    return getattr(self, "_attr_name", None)

                @property
                def has_entity_name(self):
                    return getattr(self, "_attr_has_entity_name", False)

                @property
                def unique_id(self):
                    return getattr(self, "_attr_unique_id", None)

                @property
                def device_info(self):
                    return getattr(self, "_attr_device_info", None)

                @property
                def entity_category(self):
                    return getattr(self, "_attr_entity_category", None)

                @property
                def entity_description(self):
                    return getattr(self, "_attr_entity_description", None) or getattr(self, "_entity_description", None)

                @entity_description.setter
                def entity_description(self, value):
                    self._entity_description = value

                @property
                def native_unit_of_measurement(self):
                    return getattr(self, "_attr_native_unit_of_measurement", None)

                @property
                def device_class(self):
                    return getattr(self, "_attr_device_class", None)

                @property
                def state_class(self):
                    return getattr(self, "_attr_state_class", None)

                @property
                def options(self):
                    return getattr(self, "_attr_options", [])

                def async_write_ha_state(self):
                    pass

            class MockCoordinatorEntity(MockEntity):
                def __init__(self, coordinator):
                    super().__init__()
                    self.coordinator = coordinator

            class MockDataUpdateCoordinator:
                def __init__(self, hass, logger, name, update_interval=None):
                    self.hass = hass
                    self.logger = logger
                    self.name = name
                    self.update_interval = update_interval
                    self.data = {}
                    self.last_update_success = True

                async def async_config_entry_first_refresh(self):
                    pass

                def async_set_updated_data(self, data):
                    self.data = data

                async def async_shutdown(self):
                    pass

            class UpdateFailed(Exception):
                pass

            helpers = MagicMock()
            update_coord = MagicMock()
            update_coord.CoordinatorEntity = MockCoordinatorEntity
            update_coord.DataUpdateCoordinator = MockDataUpdateCoordinator
            update_coord.UpdateFailed = UpdateFailed
            helpers.update_coordinator = update_coord

            class DeviceInfo(dict):
                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    self.__dict__ = self

            dev_reg = MagicMock()
            dev_reg.DeviceInfo = DeviceInfo
            helpers.device_registry = dev_reg
            sys.modules["homeassistant.helpers.device_registry"] = dev_reg

            sys.modules["homeassistant.helpers"] = helpers
            sys.modules["homeassistant.helpers.update_coordinator"] = update_coord
            sys.modules["homeassistant.helpers.entity_platform"] = MagicMock()

            # Config validation
            cv = MagicMock()
            cv.port = lambda v: v
            helpers.config_validation = cv
            sys.modules["homeassistant.helpers.config_validation"] = cv

            # Config entries
            class MockConfigFlow:
                def __init_subclass__(cls, domain=None, **kwargs):
                    super().__init_subclass__(**kwargs)
                    cls.domain = domain
                def async_show_form(self, step_id, data_schema, errors=None, description_placeholders=None):
                    return {
                        "type": "form",
                        "step_id": step_id,
                        "data_schema": data_schema,
                        "errors": errors or {},
                    }
                def async_create_entry(self, title, data):
                    return {"type": "create_entry", "title": title, "data": data}
                async def async_set_unique_id(self, unique_id):
                    self.unique_id = unique_id
                def _abort_if_unique_id_configured(self):
                    pass

            class MockOptionsFlow:
                def __init__(self, config_entry=None):
                    self.config_entry = config_entry
                def async_show_form(self, step_id, data_schema, description_placeholders=None):
                    return {"type": "form", "step_id": step_id, "data_schema": data_schema}
                def async_create_entry(self, title, data):
                    return {"type": "create_entry", "title": title, "data": data}

            cfg = MagicMock()
            cfg.ConfigEntry = MagicMock
            cfg.ConfigFlow = MockConfigFlow
            cfg.OptionsFlow = MockOptionsFlow
            cfg.ConfigFlowResult = dict
            sys.modules["homeassistant.config_entries"] = cfg

            # Data entry flow
            class FlowResultType(StrEnum):
                FORM = "form"
                CREATE_ENTRY = "create_entry"
                ABORT = "abort"
            data_flow = MagicMock()
            data_flow.FlowResultType = FlowResultType
            sys.modules["homeassistant.data_entry_flow"] = data_flow

            # Components
            sys.modules["homeassistant.components"] = MagicMock()

            # Sensor
            class SensorDeviceClass(StrEnum):
                TEMPERATURE = "temperature"
                PRESSURE = "pressure"
                POWER = "power"
                CURRENT = "current"
                FREQUENCY = "frequency"
                VOLTAGE = "voltage"

            class SensorStateClass(StrEnum):
                MEASUREMENT = "measurement"
                TOTAL = "total"
                TOTAL_INCREASING = "total_increasing"

            sensor_mod = MagicMock()
            sensor_mod.SensorEntity = MockEntity
            sensor_mod.SensorDeviceClass = SensorDeviceClass
            sensor_mod.SensorStateClass = SensorStateClass
            sys.modules["homeassistant.components.sensor"] = sensor_mod

            # Binary sensor
            class BinarySensorDeviceClass(StrEnum):
                PROBLEM = "problem"
                RUNNING = "running"
            binary_sensor_mod = MagicMock()
            binary_sensor_mod.BinarySensorEntity = MockEntity
            binary_sensor_mod.BinarySensorDeviceClass = BinarySensorDeviceClass
            sys.modules["homeassistant.components.binary_sensor"] = binary_sensor_mod

            # Climate
            class ClimateEntityFeature(IntFlag):
                TARGET_TEMPERATURE = 1
                FAN_MODE = 8
                PRESET_MODE = 16

            class HVACMode(StrEnum):
                OFF = "off"
                HEAT = "heat"
                COOL = "cool"
                HEAT_COOL = "heat_cool"

            class HVACAction(StrEnum):
                OFF = "off"
                HEATING = "heating"
                COOLING = "cooling"
                IDLE = "idle"

            climate_mod = MagicMock()
            climate_mod.ClimateEntity = MockEntity
            climate_mod.ClimateEntityFeature = ClimateEntityFeature
            climate_mod.HVACMode = HVACMode
            climate_mod.HVACAction = HVACAction
            climate_mod.PRESET_NONE = "none"
            climate_mod.PRESET_ECO = "eco"
            climate_mod.PRESET_BOOST = "boost"
            sys.modules["homeassistant.components.climate"] = climate_mod

            # Number
            class NumberDeviceClass(StrEnum):
                TEMPERATURE = "temperature"
            number_mod = MagicMock()
            number_mod.NumberEntity = MockEntity
            number_mod.NumberDeviceClass = NumberDeviceClass
            sys.modules["homeassistant.components.number"] = number_mod

            # Select
            select_mod = MagicMock()
            select_mod.SelectEntity = MockEntity
            sys.modules["homeassistant.components.select"] = select_mod

            # Switch
            switch_mod = MagicMock()
            switch_mod.SwitchEntity = MockEntity
            sys.modules["homeassistant.components.switch"] = switch_mod

            # Button
            class ButtonEntityDescription:
                def __init__(self, key, name=None, translation_key=None, **kwargs):
                    self.key = key
                    self.name = name
                    self.translation_key = translation_key
                    for k, v in kwargs.items():
                        setattr(self, k, v)

            button_mod = MagicMock()
            button_mod.ButtonEntity = MockEntity
            button_mod.ButtonEntityDescription = ButtonEntityDescription
            sys.modules["homeassistant.components.button"] = button_mod

            # Attach submodules to parent package so "from homeassistant import config_entries" works
            ha.config_entries = cfg
            ha.const = ha_const
            ha.core = core
            ha.helpers = helpers
            ha.data_entry_flow = data_flow
            ha.components = sys.modules["homeassistant.components"]
