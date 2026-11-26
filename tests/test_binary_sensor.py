"""Unit tests for binary_sensor.py."""
import unittest
from unittest.mock import MagicMock

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.const import CONF_NAME, EntityCategory
from custom_components.sprsun_modbus.const import (
    BINARY_SENSOR_BITS,
    CONF_ENABLE_EXPERT_WRITES,
    DOMAIN,
)
from custom_components.sprsun_modbus.controllers.chico_registers import (
    CHICO_CORE_BINARY_SENSORS,
    CHICO_EXPERT_BINARY_SENSORS,
)
from custom_components.sprsun_modbus.binary_sensor import (
    SPRSUNBinarySensor,
    async_setup_entry,
)


class TestSPRSUNBinarySensor(unittest.IsolatedAsyncioTestCase):
    """Test suite for SPRSUN binary sensors."""

    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = MagicMock()
        self.coordinator.last_update_success = True
        self.coordinator.data = {
            # 0x0003: bits 0 (hotwater_demand) and 1 (heating_demand) set
            "working_status_register": {"value": 0b00000011, "updated_at": 1000.0},
            # 0x0002: bit 4 (flow_switch) set
            "switching_input_symbol": {"value": 0b00010000, "updated_at": 1000.0},
            # 0x0004: bit 0 (compressor_running) set
            "output_symbol_1": {"value": 0b00000001, "updated_at": 1000.0},
            # 0x0005: bit 5 (heating_heater) set, scalar format
            "output_symbol_2": 0b00100000,
            # 0x0006: all bits 0
            "output_symbol_3": {"value": 0, "updated_at": 1000.0},
            # 0x0007: bit 1 (error_ambient_sensor) set
            "failure_symbol_1": {"value": 0b00000010, "updated_at": 1000.0},
        }

        self.config_entry = MagicMock()
        self.config_entry.entry_id = "entry_bin_123"
        self.config_entry.data = {
            CONF_NAME: "SPRSUN Heat Pump",
        }
        self.config_entry.options = {}

    async def test_async_setup_entry_creates_core_by_default_and_expert_when_enabled(self):
        """Test default setup creates 49 core binary sensors, and opt-in adds 17 expert."""
        hass = MagicMock()
        hass.data = {DOMAIN: {self.config_entry.entry_id: self.coordinator}}
        async_add_entities = MagicMock()

        await async_setup_entry(hass, self.config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        self.assertEqual(len(entities), len(CHICO_CORE_BINARY_SENSORS))
        self.assertEqual(len(entities), len(BINARY_SENSOR_BITS))
        self.assertEqual(len(entities), 49)

        # With expert option enabled, all 49 core + 17 expert = 66 binary sensors are added
        self.config_entry.options = {CONF_ENABLE_EXPERT_WRITES: True}
        added_expert = []
        await async_setup_entry(hass, self.config_entry, added_expert.extend)
        self.assertEqual(
            len(added_expert),
            len(CHICO_CORE_BINARY_SENSORS) + len(CHICO_EXPERT_BINARY_SENSORS),
        )
        self.assertEqual(len(added_expert), 66)

        by_key = {entity._key: entity for entity in added_expert}
        self.assertEqual(by_key["r29_constant_freq_adj"].entity_category, EntityCategory.DIAGNOSTIC)
        self.assertFalse(
            getattr(by_key["night_clock_mode"], "_attr_entity_registry_enabled_default", True)
        )
        self.assertFalse(
            getattr(by_key["r29_constant_freq_adj"], "_attr_entity_registry_enabled_default", True)
        )
        self.assertTrue(
            getattr(by_key["hotwater_demand"], "_attr_entity_registry_enabled_default", True)
        )

    def test_binary_sensor_attributes(self):
        """Test standard binary sensor naming and unique_id."""
        sensor = SPRSUNBinarySensor(
            self.coordinator,
            self.config_entry,
            "hotwater_demand",
            "Hot Water Demand",
        )
        self.assertEqual(sensor.name, "Hot Water Demand")
        self.assertTrue(sensor.has_entity_name)
        self.assertEqual(sensor.unique_id, "entry_bin_123_hotwater_demand")
        self.assertEqual(sensor.device_info["identifiers"], {(DOMAIN, "entry_bin_123")})

    def test_is_on_operational_bits(self):
        """Test is_on returns True when corresponding bit is set."""
        # hotwater_demand is bit 0 of 0x0003 (value 0b00000011 -> True)
        hw_sensor = SPRSUNBinarySensor(
            self.coordinator, self.config_entry, "hotwater_demand", "Hot Water Demand"
        )
        self.assertTrue(hw_sensor.is_on)

        # cooling_demand is bit 5 of 0x0003 (bit 5 is 0 -> False)
        cool_sensor = SPRSUNBinarySensor(
            self.coordinator, self.config_entry, "cooling_demand", "Cooling Demand"
        )
        self.assertFalse(cool_sensor.is_on)

    def test_is_on_switching_inputs(self):
        """Test is_on for switching inputs from register 0x0002."""
        # flow_switch is bit 4 of 0x0002 (value 0b00010000 -> True)
        flow_sensor = SPRSUNBinarySensor(
            self.coordinator, self.config_entry, "flow_switch", "Flow Switch"
        )
        self.assertTrue(flow_sensor.is_on)

        # ac_linkage_switch is bit 0 of 0x0002 (bit 0 is 0 -> False)
        linkage_sensor = SPRSUNBinarySensor(
            self.coordinator, self.config_entry, "ac_linkage_switch", "A/C Linkage Switch"
        )
        self.assertFalse(linkage_sensor.is_on)

    def test_is_on_outputs(self):
        """Test is_on for output symbols from 0x0004 and 0x0005."""
        # compressor_running is bit 0 of 0x0004 (value 0b00000001 -> True)
        comp_sensor = SPRSUNBinarySensor(
            self.coordinator, self.config_entry, "compressor_running", "Compressor"
        )
        self.assertTrue(comp_sensor.is_on)

        # heating_heater is bit 5 of 0x0005 (value 0b00100000 -> True)
        heater_sensor = SPRSUNBinarySensor(
            self.coordinator, self.config_entry, "heating_heater", "Heating Heater"
        )
        self.assertTrue(heater_sensor.is_on)

    def test_is_on_failures(self):
        """Test failure alarms extracted from failure_symbol registers."""
        # error_ambient_sensor is bit 1 of 0x0007 (value 0b00000010 -> True)
        err_amb = SPRSUNBinarySensor(
            self.coordinator, self.config_entry, "error_ambient_sensor", "Ambient Temp Sensor Error"
        )
        self.assertTrue(err_amb.is_on)

        # error_hotwater_sensor is bit 0 of 0x0007 (bit 0 is 0 -> False)
        err_hw = SPRSUNBinarySensor(
            self.coordinator, self.config_entry, "error_hotwater_sensor", "Hot Water Temp Sensor Error"
        )
        self.assertFalse(err_hw.is_on)

    def test_available(self):
        """Test availability reflects coordinator status and register presence."""
        sensor = SPRSUNBinarySensor(
            self.coordinator, self.config_entry, "hotwater_demand", "Hot Water Demand"
        )
        self.assertTrue(sensor.available)

        self.coordinator.last_update_success = False
        self.assertFalse(sensor.available)

        self.coordinator.last_update_success = True
        del self.coordinator.data["working_status_register"]
        self.assertFalse(sensor.available)

    def test_expert_control_bits_and_inverted_b74(self):
        """Test expert control bitfields including inverted B74 AV Cool Enable."""
        # 0x0033: bit 0 set (r29), bit 2 cleared (b74 inverted -> True!), bit 4 set (d01)
        self.coordinator.data["_control_0033"] = {"value": 0b00010001, "updated_at": 1000.0}
        self.coordinator.data["_control_0035"] = {"value": 0b00000101, "updated_at": 1000.0}

        r29 = SPRSUNBinarySensor(self.coordinator, self.config_entry, "r29_constant_freq_adj", "R29")
        self.assertTrue(r29.is_on)
        self.assertTrue(r29.available)

        # Bit 2 = 0 -> inverted=True -> ON (AV Cool Enabled)
        b74 = SPRSUNBinarySensor(self.coordinator, self.config_entry, "b74_av_cool_enable", "B74")
        self.assertTrue(b74.is_on)

        # Bit 2 = 1 -> inverted=True -> OFF (AV Cool Unused)
        self.coordinator.data["_control_0033"] = {"value": 0b00000100, "updated_at": 1000.0}
        self.assertFalse(b74.is_on)

        tb1 = SPRSUNBinarySensor(self.coordinator, self.config_entry, "timeband_1_enable", "TB1")
        tb2 = SPRSUNBinarySensor(self.coordinator, self.config_entry, "timeband_2_enable", "TB2")
        tb3 = SPRSUNBinarySensor(self.coordinator, self.config_entry, "timeband_3_enable", "TB3")
        self.assertTrue(tb1.is_on)
        self.assertFalse(tb2.is_on)
        self.assertTrue(tb3.is_on)


if __name__ == "__main__":
    unittest.main()
