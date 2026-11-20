"""Pytest configuration and shared fixtures for SPRSUN Modbus tests."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure mocks and path are initialized
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from tests.mock_ha import setup_mocks
setup_mocks()

try:
    import pytest
except ImportError:
    # Minimal pytest fixture decorator stub if pytest not installed
    class PytestStub:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
    pytest = PytestStub()


@pytest.fixture
def hass_mock():
    """Mock Home Assistant instance."""
    hass = MagicMock()
    hass.data = {}

    async def async_add_executor_job(func, *args, **kwargs):
        return func(*args, **kwargs)

    hass.async_add_executor_job = async_add_executor_job
    hass.config_entries = MagicMock()
    hass.config_entries.async_reload = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    return hass


@pytest.fixture
def mock_config_entry():
    """Mock Home Assistant config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.data = {
        "name": "SPRSUN Heat Pump",
        "host": "192.168.1.200",
        "port": 502,
        "device_address": 1,
        "scan_interval": 10,
        "controller_type": "chico",
    }
    return entry


@pytest.fixture
def mock_modbus_response_ro():
    """Mock 50 registers read-only response for CHICO controller."""
    response = MagicMock()
    response.isError.return_value = False
    
    # 50 registers from 0x0000 to 0x0031
    response.registers = [
        1250,        # 0x0000: compressor_runtime = 1250 h
        380,         # 0x0001: cop = 380 (3.8)
        0b00000001,  # 0x0002: switching_input_symbol (bit 0 set: ac_linkage_switch)
        0b00000011,  # 0x0003: working_status_mark (bit 0: hotwater_demand, bit 1: heating_demand)
        0b00000001,  # 0x0004: output_symbol_1 (bit 0: compressor_running)
        0b00000001,  # 0x0005: output_symbol_2 (bit 0: chassis_heater)
        0b01000001,  # 0x0006: output_symbol_3 (bit 0: ac_pump, bit 6: pump_running)
        0,           # 0x0007: failure_symbol_1
        0,           # 0x0008: failure_symbol_2
        0,           # 0x0009: failure_symbol_3
        0,           # 0x000A: failure_symbol_4
        0,           # 0x000B: failure_symbol_5
        0,           # 0x000C: failure_symbol_6
        0,           # 0x000D: failure_symbol_7
        245,         # 0x000E: inlet_temp = 24.5 °C (245 * 0.1)
        485,         # 0x000F: hotwater_temp = 48.5 °C (485 * 0.1)
        0,           # 0x0010: INVALID/unused
        65516,       # 0x0011: ambient_temp = -20 * 0.5 = -10.0 °C (signed: 65516 -> -20)
        320,         # 0x0012: outlet_temp = 32.0 °C (320 * 0.1)
        2024,        # 0x0013: software_version_year
        1120,        # 0x0014: software_version_month_day
        65526,       # 0x0015: suction_gas_temp = -10 * 0.5 = -5.0 °C (signed: 65526 -> -10)
        65530,       # 0x0016: coil_temp = -6 * 0.5 = -3.0 °C (signed: 65530 -> -6)
        230,         # 0x0017: ac_voltage = 230 V
        18,          # 0x0018: pump_flow = 18 m3/h
        4200,        # 0x0019: heating_cooling_capacity = 4200 W
        12,          # 0x001A: ac_current = 12 A
        78,          # 0x001B: exhaust_temp = 78 °C
        180,         # 0x001C: eev1_step = 180
        140,         # 0x001D: eev2_step = 140
        55,          # 0x001E: compressor_frequency = 55 Hz
        0,           # 0x001F: freq_conversion_failure_1
        0,           # 0x0020: freq_conversion_failure_2
        380,         # 0x0021: dc_bus_voltage = 380 V
        80,          # 0x0022: driving_temp = 40.0 °C (80 * 0.5)
        9,           # 0x0023: compressor_current = 9 A
        60,          # 0x0024: target_frequency = 60 Hz
        0,           # 0x0025: smart_grid_status
        650,         # 0x0026: dc_fan1_speed = 650 rpm
        680,         # 0x0027: dc_fan2_speed = 680 rpm
        65516,       # 0x0028: evap_temp = -2.0 °C (signed: -20 * 0.1)
        450,         # 0x0029: cond_temp = 45.0 °C (450 * 0.1)
        0,           # 0x002A: freq_conversion_fault_high
        0,           # 0x002B: freq_conversion_fault_low
        105,         # 0x002C: controller_version = 105
        102,         # 0x002D: display_version = 102
        1200,        # 0x002E: dc_pump_speed = 1200 rpm
        3500,        # 0x002F: discharge_pressure = 3500 * 0.0069 = 24.15 bar (swapped!)
        800,         # 0x0030: suction_pressure = 800 * 0.0069 = 5.52 bar (swapped!)
        700,         # 0x0031: dc_fan_target = 700 rpm
    ]
    return response


