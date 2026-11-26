"""Unit tests for heat pump controllers (Chico and base)."""
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


class TestControllers(unittest.TestCase):
    """Test suite for controller abstractions and implementations."""

    def test_get_controller_chico(self):
        """Test getting Chico controller instance."""
        controller = get_controller("chico")
        self.assertIsInstance(controller, ChicoController)
        self.assertEqual(controller.name, "CHICO")
        self.assertIn("SPRSUN", controller.manufacturer)

    def test_get_controller_carel_unsupported(self):
        """Test getting Carel controller raises ValueError as it is not supported."""
        with self.assertRaises(ValueError):
            get_controller("carel")

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

    def test_detect_controller_type_none(self):
        """Test detection returning None when Chico check fails."""
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
        regs[0x002C] = 590   # controller_version = 590
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

    def test_chico_read_all_registers_adc_noise_clamping(self):
        """Test small negative ADC noise on current sensors (0xFFFF / 65535) is clamped to 0."""
        controller = ChicoController()
        client = MagicMock()

        response = MagicMock()
        response.isError.return_value = False

        regs = [0] * 50
        regs[0x002C] = 590    # controller_version
        regs[0x000E] = 250    # inlet_temp = 25.0 °C
        regs[0x001A] = 65535  # ac_current = -1 signed int16 (ADC noise around 0)
        regs[0x0023] = 65534  # compressor_current = -2 signed int16 (ADC noise around 0)
        response.registers = regs

        client.read_holding_registers.return_value = response

        data = controller.read_all_registers(client, device_address=1, initial_read=False)

        # Negative noise should be clamped to 0.0
        self.assertEqual(data["ac_current"], 0.0)
        self.assertEqual(data["compressor_current"], 0.0)

        # Positive current values should be preserved
        regs[0x001A] = 12
        regs[0x0023] = 8
        data_pos = controller.read_all_registers(client, device_address=1, initial_read=False)
        self.assertEqual(data_pos["ac_current"], 12.0)
        self.assertEqual(data_pos["compressor_current"], 8.0)

    def test_chico_read_all_registers_corrupt_all_zeros(self):
        """Test corrupt zero-filled frame from RS485 gateway raises ValueError."""
        controller = ChicoController()
        client = MagicMock()

        response = MagicMock()
        response.isError.return_value = False
        response.registers = [0] * 50
        client.read_holding_registers.return_value = response

        with self.assertRaises(ValueError) as ctx:
            controller.read_all_registers(client, device_address=1, initial_read=False)
        self.assertIn("Corrupt Modbus frame detected", str(ctx.exception))

    def test_chico_read_all_registers_corrupt_zero_version_and_water_temps(self):
        """Test zero controller version and simultaneous zero water temps raises ValueError."""
        controller = ChicoController()
        client = MagicMock()

        response = MagicMock()
        response.isError.return_value = False
        regs = [10] * 50
        regs[0x002C] = 0  # controller_version = 0
        regs[0x000E] = 0  # inlet_temp = 0
        regs[0x000F] = 0  # hotwater_temp = 0
        regs[0x0012] = 0  # outlet_temp = 0
        response.registers = regs
        client.read_holding_registers.return_value = response

        with self.assertRaises(ValueError) as ctx:
            controller.read_all_registers(client, device_address=1, initial_read=False)
        self.assertIn("Corrupt Modbus frame detected", str(ctx.exception))

    def test_chico_read_all_registers_short_frame(self):
        """Test incomplete RO frame (<50 registers) raises ValueError."""
        controller = ChicoController()
        client = MagicMock()

        response = MagicMock()
        response.isError.return_value = False
        response.registers = [10] * 40  # only 40 registers instead of 50
        client.read_holding_registers.return_value = response

        with self.assertRaises(ValueError) as ctx:
            controller.read_all_registers(client, device_address=1, initial_read=False)
        self.assertIn("expected 50 registers", str(ctx.exception))

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
                regs = [0] * 50
                regs[0x002C] = 590  # controller_version
                regs[0x000E] = 250  # inlet_temp
                res.registers = regs
            elif address == 0x0032:  # Batch 1 (0x0032-0x0036): 5 registers
                res.registers = [1, 0, 0, 0, 3]
            elif address == 0x0169:  # Batch 3: E01-E24 + G08-G03 (29 registers)
                # First register negative ambient: -15°C -> 65521
                res.registers = [65521] + [0] * 28
            else:
                res.registers = [0] * count
            return res

        client.read_holding_registers.side_effect = mock_read

        with patch("time.sleep"):  # Speed up test
            data = controller.read_all_registers(client, device_address=1, initial_read=True)

        self.assertEqual(data["_control_0032"], 1)
        self.assertEqual(data["unit_mode"], 3)
        self.assertEqual(data["econ_heat_ambi_1"], -15)

    def test_chico_rw_batch_size_mismatch_resets_connection(self):
        """Test batch register count mismatch triggers client.close() and breaks loop."""
        controller = ChicoController()
        client = MagicMock()

        def mock_read(address, count, device_id):
            res = MagicMock()
            res.isError.return_value = False
            if address == 0x0000:
                regs = [0] * 50
                regs[0x002C] = 590
                regs[0x000E] = 250
                res.registers = regs
            elif address == 0x0032:
                # Batch 1 expects count=5, but gateway returned truncated response with 2 registers
                res.registers = [1, 0]
            else:
                res.registers = [0] * count
            return res

        client.read_holding_registers.side_effect = mock_read

        with patch("time.sleep"):
            data = controller.read_all_registers(client, device_address=1, initial_read=True)

        # Connection should be safely reset to prevent stream desynchronization
        client.close.assert_called_once()
        # Loop was broken: subsequent batches (e.g. 0x0036 unit_mode) should not be read
        self.assertNotIn("unit_mode", data)
        # RO data read before the mismatch should remain intact
        self.assertEqual(data["inlet_temp"], 25.0)

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

    def test_chico_read_expert_registers_scaling_signed_and_optional_gap(self):
        """Test expert parameters decode signed, offset, bit_mask, scaled values & tolerate optional gap errors."""
        controller = ChicoController()
        client = MagicMock()

        def mock_read(address, count, device_id):
            res = MagicMock()
            if address in (0x006A, 0x0072):
                # Simulate firmware rejecting Invalid gaps with IllegalDataAddress
                res.isError.return_value = True
                return res
            res.isError.return_value = False
            regs = [0] * count
            if address == 0x0000:
                regs[0x002C] = 590
                regs[0x000E] = 250
            elif address == 0x0032:
                regs[0x0032 - address] = 0b00100011  # power, MV manual, AV manual
                regs[0x0033 - address] = 0b00010001  # r29=1, b74=0(inv->True), d01=1
                regs[0x0035 - address] = 0b00000101  # tb1, tb3
            elif address == 0x0037:
                regs[0x0037 - address] = 75         # h01 = 75 Hz
                regs[0x003B - address] = 10         # h15 = 10 * 5 = 50 min
                regs[0x003F - address] = 120        # a14 = 120 * 2 = 240 steps
            elif address == 0x0078:
                regs[0x0082 - address] = 12         # f02 = (12 + 250) * 0.1 = 26.2 bar
                regs[0x0084 - address] = 35         # f04 = 35 * 0.1 = 3.5 bar
            elif address == 0x00B6:
                regs[0x00D4 - address] = 65526      # h03 = -10 °C (INT16)
                regs[0x00DC - address] = 65532      # a02 = -4 °C (INT16)
            elif address == 0x0186:
                regs[0x0186 - address] = 1          # f13 = 1 (Auto)
                regs[0x01A3 - address] = 65511      # f41 = -25 °C (INT16)
                regs[0x01A4 - address] = 0x0244     # tb1 hw: upper byte 0x02 ignored, low byte 0x44=68 -> 34.0 °C
                regs[0x01B1 - address] = 65         # h18 = 65 * 10 = 650 rpm
                regs[0x01BB - address] = 45         # r94 = 45 Hz
            res.registers = regs
            return res

        client.read_holding_registers.side_effect = mock_read
        with patch("time.sleep"):
            data = controller.read_all_registers(client, device_address=1, initial_read=True)

        self.assertEqual(data["_control_0033"], 0b00010001)
        self.assertEqual(data["_control_0035"], 0b00000101)
        self.assertEqual(data["h01_defrost_freq"], 75)
        self.assertEqual(data["h15_comp_total_run"], 50)
        self.assertEqual(data["a14_mv_heat_initial_0"], 240)
        self.assertEqual(data["f02_hp_protect_value"], 26.2)
        self.assertEqual(data["f04_lp_protect_value"], 3.5)
        self.assertEqual(data["h03_defrost_in_stp"], -10)
        self.assertEqual(data["a02_mv_heating_sh_1"], -4)
        self.assertEqual(data["f13_dc_pump_mode"], 1)
        self.assertEqual(data["f41_air_too_low_stp"], -25)
        self.assertEqual(data["timeband_1_hotwater_setp"], 34.0)
        self.assertEqual(data["h18_def_fan_speed"], 650)
        self.assertEqual(data["r94_oil_return_freq"], 45)
        self.assertNotIn("b21_av_heat_initial_2", data)

    def test_chico_spec_integrity_and_batch_coverage(self):
        """Verify all CHICO keys, addresses are unique and covered by read batches."""
        controller = ChicoController()
        all_specs = (
            controller.get_sensors()
            + controller.get_expert_sensors()
            + controller.get_binary_sensors()
            + controller.get_expert_binary_sensors()
            + controller.get_numbers()
            + controller.get_selects()
            + controller.get_switches()
            + controller.get_buttons()
        )
        keys = [s.key for s in all_specs]
        self.assertEqual(len(keys), len(set(keys)), "Duplicate CHICO entity key detected")

        from custom_components.sprsun_modbus.controllers.chico_registers import (
            CHICO_OPTIONAL_RW_BATCHES,
            CHICO_RO_BATCH,
            CHICO_RW_BATCHES,
        )
        word_specs = (
            controller.get_sensors()
            + controller.get_expert_sensors()
            + controller.get_numbers()
            + controller.get_selects()
        )
        addrs = [s.address for s in word_specs]
        self.assertEqual(len(addrs), len(set(addrs)), "Duplicate CHICO word register address detected")

        covered = set()
        for batch in (CHICO_RO_BATCH,) + CHICO_RW_BATCHES + CHICO_OPTIONAL_RW_BATCHES:
            for addr in range(batch.start_address, batch.start_address + batch.count):
                covered.add(addr)
        for spec in word_specs:
            self.assertIn(spec.address, covered, f"Address 0x{spec.address:04X} ({spec.key}) not covered by batch")

        by_key = {spec.key: spec for spec in controller.get_sensors() + controller.get_expert_sensors()}
        self.assertEqual(by_key["dc_pump_speed"].unit, "%")
        self.assertEqual(by_key["d05_cool_dcfan_high_press"].unit, "bar")
        self.assertEqual(by_key["d06_cool_dcfan_open_diff"].device_class, "pressure")
        self.assertEqual(by_key["d16_dcfan_adjust_speed_1"].unit, "rpm")
        self.assertEqual(by_key["a44_mv_water_lower"].min_value, 0)
        self.assertEqual(by_key["f40_wt_constant_temp_diff"].min_value, 0)
        self.assertEqual(by_key["timeband_1_weekday"].max_value, 127)

    def test_chico_primary_setpoints_mask_upper_byte_on_read(self):
        """Test P01/P02/P04 decode only the lower 8 bits even when upper byte is non-zero."""
        controller = ChicoController()
        client = MagicMock()

        def mock_read(address, count, device_id):
            res = MagicMock()
            res.isError.return_value = False
            regs = [0] * count
            if address == 0x0000:
                regs[0x002C] = 590
                regs[0x000E] = 250
            elif address == 0x00B6:
                regs[0x00CA - address] = 0x8160  # upper byte 0x81 ignored, low byte 0x60=96 -> 48.0 C
                regs[0x00CB - address] = 0x0424  # upper byte 0x04 ignored, low byte 0x24=36 -> 18.0 C
                regs[0x00CC - address] = 0xFF39  # upper byte 0xFF ignored, low byte 0x39=57 -> 28.5 C
            res.registers = regs
            return res

        client.read_holding_registers.side_effect = mock_read
        with patch("time.sleep"):
            data = controller.read_all_registers(client, device_address=1, initial_read=True)

        self.assertEqual(data["hotwater_setpoint"], 48.0)
        self.assertEqual(data["cooling_setpoint"], 18.0)
        self.assertEqual(data["heating_setpoint"], 28.5)


if __name__ == "__main__":
    unittest.main()
