"""Unit tests for SPRSUN Modbus const.py"""
import pytest
from custom_components.sprsun_modbus.const import (
    REGISTERS_READ_ONLY,
    REGISTERS_NUMBER,
    BINARY_SENSOR_BITS,
    UNIT_MODE_MAP,
)


def test_registers_read_only_count():
    """Test that we have correct number of read-only registers."""
    assert len(REGISTERS_READ_ONLY) == 50, "Should have 50 read-only registers"


def test_registers_read_only_addresses():
    """Test that read-only register addresses are in valid range."""
    for address in REGISTERS_READ_ONLY.keys():
        assert 0x0000 <= address <= 0x0031, f"Address {hex(address)} out of range"
        assert address != 0x0010, "Address 0x0010 is Invalid and should be skipped"


def test_registers_read_only_scaling():
    """Test that scaling factors are correct."""
    valid_scales = [0.1, 0.5, 1]
    
    for address, config in REGISTERS_READ_ONLY.items():
        key, name, scale, unit, device_class = config
        assert scale in valid_scales, f"Invalid scale {scale} for {hex(address)}"


def test_temperature_sensors_have_correct_scale():
    """Test temperature sensors use documented scaling."""
    temp_sensors = {
        0x000E: 0.1,  # inlet_temp
        0x000F: 0.1,  # hotwater_temp
        0x0011: 0.5,  # ambient_temp
        0x0012: 0.1,  # outlet_temp
        0x0015: 0.5,  # suction_gas_temp
        0x0016: 0.5,  # coil_temp
        0x001B: 1,    # exhaust_temp
        0x0022: 0.5,  # driving_temp
        0x0028: 0.1,  # evap_temp
        0x0029: 0.1,  # cond_temp
    }
    
    for address, expected_scale in temp_sensors.items():
        config = REGISTERS_READ_ONLY[address]
        scale = config[2]
        assert scale == expected_scale, f"Wrong scale for {hex(address)}: {scale} != {expected_scale}"


def test_pressure_sensors_have_correct_scale():
    """Test pressure sensors use 0.1 bar scaling."""
    pressure_sensors = [0x002F, 0x0030]  # suction_pressure, discharge_pressure
    
    for address in pressure_sensors:
        config = REGISTERS_READ_ONLY[address]
        scale = config[2]
        assert scale == 0.1, f"Pressure sensor {hex(address)} should have scale 0.1"


def test_registers_number_count():
    """Test that we have correct number of read-write registers."""
    assert len(REGISTERS_NUMBER) == 42, "Should have 42 read-write registers"


def test_registers_number_addresses():
    """Test that RW register addresses match documentation."""
    expected_addresses = [
        0x0036,  # unit_mode
        0x00CC, 0x00CB, 0x00CA,  # setpoints
        0x00C6, 0x00C8,  # temp diffs
        0x0190,  # fan_mode
        # Economic heating
        0x0169, 0x016A, 0x016B, 0x016C,  # ambient temps
        0x0175, 0x0176, 0x0177, 0x0178,  # water temps
        # Economic water
        0x016D, 0x016E, 0x016F, 0x0170,  # ambient temps
        0x0179, 0x017A, 0x017B, 0x017C,  # water temps
        # Economic cooling
        0x0171, 0x0172, 0x0173, 0x0174,  # ambient temps
        0x017D, 0x017E, 0x017F, 0x0180,  # water temps
        # General config
        0x0181, 0x0182, 0x0183, 0x0184, 0x0185, 0x018D,
        0x0191, 0x0192, 0x0193, 0x019E,
        # Antilegionella
        0x019A, 0x019B, 0x019C, 0x019D,
    ]
    
    actual_addresses = sorted(REGISTERS_NUMBER.keys())
    assert actual_addresses == sorted(expected_addresses), "RW addresses don't match documentation"


def test_setpoint_scaling():
    """Test that setpoints use 0.5°C scaling."""
    setpoint_addresses = [0x00CC, 0x00CB, 0x00CA]  # heating, cooling, hotwater
    
    for address in setpoint_addresses:
        config = REGISTERS_NUMBER[address]
        scale = config[2]
        assert scale == 0.5, f"Setpoint {hex(address)} should have scale 0.5"


def test_economic_mode_ambient_scaling():
    """Test that economic mode ambient temps use 1°C scaling."""
    ambient_addresses = list(range(0x0169, 0x016D)) + list(range(0x016D, 0x0171)) + list(range(0x0171, 0x0175))
    
    for address in ambient_addresses:
        if address in REGISTERS_NUMBER:
            config = REGISTERS_NUMBER[address]
            scale = config[2]
            assert scale == 1, f"Economic ambient {hex(address)} should have scale 1"


def test_economic_mode_water_scaling():
    """Test that economic mode water temps use 0.5°C scaling."""
    water_temp_addresses = list(range(0x0175, 0x0179)) + list(range(0x0179, 0x017D)) + list(range(0x017D, 0x0181))
    
    for address in water_temp_addresses:
        if address in REGISTERS_NUMBER:
            config = REGISTERS_NUMBER[address]
            scale = config[2]
            assert scale == 0.5, f"Economic water temp {hex(address)} should have scale 0.5"


def test_binary_sensor_bits():
    """Test binary sensor bit definitions."""
    assert len(BINARY_SENSOR_BITS) == 6, "Should have 6 binary sensors"
    
    # All should read from register 0x0003
    for key, (register, bit, name) in BINARY_SENSOR_BITS.items():
        assert register == 0x0003, f"Binary sensor {key} should read from 0x0003"
        assert 0 <= bit <= 7, f"Bit position {bit} invalid for {key}"


def test_binary_sensor_bit_positions():
    """Test binary sensors use correct bit positions."""
    expected_bits = {
        "hotwater_demand": 0,
        "heating_demand": 1,
        "cooling_demand": 5,
        "antilegionella_active": 4,
        "defrost_active": 7,
        "alarm_stop": 6,
    }
    
    for key, expected_bit in expected_bits.items():
        register, bit, name = BINARY_SENSOR_BITS[key]
        assert bit == expected_bit, f"Binary sensor {key} should be bit {expected_bit}, got {bit}"


def test_unit_mode_map():
    """Test unit mode descriptions."""
    assert len(UNIT_MODE_MAP) == 5, "Should have 5 unit modes"
    assert 0 in UNIT_MODE_MAP and 4 in UNIT_MODE_MAP, "Modes should be 0-4"


def test_batch_read_covers_all_ro_registers():
    """Test that batch read count=50 covers all RO registers."""
    max_address = max(REGISTERS_READ_ONLY.keys())
    min_address = min(REGISTERS_READ_ONLY.keys())
    
    # Batch read: address=0x0000, count=50 → covers 0x0000 to 0x0031 (50 registers)
    batch_start = 0x0000
    batch_count = 50
    batch_end = batch_start + batch_count - 1
    
    assert min_address >= batch_start, f"Min address {hex(min_address)} outside batch"
    assert max_address <= batch_end, f"Max address {hex(max_address)} outside batch (end={hex(batch_end)})"
    
    # Verify count=50 is correct
    expected_range = max_address - min_address + 1
    # Account for 0x0010 being skipped
    expected_count = expected_range
    assert batch_count >= expected_count, f"Batch count {batch_count} too small for range {expected_count}"
