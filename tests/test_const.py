"""Unit tests for constants in const.py."""
import unittest

from tests.conftest import setup_mocks
setup_mocks()

from custom_components.sprsun_modbus.const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_DEVICE_ADDRESS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_TEMP_STEP,
    INTER_WRITE_DELAY,
    CONF_TEMP_STEP,
    PLATFORMS,
    REGISTERS_READ_ONLY,
    REGISTERS_EXPERT,
    BINARY_SENSOR_BITS,
    EXPERT_BINARY_SENSOR_BITS,
    REGISTERS_SWITCH,
    REGISTERS_BUTTON,
    REGISTERS_SELECT,
    REGISTERS_NUMBER,
    WEEKDAY_MAP,
    get_temp_step,
)


class TestSPRSUNConstants(unittest.TestCase):
    """Test suite for SPRSUN Modbus constants and register definitions."""

    def test_domain_and_defaults(self):
        """Test domain name and default configuration values."""
        self.assertEqual(DOMAIN, "sprsun_modbus")
        self.assertEqual(DEFAULT_NAME, "SPRSUN Heat Pump")
        self.assertEqual(DEFAULT_PORT, 502)
        self.assertEqual(DEFAULT_DEVICE_ADDRESS, 1)
        self.assertEqual(DEFAULT_SCAN_INTERVAL, 10)
        self.assertEqual(DEFAULT_TIMEOUT, 30)
        self.assertEqual(DEFAULT_TEMP_STEP, 1.0)
        self.assertEqual(CONF_TEMP_STEP, "temp_step")
        self.assertEqual(INTER_WRITE_DELAY, 0.08)

    def test_platforms(self):
        """Test platforms list contains all supported entity platforms."""
        expected_platforms = ["sensor", "binary_sensor", "number", "select", "switch", "button", "climate"]
        self.assertEqual(sorted(PLATFORMS), sorted(expected_platforms))

    def test_read_only_registers_count_and_range(self):
        """Test that read-only registers are within the 0x0000-0x0031 block."""
        # 50 contiguous addresses minus 0x0010 (invalid) = 49 registers
        self.assertEqual(len(REGISTERS_READ_ONLY), 49)
        self.assertNotIn(0x0010, REGISTERS_READ_ONLY, "0x0010 is invalid and must be skipped")

        for addr, config in REGISTERS_READ_ONLY.items():
            self.assertGreaterEqual(addr, 0x0000)
            self.assertLessEqual(addr, 0x0031)
            key, name, scale, unit, device_class = config
            self.assertIsInstance(key, str)
            self.assertIsInstance(name, str)
            self.assertIn(scale, [0.1, 0.5, 1, 0.0069])

    def test_read_only_keys_unique(self):
        """Ensure all RO register keys are unique."""
        keys = [config[0] for config in REGISTERS_READ_ONLY.values()]
        self.assertEqual(len(keys), len(set(keys)), "Duplicate RO register key found")

    def test_pressure_sensors_scaling_and_swap(self):
        """Test pressure sensors use 0.0069 bar scaling and swapped registers."""
        # 0x002E DC pump speed is PWM percentage (%)
        pump_key, pump_name, pump_scale, pump_unit, pump_dev_class = REGISTERS_READ_ONLY[0x002E]
        self.assertEqual(pump_key, "dc_pump_speed")
        self.assertEqual(pump_scale, 1)
        self.assertEqual(pump_unit, "%")
        self.assertIsNone(pump_dev_class)

        # 0x002F is labeled suction in manual, but actually discharge
        dis_key, dis_name, dis_scale, dis_unit, dis_dev_class = REGISTERS_READ_ONLY[0x002F]
        self.assertEqual(dis_key, "discharge_pressure")
        self.assertEqual(dis_scale, 0.0069)
        self.assertEqual(dis_unit, "bar")
        self.assertEqual(dis_dev_class, "pressure")

        # 0x0030 is labeled discharge in manual, but actually suction
        suc_key, suc_name, suc_scale, suc_unit, suc_dev_class = REGISTERS_READ_ONLY[0x0030]
        self.assertEqual(suc_key, "suction_pressure")
        self.assertEqual(suc_scale, 0.0069)
        self.assertEqual(suc_unit, "bar")
        self.assertEqual(suc_dev_class, "pressure")

    def test_temperature_sensors(self):
        """Verify key temperature sensor scales and device classes."""
        temp_registers = {
            0x000E: ("inlet_temp", 0.1),
            0x000F: ("hotwater_temp", 0.1),
            0x0011: ("ambient_temp", 0.5),
            0x0012: ("outlet_temp", 0.1),
            0x0015: ("suction_gas_temp", 0.5),
            0x0016: ("coil_temp", 0.5),
            0x001B: ("exhaust_temp", 1),
            0x0022: ("driving_temp", 0.5),
            0x0028: ("evap_temp", 0.1),
            0x0029: ("cond_temp", 0.1),
        }
        for addr, (expected_key, expected_scale) in temp_registers.items():
            config = REGISTERS_READ_ONLY[addr]
            self.assertEqual(config[0], expected_key)
            self.assertEqual(config[2], expected_scale)
            self.assertEqual(config[3], "°C")
            self.assertEqual(config[4], "temperature")

    def test_binary_sensors_count_and_bits(self):
        """Test binary sensor definitions across all status registers."""
        self.assertEqual(len(BINARY_SENSOR_BITS), 49)

        valid_source_registers = {
            0x0002, 0x0003, 0x0004, 0x0005, 0x0006,
            0x0007, 0x0008, 0x0009, 0x000A, 0x000B, 0x000C, 0x000D,
        }

        for key, (source_addr, bit, name) in BINARY_SENSOR_BITS.items():
            self.assertIn(source_addr, valid_source_registers)
            self.assertGreaterEqual(bit, 0)
            self.assertLessEqual(bit, 7)
            self.assertIsInstance(name, str)

        # Verify key operational indicators
        self.assertEqual(BINARY_SENSOR_BITS["hotwater_demand"], (0x0003, 0, "Hot Water Demand"))
        self.assertEqual(BINARY_SENSOR_BITS["heating_demand"], (0x0003, 1, "Heating Demand"))
        self.assertEqual(BINARY_SENSOR_BITS["compressor_running"], (0x0004, 0, "Compressor"))
        self.assertEqual(BINARY_SENSOR_BITS["flow_switch"], (0x0002, 4, "Flow Switch"))

    def test_switch_registers(self):
        """Test switch register definitions."""
        self.assertIn("power_switch", REGISTERS_SWITCH)
        self.assertIn("antilegionella_enable", REGISTERS_SWITCH)
        self.assertIn("two_three_function", REGISTERS_SWITCH)

        power_addr, power_bit, power_name, power_coil = REGISTERS_SWITCH["power_switch"]
        self.assertEqual(power_addr, 0x0032)
        self.assertEqual(power_bit, 0)
        self.assertEqual(power_name, "Power")
        self.assertEqual(power_coil, 0x0320)

    def test_button_registers(self):
        """Test button definitions."""
        self.assertIn("failure_reset", REGISTERS_BUTTON)
        addr, bit, name, desc = REGISTERS_BUTTON["failure_reset"]
        self.assertEqual(addr, 0x0033)
        self.assertEqual(bit, 7)
        self.assertEqual(name, "Failure Reset")

    def test_select_registers(self):
        """Test select definitions for mode control."""
        self.assertIn(0x0036, REGISTERS_SELECT)  # unit_mode
        self.assertIn(0x0190, REGISTERS_SELECT)  # fan_mode
        self.assertIn(0x019E, REGISTERS_SELECT)  # pump_mode

        key, name, options = REGISTERS_SELECT[0x0036]
        self.assertEqual(key, "unit_mode")
        self.assertEqual(len(options), 5)
        self.assertEqual(options[0], "Hot Water Only")
        self.assertEqual(options[1], "Heating Only")
        self.assertEqual(options[2], "Cooling Only")
        self.assertEqual(options[3], "Heating + Hot Water")
        self.assertEqual(options[4], "Cooling + Hot Water")

    def test_number_registers_configuration(self):
        """Test RW number registers count, ranges and scaling."""
        self.assertEqual(len(REGISTERS_NUMBER), 42)

        for addr, config in REGISTERS_NUMBER.items():
            key, name, scale, unit, min_val, max_val, step, device_class = config
            self.assertIsInstance(key, str)
            self.assertIsInstance(name, str)
            self.assertGreater(scale, 0)
            self.assertLess(min_val, max_val)
            self.assertGreater(step, 0)

        # Setpoints verification
        self.assertEqual(REGISTERS_NUMBER[0x00CC][0], "heating_setpoint")
        self.assertEqual(REGISTERS_NUMBER[0x00CB][0], "cooling_setpoint")
        self.assertEqual(REGISTERS_NUMBER[0x00CA][0], "hotwater_setpoint")

    def test_weekday_map(self):
        """Test weekday map matches Sunday (0) to Saturday (6)."""
        self.assertEqual(len(WEEKDAY_MAP), 7)
        self.assertEqual(WEEKDAY_MAP[0], "Sunday")
        self.assertEqual(WEEKDAY_MAP[1], "Monday")
        self.assertEqual(WEEKDAY_MAP[6], "Saturday")

    def test_get_temp_step_mappings_and_fallbacks(self):
        """Test get_temp_step helper handles dict, MappingProxyType, None and fallback."""
        from types import MappingProxyType
        from unittest.mock import MagicMock

        # Standard dict
        entry = MagicMock()
        entry.options = {CONF_TEMP_STEP: 1.0}
        self.assertEqual(get_temp_step(entry), 1.0)

        # MappingProxyType (used by Home Assistant)
        entry.options = MappingProxyType({CONF_TEMP_STEP: 1.0})
        self.assertEqual(get_temp_step(entry), 1.0)

        # In data
        entry.options = MappingProxyType({})
        entry.data = MappingProxyType({CONF_TEMP_STEP: 1.0})
        self.assertEqual(get_temp_step(entry), 1.0)

        # Default fallback
        entry.options = MappingProxyType({})
        entry.data = MappingProxyType({})
        self.assertEqual(get_temp_step(entry), 1.0)
        self.assertEqual(get_temp_step(None), 1.0)

        # Coordinator mock fallback
        mock_coord_entry = MagicMock()
        mock_fallback = MagicMock()
        mock_fallback.options = {CONF_TEMP_STEP: 1.0}
        self.assertEqual(get_temp_step(mock_coord_entry, mock_fallback), 1.0)

    def test_expert_registers_and_bits_views(self):
        """Test expert register and control bit legacy map views."""
        self.assertEqual(len(REGISTERS_EXPERT), 336)
        self.assertEqual(len(EXPERT_BINARY_SENSOR_BITS), 17)
        self.assertEqual(REGISTERS_EXPERT[0x0037][0], "h01_defrost_freq")
        self.assertEqual(REGISTERS_EXPERT[0x0082][0], "f02_hp_protect_value")
        self.assertEqual(REGISTERS_EXPERT[0x01BB][0], "r94_oil_return_freq")
        self.assertEqual(EXPERT_BINARY_SENSOR_BITS["b74_av_cool_enable"][:2], (0x0033, 2))
        self.assertEqual(EXPERT_BINARY_SENSOR_BITS["timeband_1_enable"][:2], (0x0035, 0))


if __name__ == "__main__":
    unittest.main()
