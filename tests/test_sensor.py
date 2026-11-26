"""Unit tests for sensor.py."""
import unittest
from unittest.mock import MagicMock, AsyncMock

from tests.conftest import setup_mocks
setup_mocks()

from homeassistant.const import CONF_NAME, EntityCategory
from custom_components.sprsun_modbus.const import DOMAIN, REGISTERS_READ_ONLY
from custom_components.sprsun_modbus.controllers.chico_derived import CHICO_DERIVED_SENSORS
from custom_components.sprsun_modbus.controllers.chico_registers import CHICO_SENSORS
from custom_components.sprsun_modbus.sensor import SPRSUNDerivedSensor, SPRSUNSensor, async_setup_entry


class TestSPRSUNSensor(unittest.IsolatedAsyncioTestCase):
    """Test suite for SPRSUN sensor entities."""

    def setUp(self):
        """Set up test environment."""
        self.coordinator = MagicMock()
        self.coordinator.last_update_success = True
        self.coordinator.data = {
            "inlet_temp": {"value": 24.5, "updated_at": 1000.0},
            "cop": 3.8,  # Test legacy scalar format
            "discharge_pressure": {"value": 24.15, "updated_at": 1000.0},
            "ac_voltage": {"value": 230.0, "updated_at": 1000.0},
            "ac_current": {"value": 10.5, "updated_at": 1000.0},
            "compressor_frequency": {"value": 50.0, "updated_at": 1000.0},
            "heating_cooling_capacity": {"value": 3500.0, "updated_at": 1000.0},
        }

        self.config_entry = MagicMock()
        self.config_entry.entry_id = "test_entry_456"
        self.config_entry.data = {
            CONF_NAME: "SPRSUN Heat Pump",
        }

    async def test_async_setup_entry_creates_all_sensors(self):
        """Test async_setup_entry adds all core (49), expert (336), and derived (10) sensors."""
        hass = MagicMock()
        hass.data = {DOMAIN: {self.config_entry.entry_id: self.coordinator}}
        async_add_entities = MagicMock()

        await async_setup_entry(hass, self.config_entry, async_add_entities)

        async_add_entities.assert_called_once()
        entities = async_add_entities.call_args[0][0]
        self.assertEqual(len(entities), len(CHICO_SENSORS) + len(CHICO_DERIVED_SENSORS))
        self.assertEqual(len(entities), 395)

        by_key = {entity._key: entity for entity in entities}
        self.assertEqual(by_key["h01_defrost_freq"].entity_category, EntityCategory.DIAGNOSTIC)
        self.assertIsNone(by_key["h01_defrost_freq"].state_class)
        self.assertFalse(
            getattr(by_key["b21_av_heat_initial_2"], "_attr_entity_registry_enabled_default", True)
        )
        self.assertFalse(
            getattr(by_key["h01_defrost_freq"], "_attr_entity_registry_enabled_default", True)
        )
        self.assertTrue(
            getattr(by_key["inlet_temp"], "_attr_entity_registry_enabled_default", True)
        )
        for derived_spec in CHICO_DERIVED_SENSORS:
            derived_ent = by_key[derived_spec.key]
            self.assertIsInstance(derived_ent, SPRSUNDerivedSensor)
            self.assertFalse(
                getattr(derived_ent, "_attr_entity_registry_enabled_default", True),
                f"Derived sensor {derived_spec.key} must be disabled by default",
            )

    def test_sensor_creation_and_attributes(self):
        """Test sensor initialization and standard HA properties."""
        key, name, scale, unit, device_class = REGISTERS_READ_ONLY[0x000E]  # inlet_temp
        sensor = SPRSUNSensor(
            self.coordinator,
            self.config_entry,
            key,
            name,
            unit,
            device_class,
        )

        self.assertEqual(sensor.name, name)
        self.assertTrue(sensor.has_entity_name)
        self.assertEqual(sensor.unique_id, "test_entry_456_inlet_temp")
        self.assertEqual(sensor.native_unit_of_measurement, "°C")
        self.assertEqual(str(sensor.device_class), "temperature")
        self.assertEqual(str(sensor.state_class), "measurement")
        self.assertEqual(sensor.device_info["identifiers"], {(DOMAIN, "test_entry_456")})

    def test_native_value_dict_format(self):
        """Test native_value extracts float from new dict cache format."""
        sensor = SPRSUNSensor(
            self.coordinator,
            self.config_entry,
            "inlet_temp",
            "Inlet Temp",
            "°C",
            "temperature",
        )
        self.assertEqual(sensor.native_value, 24.5)

    def test_native_value_scalar_format(self):
        """Test native_value handles legacy scalar cache format."""
        sensor = SPRSUNSensor(
            self.coordinator,
            self.config_entry,
            "cop",
            "COP",
            None,
            None,
        )
        self.assertEqual(sensor.native_value, 3.8)

    def test_native_value_missing_returns_none(self):
        """Test native_value returns None when key is absent in cache."""
        sensor = SPRSUNSensor(
            self.coordinator,
            self.config_entry,
            "nonexistent_key",
            "Nonexistent",
            None,
            None,
        )
        self.assertIsNone(sensor.native_value)

    def test_availability(self):
        """Test availability reflects coordinator success and key presence."""
        sensor = SPRSUNSensor(
            self.coordinator,
            self.config_entry,
            "inlet_temp",
            "Inlet Temp",
            "°C",
            "temperature",
        )
        self.assertTrue(sensor.available)

        # When coordinator fails
        self.coordinator.last_update_success = False
        self.assertFalse(sensor.available)

        # When key missing
        self.coordinator.last_update_success = True
        sensor._key = "missing_sensor"
        self.assertFalse(sensor.available)

    def test_device_classes(self):
        """Test device class mappings for various sensor types."""
        test_cases = [
            ("discharge_pressure", "bar", "pressure", "pressure"),
            ("heating_cooling_capacity", "W", "power", "power"),
            ("ac_voltage", "V", "voltage", "voltage"),
            ("ac_current", "A", "current", "current"),
            ("compressor_frequency", "Hz", "frequency", "frequency"),
        ]
        for key, unit, dev_class_str, expected in test_cases:
            sensor = SPRSUNSensor(
                self.coordinator,
                self.config_entry,
                key,
                key.replace("_", " ").title(),
                unit,
                dev_class_str,
            )
            self.assertEqual(str(sensor.device_class), expected)
            self.assertEqual(str(sensor.state_class), "measurement")

    def test_enum_options_and_static_state_class(self):
        """Test options mapping for enum-style expert sensors and static state_class='none'."""
        self.coordinator.data["f13_dc_pump_mode"] = {"value": 1, "updated_at": 1000.0}
        self.coordinator.data["f56_model_selection"] = {"value": 99, "updated_at": 1000.0}
        self.coordinator.data["h01_defrost_freq"] = {"value": 55, "updated_at": 1000.0}

        pump_mode = SPRSUNSensor(
            self.coordinator,
            self.config_entry,
            "f13_dc_pump_mode",
            "F13 DC Pump Mode",
            None,
            None,
            state_class="none",
            diagnostic=True,
            options={0: "Manual", 1: "Auto"},
        )
        self.assertEqual(pump_mode.native_value, "Auto")
        self.assertIsNone(pump_mode.state_class)
        self.assertEqual(pump_mode.entity_category, EntityCategory.DIAGNOSTIC)

        model_sel = SPRSUNSensor(
            self.coordinator,
            self.config_entry,
            "f56_model_selection",
            "F56 Model Selection",
            None,
            None,
            state_class="none",
            diagnostic=True,
            options={1: "A102508"},
        )
        self.assertEqual(model_sel.native_value, "Unknown (99)")

        h01 = SPRSUNSensor(
            self.coordinator,
            self.config_entry,
            "h01_defrost_freq",
            "H01 Defrost Frequency",
            "Hz",
            "frequency",
            state_class="none",
            diagnostic=True,
        )
        self.assertEqual(str(h01.device_class), "frequency")
        self.assertIsNone(h01.state_class)


if __name__ == "__main__":
    unittest.main()
