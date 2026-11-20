"""Unit tests for heat pump controllers (Chico, Carel, and base)."""
import unittest
from unittest.mock import MagicMock, patch

from tests.conftest import setup_mocks
setup_mocks()

from custom_components.sprsun_modbus.controllers import (
    get_controller,
    detect_controller_type,
    ControllerBase,
)
from custom_components.sprsun_modbus.controllers.chico import ChicoController
from custom_components.sprsun_modbus.controllers.carel import CarelController


class TestControllers(unittest.TestCase):
    """Test suite for controller abstractions and implementations."""

    def test_get_controller_chico(self):
        """Test getting Chico controller instance."""
        controller = get_controller("chico")
        self.assertIsInstance(controller, ChicoController)
        self.assertEqual(controller.name, "CHICO")
        self.assertIn("SPRSUN", controller.manufacturer)

    def test_get_controller_carel(self):
        """Test getting Carel controller instance."""
        controller = get_controller("carel")
        self.assertIsInstance(controller, CarelController)
        self.assertEqual(controller.name, "CAREL")

    def test_get_controller_unknown(self):
        """Test getting unknown controller raises ValueError."""
        with self.assertRaises(ValueError):
            get_controller("unknown_type")

    def test_detect_controller_type_chico(self):
        """Test auto-detecting Chico controller."""
        client = MagicMock()
        
        # When Chico detection runs, it reads address 0x002C, count 2
        response = MagicMock()
        response.isError.return_value = False
        response.registers = [105, 102]  # valid controller and display versions
        client.read_holding_registers.return_value = response

        detected = detect_controller_type(client, device_address=1)
        self.assertEqual(detected, "chico")

    def test_detect_controller_type_carel(self):
        """Test auto-detecting Carel controller when Chico detection fails."""
        client = MagicMock()
        
        # Chico check (0x002C) fails, Carel check (325) succeeds
        def mock_read(address, count, device_id):
            res = MagicMock()
            if address == 0x002C:
                res.isError.return_value = True
            elif address == 325:
                res.isError.return_value = False
                res.registers = [1, 2, 3]  # Version 1.2.3
            else:
                res.isError.return_value = True
            return res

        client.read_holding_registers.side_effect = mock_read
        detected = detect_controller_type(client, device_address=1)
        self.assertEqual(detected, "carel")

    def test_detect_controller_type_none(self):
        """Test detection returning None when all checks fail."""
        client = MagicMock()
        res = MagicMock()
        res.isError.return_value = True
        client.read_holding_registers.return_value = res

        detected = detect_controller_type(client, device_address=1)
        self.assertIsNone(detected)

    def test_chico_platforms_and_device_info(self):
        """Test Chico supported platforms and device info dictionary."""
        controller = ChicoController()
        platforms = controller.get_platforms()
        self.assertIn("sensor", platforms)
        self.assertIn("binary_sensor", platforms)
        self.assertIn("climate", platforms)

        device_info = controller.get_device_info("entry_test_1")
        self.assertIn(("sprsun_modbus", "entry_test_1"), device_info["identifiers"])
        self.assertEqual(device_info["manufacturer"], "SPRSUN")
        self.assertIn("CHICO", device_info["model"])

    def test_chico_read_all_registers_ro_and_signed(self):
        """Test reading RO registers with signed integer conversions."""
        controller = ChicoController()
        client = MagicMock()

        response = MagicMock()
        response.isError.return_value = False
        
        # 50 registers
        regs = [0] * 50
        regs[0x000E] = 250   # inlet_temp = 25.0 °C
        regs[0x0011] = 65516 # ambient_temp = -20 * 0.5 = -10.0 °C (signed)
        regs[0x0015] = 65526 # suction_gas_temp = -10 * 0.5 = -5.0 °C (signed)
        regs[0x0016] = 65530 # coil_temp = -6 * 0.5 = -3.0 °C (signed)
        regs[0x0022] = 80    # driving_temp = 80 * 0.5 = 40.0 °C (positive signed)
        regs[0x0028] = 65516 # evap_temp = -20 * 0.1 = -2.0 °C (signed)
        regs[0x0003] = 0b00000011 # working_status_register
        regs[0x0004] = 0b00000001 # output_symbol_1
        response.registers = regs

        client.read_holding_registers.return_value = response

        data = controller.read_all_registers(client, device_address=1, initial_read=False)

        self.assertAlmostEqual(data["inlet_temp"], 25.0)
        self.assertAlmostEqual(data["ambient_temp"], -10.0)
        self.assertAlmostEqual(data["suction_gas_temp"], -5.0)
        self.assertAlmostEqual(data["coil_temp"], -3.0)
        self.assertAlmostEqual(data["driving_temp"], 40.0)
        self.assertAlmostEqual(data["evap_temp"], -2.0)
        self.assertEqual(data["working_status_register"], 0b00000011)
        self.assertEqual(data["output_symbol_1"], 0b00000001)

    def test_chico_read_all_registers_ro_error(self):
        """Test handling of Modbus error on RO read."""
        controller = ChicoController()
        client = MagicMock()

        response = MagicMock()
        response.isError.return_value = True
        client.read_holding_registers.return_value = response

        with self.assertRaises(ValueError):
            controller.read_all_registers(client, device_address=1, initial_read=False)

    def test_chico_read_rw_batches_on_initial_read(self):
        """Test reading RW register batches on initial read."""
        controller = ChicoController()
        client = MagicMock()

        def mock_read(address, count, device_id):
            res = MagicMock()
            res.isError.return_value = False
            # Return all zeros or dummy values matching count
            if address == 0x0000:
                res.registers = [0] * 50
            elif address == 0x0032:  # Batch 1 (0x0032-0x0034): 3 registers
                res.registers = [1, 0, 3]
            elif address == 0x0036:  # Batch 2: P06
                res.registers = [3]  # Heat + DHW
            elif address == 0x0169:  # Batch 4: E01-E12 (12 registers)
                # First register negative ambient: -15°C -> 65521
                res.registers = [65521] + [0] * 11
            else:
                res.registers = [0] * count
            return res

        client.read_holding_registers.side_effect = mock_read

        with patch("time.sleep"):  # Speed up test
            data = controller.read_all_registers(client, device_address=1, initial_read=True)

        self.assertEqual(data["_control_0032"], 1)
        self.assertEqual(data["unit_mode"], 3)
        self.assertEqual(data["econ_heat_ambi_1"], -15)

    def test_chico_write_register_success(self):
        """Test successful Chico register write."""
        controller = ChicoController()
        client = MagicMock()
        client.connected = True
        res = MagicMock()
        res.isError.return_value = False
        client.write_register.return_value = res

        result = controller.write_register(client, device_address=1, address=0x00CC, value=76)
        self.assertTrue(result)
        client.write_register.assert_called_once_with(address=0x00CC, value=76, device_id=1)

    def test_chico_write_register_disconnected_reconnects(self):
        """Test write_register reconnects if client disconnected."""
        controller = ChicoController()
        client = MagicMock()
        client.connected = False
        client.connect.return_value = True
        res = MagicMock()
        res.isError.return_value = False
        client.write_register.return_value = res

        result = controller.write_register(client, device_address=1, address=0x00CC, value=76)
        self.assertTrue(result)
        client.connect.assert_called_once()

    def test_chico_write_register_error(self):
        """Test write_register raises ValueError on Modbus error response."""
        controller = ChicoController()
        client = MagicMock()
        client.connected = True
        res = MagicMock()
        res.isError.return_value = True
        client.write_register.return_value = res

        with self.assertRaises(ValueError):
            controller.write_register(client, device_address=1, address=0x00CC, value=76)

    def test_carel_stubs(self):
        """Test Carel placeholder methods handle gracefully."""
        controller = CarelController()
        client = MagicMock()

        self.assertEqual(controller.read_all_registers(client, 1), {})
        self.assertFalse(controller.write_register(client, 1, 0x0001, 10))
        self.assertIn("CAREL", controller.get_device_info("entry_carel")["model"])


if __name__ == "__main__":
    unittest.main()