@pytest.fixture
def mock_modbus_client(mock_modbus_response_ro):
    """Mock ModbusTcpClient with predefined behaviors."""
    client = MagicMock()
    client.connected = True
    client.connect.return_value = True
    client.read_holding_registers.return_value = mock_modbus_response_ro
    
    write_res = MagicMock()
    write_res.isError.return_value = False
    client.write_register.return_value = write_res
    return client


@pytest.fixture
def mock_coordinator(mock_modbus_client):
    """Mock coordinator with realistic cached state."""
    coordinator = MagicMock()
    coordinator.client = mock_modbus_client
    coordinator.device_address = 1
    coordinator.last_update_success = True
    coordinator.cache_staleness_seconds = 20

    # Populated cache with new dictionary format {"value": ..., "updated_at": ...}
    import time
    now = time.time()
    coordinator.data = {
        # Status registers for binary sensors
        "working_status_register": {"value": 0b00000011, "updated_at": now},
        "switching_input_symbol": {"value": 0b00000001, "updated_at": now},
        "output_symbol_1": {"value": 0b00000001, "updated_at": now},
        "output_symbol_2": {"value": 0b00000001, "updated_at": now},
        "output_symbol_3": {"value": 0b01000001, "updated_at": now},
        "failure_symbol_1": {"value": 0, "updated_at": now},
        "failure_symbol_2": {"value": 0, "updated_at": now},
        "failure_symbol_3": {"value": 0, "updated_at": now},
        "failure_symbol_4": {"value": 0, "updated_at": now},
        "failure_symbol_5": {"value": 0, "updated_at": now},
        "failure_symbol_6": {"value": 0, "updated_at": now},
        "failure_symbol_7": {"value": 0, "updated_at": now},

        # Sensors
        "inlet_temp": {"value": 24.5, "updated_at": now},
        "outlet_temp": {"value": 32.0, "updated_at": now},
        "hotwater_temp": {"value": 48.5, "updated_at": now},
        "ambient_temp": {"value": -10.0, "updated_at": now},
        "compressor_runtime": {"value": 1250, "updated_at": now},
        "cop": {"value": 3.8, "updated_at": now},
        "compressor_frequency": {"value": 55, "updated_at": now},
        "discharge_pressure": {"value": 24.15, "updated_at": now},
        "suction_pressure": {"value": 5.52, "updated_at": now},
        "compressor_running": {"value": True, "updated_at": now},

        # Control registers for switches
        "_control_0032": {"value": 1, "updated_at": now},  # power ON (bit 0 = 1)
        "_control_0034": {"value": 3, "updated_at": now},  # antilegionella (bit 0=1), two_three (bit 1=1)

        # Select & numbers
        "unit_mode": {"value": 3, "updated_at": now},  # Heating + Hot Water
        "fan_mode": {"value": 0, "updated_at": now},  # Normal
        "pump_mode": {"value": 1, "updated_at": now},  # Normal
        "mode_control_enable": {"value": 0, "updated_at": now},
        "heating_setpoint": {"value": 38.0, "updated_at": now},
        "cooling_setpoint": {"value": 18.0, "updated_at": now},
        "hotwater_setpoint": {"value": 50.0, "updated_at": now},
        "econ_heat_ambi_1": {"value": -15.0, "updated_at": now},
    }

    coordinator._ensure_connection = MagicMock(return_value=True)
    coordinator.async_write_register = AsyncMock()
    return coordinator
