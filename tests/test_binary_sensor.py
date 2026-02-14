"""Unit tests for binary_sensor.py"""
import pytest
from unittest.mock import MagicMock
from custom_components.sprsun_modbus.binary_sensor import SPRSUNBinarySensor
from custom_components.sprsun_modbus.const import BINARY_SENSOR_BITS, DOMAIN
from homeassistant.const import CONF_NAME


@pytest.fixture
def mock_coordinator():
    """Mock coordinator with working status register."""
    coordinator = MagicMock()
    # Simulate register 0x0003 = 0b00110011
    # bit 0: ON (hotwater_demand)
    # bit 1: ON (heating_demand)
    # bit 4: ON (antilegionella)
    # bit 5: ON (cooling_demand)
    coordinator.data = {
        'working_status_register': 0b00110011,
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


def test_binary_sensor_creation(mock_coordinator, mock_config_entry):
    """Test binary sensor entity creation."""
    key = "hotwater_demand"
    register, bit, name = BINARY_SENSOR_BITS[key]
    
    sensor = SPRSUNBinarySensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        bit=bit,
    )
    
    assert sensor._key == "hotwater_demand"
    assert sensor._bit == 0
    assert sensor.name == "Test Heat Pump Hot Water Demand"


def test_binary_sensor_is_on_bit_0(mock_coordinator, mock_config_entry):
    """Test binary sensor reads bit 0 correctly."""
    key = "hotwater_demand"
    register, bit, name = BINARY_SENSOR_BITS[key]
    
    sensor = SPRSUNBinarySensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        bit=bit,
    )
    
    # bit 0 is ON in 0b00110011
    assert sensor.is_on is True


def test_binary_sensor_is_on_bit_1(mock_coordinator, mock_config_entry):
    """Test binary sensor reads bit 1 correctly."""
    key = "heating_demand"
    register, bit, name = BINARY_SENSOR_BITS[key]
    
    sensor = SPRSUNBinarySensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        bit=bit,
    )
    
    # bit 1 is ON in 0b00110011
    assert sensor.is_on is True


def test_binary_sensor_is_on_bit_5(mock_coordinator, mock_config_entry):
    """Test binary sensor reads bit 5 correctly."""
    key = "cooling_demand"
    register, bit, name = BINARY_SENSOR_BITS[key]
    
    sensor = SPRSUNBinarySensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        bit=bit,
    )
    
    # bit 5 is ON in 0b00110011
    assert sensor.is_on is True


def test_binary_sensor_is_off_bit_6(mock_coordinator, mock_config_entry):
    """Test binary sensor reads bit 6 correctly (OFF)."""
    key = "alarm_stop"
    register, bit, name = BINARY_SENSOR_BITS[key]
    
    sensor = SPRSUNBinarySensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        bit=bit,
    )
    
    # bit 6 is OFF in 0b00110011
    assert sensor.is_on is False


def test_binary_sensor_is_off_bit_7(mock_coordinator, mock_config_entry):
    """Test binary sensor reads bit 7 correctly (OFF)."""
    key = "defrost_active"
    register, bit, name = BINARY_SENSOR_BITS[key]
    
    sensor = SPRSUNBinarySensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        bit=bit,
    )
    
    # bit 7 is OFF in 0b00110011
    assert sensor.is_on is False


def test_binary_sensor_unavailable_no_register(mock_coordinator, mock_config_entry):
    """Test binary sensor unavailable when register not in data."""
    key = "hotwater_demand"
    register, bit, name = BINARY_SENSOR_BITS[key]
    
    mock_coordinator.data = {}  # No working_status_register
    
    sensor = SPRSUNBinarySensor(
        coordinator=mock_coordinator,
        config_entry=mock_config_entry,
        key=key,
        name=name,
        bit=bit,
    )
    
    assert sensor.available is False
    assert sensor.is_on is False


def test_binary_sensor_bit_extraction():
    """Test bit extraction logic with various register values."""
    test_cases = [
        (0b00000001, 0, True),   # bit 0 ON
        (0b00000010, 1, True),   # bit 1 ON
        (0b00010000, 4, True),   # bit 4 ON
        (0b10000000, 7, True),   # bit 7 ON
        (0b11111110, 0, False),  # bit 0 OFF
        (0b11111101, 1, False),  # bit 1 OFF
        (0b00000000, 5, False),  # all OFF
        (0b11111111, 3, True),   # all ON
    ]
    
    for register_value, bit_position, expected in test_cases:
        result = bool(register_value & (1 << bit_position))
        assert result == expected, f"Failed for register={bin(register_value)}, bit={bit_position}"
