"""Unit tests for sensor.py"""
import pytest
from unittest.mock import MagicMock
from custom_components.sprsun_modbus.sensor import SPRSUNSensor
from custom_components.sprsun_modbus.const import REGISTERS_READ_ONLY, DOMAIN
from homeassistant.const import CONF_NAME


@pytest.fixture
def mock_coordinator():
    """Mock coordinator with sample data."""
    coordinator = MagicMock()
    coordinator.data = {
        'compressor_runtime': 120.0,
        'cop': 380.0,
        'inlet_temp': 23.5,
        'outlet_temp': 28.5,
        'ambient_temp': 20.0,
        'hotwater_temp': 45.0,
        'compressor_frequency': 45.0,
        'ac_voltage': 230.0,
    }
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        CONF_NAME: "Test Heat Pump",
    }
    return entry


def test_sensor_creation(mock_coordinator, mock_config_entry):
    """Test sensor entity creation."""
    address = 0x000E
    key, name, scale, unit, device_class = REGISTERS_READ_ONLY[address]
    
    sensor = SPRSUNSensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        scale=scale,
        unit=unit,
        device_class=device_class,
    )
    
    assert sensor._key == "inlet_temp"
    assert sensor._scale == 0.1
    assert sensor.name == "Test Heat Pump Inlet Water Temperature"
    assert sensor.unique_id == "test_entry_inlet_temp"


def test_sensor_native_value(mock_coordinator, mock_config_entry):
    """Test sensor returns correct value from coordinator."""
    address = 0x000E
    key, name, scale, unit, device_class = REGISTERS_READ_ONLY[address]
    
    sensor = SPRSUNSensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        scale=scale,
        unit=unit,
        device_class=device_class,
    )
    
    assert sensor.native_value == 23.5


def test_sensor_unavailable_when_no_data(mock_coordinator, mock_config_entry):
    """Test sensor returns None when key not in coordinator data."""
    address = 0x002F  # suction_pressure
    key, name, scale, unit, device_class = REGISTERS_READ_ONLY[address]
    
    sensor = SPRSUNSensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        scale=scale,
        unit=unit,
        device_class=device_class,
    )
    
    assert sensor.native_value is None


def test_sensor_available(mock_coordinator, mock_config_entry):
    """Test sensor availability based on coordinator success."""
    address = 0x000E
    key, name, scale, unit, device_class = REGISTERS_READ_ONLY[address]
    
    sensor = SPRSUNSensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        scale=scale,
        unit=unit,
        device_class=device_class,
    )
    
    assert sensor.available is True
    
    mock_coordinator.last_update_success = False
    assert sensor.available is False


def test_sensor_device_class_temperature(mock_coordinator, mock_config_entry):
    """Test temperature sensor has correct device class."""
    address = 0x000E
    key, name, scale, unit, device_class = REGISTERS_READ_ONLY[address]
    
    sensor = SPRSUNSensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        scale=scale,
        unit=unit,
        device_class=device_class,
    )
    
    assert sensor.device_class == "temperature"
    assert sensor.native_unit_of_measurement == "°C"


def test_sensor_device_class_power(mock_coordinator, mock_config_entry):
    """Test power sensor has correct device class."""
    address = 0x0017  # ac_voltage
    key, name, scale, unit, device_class = REGISTERS_READ_ONLY[address]
    
    sensor = SPRSUNSensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        scale=scale,
        unit=unit,
        device_class=device_class,
    )
    
    assert sensor.device_class == "power"
    assert sensor.native_unit_of_measurement == "W"


def test_sensor_device_info(mock_coordinator, mock_config_entry):
    """Test sensor has correct device info."""
    address = 0x000E
    key, name, scale, unit, device_class = REGISTERS_READ_ONLY[address]
    
    sensor = SPRSUNSensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        scale=scale,
        unit=unit,
        device_class=device_class,
    )
    
    device_info = sensor.device_info
    assert (DOMAIN, "test_entry") in device_info["identifiers"]
    assert device_info["manufacturer"] == "SPRSUN"
    assert device_info["model"] == "Heat Pump"
