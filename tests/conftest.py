"""Pytest configuration for SPRSUN Modbus integration tests."""
import pytest
from unittest.mock import MagicMock, patch
import socket


# Allow socket connections for integration tests
@pytest.fixture(scope="session", autouse=True)
def socket_enabled(pytestconfig):
    """Enable real socket connections for integration tests."""
    # This allows pytest-socket to be bypassed for integration tests
    # that need real device connections
    pass


# Alternative: configure pytest-socket to allow specific hosts
def pytest_runtest_setup(item):
    """Configure socket permissions based on test markers."""
    # Allow sockets for tests marked with 'integration' or in test_integration.py
    if 'integration' in item.keywords or 'test_integration' in str(item.fspath):
        # Bypass socket blocking for integration tests
        item.add_marker(pytest.mark.allow_hosts(['192.168.1.234', 'localhost']))


@pytest.fixture
def mock_modbus_client():
    """Mock Modbus client."""
    with patch("custom_components.sprsun_modbus.ModbusTcpClient") as mock:
        client = MagicMock()
        client.connected = True
        client.connect.return_value = True
        mock.return_value = client
        yield client


@pytest.fixture
def mock_modbus_response_ro():
    """Mock successful Modbus response for Read-Only registers (50 values)."""
    response = MagicMock()
    response.isError.return_value = False
    
    # Simulate 50 registers (0x0000-0x0031, minus Invalid 0x0010)
    response.registers = [
        100,    # 0x0000: compressor_runtime = 100h
        350,    # 0x0001: cop = 350 (COP 3.5)
        0b00000011,  # 0x0002: switching_input_symbol
        0b00100011,  # 0x0003: working_status_mark (bits 0,1,5 set)
        0b01100001,  # 0x0004: output_symbol_1
        0b01000000,  # 0x0005: output_symbol_2
        0b01000001,  # 0x0006: output_symbol_3
        0,      # 0x0007: failure_symbol_1
        0,      # 0x0008: failure_symbol_2
        0,      # 0x0009: failure_symbol_3
        0,      # 0x000A: failure_symbol_4
        0,      # 0x000B: failure_symbol_5
        0,      # 0x000C: failure_symbol_6
        0,      # 0x000D: failure_symbol_7
        235,    # 0x000E: inlet_temp = 235 * 0.1 = 23.5°C
        450,    # 0x000F: hotwater_temp = 450 * 0.1 = 45.0°C
        0,      # 0x0010: INVALID (skipped in parsing)
        40,     # 0x0011: ambient_temp = 40 * 0.5 = 20.0°C
        280,    # 0x0012: outlet_temp = 280 * 0.1 = 28.0°C
        2026,   # 0x0013: software_version_year
        214,    # 0x0014: software_version_month_day (Feb 14)
        50,     # 0x0015: suction_gas_temp = 50 * 0.5 = 25.0°C
        60,     # 0x0016: coil_temp = 60 * 0.5 = 30.0°C
        230,    # 0x0017: ac_voltage = 230W
        15,     # 0x0018: pump_flow = 15 m³/h
        3500,   # 0x0019: heating_capacity = 3500W
        10,     # 0x001A: ac_current = 10A
        85,     # 0x001B: exhaust_temp = 85°C
        150,    # 0x001C: eev1_step = 150
        120,    # 0x001D: eev2_step = 120
        45,     # 0x001E: compressor_frequency = 45Hz
        0,      # 0x001F: freq_conversion_failure_1
        0,      # 0x0020: freq_conversion_failure_2
        340,    # 0x0021: dc_bus_voltage = 340V
        70,     # 0x0022: driving_temp = 70 * 0.5 = 35.0°C
        8,      # 0x0023: compressor_current = 8A
        50,     # 0x0024: target_frequency = 50Hz
        0,      # 0x0025: smart_grid_status
        800,    # 0x0026: dc_fan1_speed = 800rpm
        850,    # 0x0027: dc_fan2_speed = 850rpm
        50,     # 0x0028: evap_temp = 50 * 0.1 = 5.0°C
        700,    # 0x0029: cond_temp = 700 * 0.1 = 70.0°C
        0,      # 0x002A: freq_conversion_fault_high
        0,      # 0x002B: freq_conversion_fault_low
        100,    # 0x002C: controller_version
        101,    # 0x002D: display_version
        1500,   # 0x002E: dc_pump_speed = 1500rpm
        25,     # 0x002F: suction_pressure = 25 * 0.1 = 2.5bar
        120,    # 0x0030: discharge_pressure = 120 * 0.1 = 12.0bar
        900,    # 0x0031: dc_fan_target = 900rpm
    ]
    
    return response


@pytest.fixture
def mock_modbus_response_rw():
    """Mock Modbus response for single RW register."""
    response = MagicMock()
    response.isError.return_value = False
    response.registers = [100]  # Example: heating_setpoint = 100 * 0.5 = 50°C
    return response


@pytest.fixture
def mock_modbus_write_success():
    """Mock successful Modbus write response."""
    response = MagicMock()
    response.isError.return_value = False
    return response


@pytest.fixture
def hass_mock():
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}
    hass.async_add_executor_job = lambda func, *args: func(*args)
    return hass
