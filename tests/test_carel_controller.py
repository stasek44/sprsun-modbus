"""Unit tests for the CAREL heat pump controller driver and protocol behaviors."""
from __future__ import annotations

import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import setup_mocks

setup_mocks()

from homeassistant.components.climate import HVACAction, HVACMode  # noqa: E402
from homeassistant.const import CONF_NAME  # noqa: E402
from homeassistant.exceptions import HomeAssistantError  # noqa: E402

from custom_components.sprsun_modbus import SPRSUNDataUpdateCoordinator  # noqa: E402
from custom_components.sprsun_modbus.climate import _round_to_step as climate_round  # noqa: E402
from custom_components.sprsun_modbus.controllers import (  # noqa: E402
    CarelController,
    RegisterSpace,
    detect_controller_type,
    get_controller,
    get_supported_controllers,
)
from custom_components.sprsun_modbus.controllers.carel import (  # noqa: E402
    _decode_alarm_bits,
    _interpolate_eco_curve,
)
from custom_components.sprsun_modbus.controllers.modbus_helpers import (  # noqa: E402
    decode_batch_into_data,
)
from custom_components.sprsun_modbus.number import _round_to_step as number_round  # noqa: E402
from custom_components.sprsun_modbus.select import SPRSUNSelect  # noqa: E402
from custom_components.sprsun_modbus.sensor import SPRSUNSensor  # noqa: E402
from custom_components.sprsun_modbus.switch import SPRSUNSwitch  # noqa: E402


def _make_reg_res(registers: list[int], error: bool = False) -> MagicMock:
    res = MagicMock()
    res.isError.return_value = error
    res.registers = registers
    return res


def _make_bit_res(bits: list[bool], error: bool = False) -> MagicMock:
    res = MagicMock()
    res.isError.return_value = error
    res.bits = bits
    return res


class TestCarelDetectionAndPolling(unittest.TestCase):
    """Test CAREL detection, polling batches, signed decoding, and alarm aggregation."""

    def test_registry_includes_carel_after_chico(self) -> None:
        supported = get_supported_controllers()
        self.assertEqual(supported[0], "chico")
        self.assertIn("carel", supported)
        ctrl = get_controller("carel")
        self.assertIsInstance(ctrl, CarelController)
        self.assertEqual(ctrl.name, "CAREL")

    def test_detect_carel_valid_and_rejects_zeros(self) -> None:
        client = MagicMock()

        def read_hr(address: int, count: int, device_id: int = 1):
            if address == 0x002C:  # CHICO probe fails
                return _make_reg_res([], error=True)
            if address == 0 and count == 4:
                return _make_reg_res([4, 380, 180, 480])  # Heat+DHW, 38.0°C, 18.0°C, 48.0°C
            if address == 215 and count == 3:
                return _make_reg_res([1, 380, 1])  # run_mode=Heating, target=38.0, status=Unit ON
            return _make_reg_res([], error=True)

        client.read_holding_registers.side_effect = read_hr
        client.read_discrete_inputs.return_value = _make_bit_res([True, False, False, False, False, False, False, False])

        self.assertTrue(CarelController.detect(client, 1))
        self.assertEqual(detect_controller_type(client, 1), "carel")

        # All-zero dummy registers must be rejected
        zero_client = MagicMock()
        zero_client.read_holding_registers.return_value = _make_reg_res([0, 0, 0, 0])
        zero_client.read_discrete_inputs.return_value = _make_bit_res([False] * 8)
        self.assertFalse(CarelController.detect(zero_client, 1))

    def test_probe_connection(self) -> None:
        client = MagicMock()
        client.read_holding_registers.return_value = _make_reg_res([6])  # OFF by Keyboard
        client.read_discrete_inputs.return_value = _make_bit_res([False] * 8)
        self.assertTrue(CarelController.probe_connection(client, 1))

        client.read_holding_registers.return_value = _make_reg_res([99])  # Invalid status
        self.assertFalse(CarelController.probe_connection(client, 1))

    def test_read_all_registers_ro_and_rw_with_negative_int16_and_alarms(self) -> None:
        ctrl = CarelController()
        client = MagicMock()

        # Holding 188..217 (30 regs)
        telemetry = [0] * 30
        telemetry[188 - 188] = 312    # inlet_temp = 31.2 °C
        telemetry[189 - 188] = 358    # outlet_temp = 35.8 °C
        telemetry[190 - 188] = 65486  # ambient_temp = -50 -> -5.0 °C (INT16)
        telemetry[193 - 188] = 142    # discharge_pressure = 14.2 bar
        telemetry[194 - 188] = 78     # suction_pressure = 7.8 bar
        telemetry[195 - 188] = 465    # hotwater_temp = 46.5 °C
        telemetry[196 - 188] = 65456  # coil_temp = -80 -> -8.0 °C (INT16)
        telemetry[197 - 188] = 512    # fan_output = 51.2 %
        telemetry[200 - 188] = 440    # fan1_rpm_feedback = 440 rpm
        telemetry[205 - 188] = 363    # compressor_speed = 36.3 rps
        telemetry[215 - 188] = 1      # unit_run_mode = Heating
        telemetry[216 - 188] = 360    # target_temp = 36.0 °C
        telemetry[217 - 188] = 1      # unit_status = Unit ON

        # Holding 0..15 (16 regs)
        rw_core = [4, 380, 180, 480, 50, 10, 30, 10, 20, 120, 5, 1, 2, 30, 65486, 50]

        def read_hr(address: int, count: int, device_id: int = 1):
            if address == 188 and count == 30:
                return _make_reg_res(telemetry)
            if address == 333 and count == 3:
                return _make_reg_res([12, 230, 55])  # 1200 W, 230 V, 5.5 A
            if address == 0 and count == 16:
                return _make_reg_res(rw_core)
            if address == 323 and count == 7:
                return _make_reg_res([2, 0, 1, 5, 3, 40, 2])
            return _make_reg_res([], error=True)

        # Alarm bits DI 13..177: set DI 141 (AL129 High pressure alarm)
        alarm_bits = [False] * 165
        alarm_bits[141 - 13] = True

        def read_di(address: int, count: int, device_id: int = 1):
            if address == 0 and count == 13:
                bits = [False] * 16
                bits[0] = True   # unit_on
                bits[1] = True   # flow_switch
                bits[8] = True   # pump_output_relay
                bits[11] = False # three_way_valve
                return _make_bit_res(bits)
            if address == 178 and count == 6:
                return _make_bit_res([True, True, True, False, False, False, False, False])
            if address == 13 and count == 165:
                return _make_bit_res(alarm_bits)
            return _make_bit_res([], error=True)

        def read_coils(address: int, count: int, device_id: int = 1):
            if address == 40 and count == 1:
                return _make_bit_res([True] + [False] * 7)
            if address == 0 and count == 43:
                coils = [False] * 48
                coils[40] = True   # power ON
                coils[42] = False  # dhw_enable active-low -> raw False means ON!
                return _make_bit_res(coils)
            return _make_bit_res([], error=True)

        client.read_holding_registers.side_effect = read_hr
        client.read_discrete_inputs.side_effect = read_di
        client.read_coils.side_effect = read_coils

        with patch("time.sleep"):
            data = ctrl.read_all_registers(client, device_address=1, initial_read=True)

        self.assertAlmostEqual(data["inlet_temp"], 31.2)
        self.assertAlmostEqual(data["outlet_temp"], 35.8)
        self.assertAlmostEqual(data["ambient_temp"], -5.0)
        self.assertAlmostEqual(data["coil_temp"], -8.0)
        self.assertAlmostEqual(data["discharge_pressure"], 14.2)
        self.assertEqual(data["bldc_power"], 1200)
        self.assertEqual(data["bldc_voltage"], 230)
        self.assertAlmostEqual(data["bldc_current"], 5.5)
        self.assertAlmostEqual(data["aux_heat_ambient_setpoint"], -5.0)
        self.assertTrue(data["unit_on"])
        self.assertTrue(data["compressor_running"])
        self.assertTrue(data["power"])
        self.assertFalse(data["dhw_enable"])  # raw coil stored; switch applies inverted=True
        self.assertTrue(data["alarm_active"])
        self.assertEqual(data["active_alarms"], "AL129: High pressure alarm")
        self.assertEqual(data["active_alarms_list"], ["AL129: High pressure alarm"])
        self.assertTrue(ctrl.has_rw_data(data))

    def test_decode_alarm_bits_none_and_multiple(self) -> None:
        active, summary, items = _decode_alarm_bits([False] * 165)
        self.assertFalse(active)
        self.assertEqual(summary, "None")
        self.assertEqual(items, [])

        bits = [False] * 165
        bits[19 - 13] = True   # AL007 Water flow switch
        bits[141 - 13] = True  # AL129 High pressure alarm
        active, summary, items = _decode_alarm_bits(bits)
        self.assertTrue(active)
        self.assertEqual(summary, "AL007: Water flow switch (+1 more)")
        self.assertEqual(len(items), 2)

    def test_round_to_step_0_1_has_no_float_artifacts(self) -> None:
        self.assertEqual(number_round(22.3, 0.1), 22.3)
        self.assertEqual(climate_round(22.3, 0.1), 22.3)
        self.assertEqual(number_round(26.3, 0.1), 26.3)

    def test_derived_sensors_water_delta_t_and_eco_curve(self) -> None:
        ctrl = CarelController()
        data = {
            "inlet_temp": {"value": 30.0},
            "outlet_temp": {"value": 34.6},
            "ambient_temp": {"value": 0.0},
            "eco_heat_x1": {"value": -15.0},
            "eco_heat_x2": {"value": -5.0},
            "eco_heat_x3": {"value": 5.0},
            "eco_heat_x4": {"value": 15.0},
            "eco_heat_y1": {"value": 45.0},
            "eco_heat_y2": {"value": 40.0},
            "eco_heat_y3": {"value": 34.0},
            "eco_heat_y4": {"value": 28.0},
        }
        derived = ctrl.compute_derived_data(data)
        self.assertEqual(derived["water_delta_t"], 4.6)
        # Ambient 0.0 is halfway between -5.0 (40.0°C) and 5.0 (34.0°C) -> 37.0°C
        self.assertEqual(derived["eco_heating_setpoint"], 37.0)
        self.assertIsNone(derived["eco_cooling_setpoint"])
        # Clamping below X1
        data["ambient_temp"] = {"value": -25.0}
        self.assertEqual(_interpolate_eco_curve(data, "eco_heat"), 45.0)
        # Clamping above X4
        data["ambient_temp"] = {"value": 25.0}
        self.assertEqual(_interpolate_eco_curve(data, "eco_heat"), 28.0)


class TestCarelWritesAndClimate(unittest.IsolatedAsyncioTestCase):
    """Test CAREL inverted coil switches, safe mode-switch sequence, and climate control."""

    def setUp(self) -> None:
        self.ctrl = CarelController()
        self.entry = MagicMock()
        self.entry.entry_id = "carel_test"
        self.entry.data = {CONF_NAME: "SPRSUN CAREL"}
        self.entry.options = {}

    async def test_inverted_coil_switch_no_double_inversion_end_to_end(self) -> None:
        """Verify Coil 42 (dhw_enable, inverted=True) decodes & writes cleanly end-to-end."""
        dhw_spec = next(s for s in self.ctrl.get_switches() if s.key == "dhw_enable")
        raw_cache: dict = {}
        # Hardware Coil 42 = False (0) means Hot Water ON
        decode_batch_into_data(self.ctrl.get_switches(), RegisterSpace.COIL, 42, [False], raw_cache)
        self.assertFalse(raw_cache["dhw_enable"])

        coord = MagicMock()
        coord.controller = self.ctrl
        coord.last_update_success = True
        coord.data = {"dhw_enable": {"value": raw_cache["dhw_enable"], "updated_at": time.time()}}
        coord.async_write_coil = AsyncMock()

        sw = SPRSUNSwitch(
            coord,
            self.entry,
            dhw_spec.key,
            dhw_spec.name,
            dhw_spec.address,
            dhw_spec.bit,
            space=dhw_spec.space,
            is_config=dhw_spec.is_config,
            inverted=dhw_spec.inverted,
        )
        # Raw False + inverted=True -> HA switch is ON
        self.assertTrue(sw.is_on)

        # Turning OFF writes hardware True (1 = Hot Water OFF)
        await sw.async_turn_off()
        coord.async_write_coil.assert_called_with(42, True, key="dhw_enable")

        # Turning ON writes hardware False (0 = Hot Water ON)
        await sw.async_turn_on()
        coord.async_write_coil.assert_called_with(42, False, key="dhw_enable")

    async def test_select_unit_mode_triggers_safe_power_cycle_when_running(self) -> None:
        """Changing Holding 0 via select while running must cycle Coil 40 OFF -> write -> ON."""
        coord = MagicMock()
        coord.controller = self.ctrl
        coord.last_update_success = True
        coord.data = {"unit_mode": {"value": 1, "updated_at": time.time()}}
        coord.async_read_register = AsyncMock(return_value=1)  # currently Heating
        coord.async_read_coil = AsyncMock(return_value=True)   # currently ON

        call_order: list[tuple] = []

        async def record_coil(address, value, key=None):
            call_order.append(("coil", address, value))

        async def record_reg(address, value, key, scale=1, cached_value=None):
            call_order.append(("reg", address, int(value)))

        coord.async_write_coil = AsyncMock(side_effect=record_coil)
        coord.async_write_register = AsyncMock(side_effect=record_reg)

        mode_spec = next(s for s in self.ctrl.get_selects() if s.key == "unit_mode")
        sel = SPRSUNSelect(coord, self.entry, mode_spec.key, mode_spec.name, mode_spec.address, mode_spec.options)
        await sel.async_select_option("Heating + Hot Water")

        self.assertEqual(
            call_order,
            [
                ("coil", 40, False),
                ("reg", 0, 4),
                ("coil", 40, True),
            ],
        )

    async def test_climate_space_and_dhw_modes_actions_and_writes(self) -> None:
        now = time.time()
        data = {
            "power": {"value": True, "updated_at": now},
            "unit_mode": {"value": 4, "updated_at": now},  # Heating + Hot Water
            "unit_run_mode": {"value": 1, "updated_at": now},  # Heating active
            "compressor_running": {"value": True, "updated_at": now},
            "inlet_temp": {"value": 32.5, "updated_at": now},
            "hotwater_temp": {"value": 45.0, "updated_at": now},
            "heating_setpoint": {"value": 38.0, "updated_at": now},
            "cooling_setpoint": {"value": 18.0, "updated_at": now},
            "hotwater_setpoint": {"value": 48.0, "updated_at": now},
            "fan_mode": {"value": 2, "updated_at": now},
        }
        self.assertEqual(self.ctrl.get_space_hvac_mode(data), HVACMode.HEAT)
        self.assertEqual(self.ctrl.get_space_hvac_action(data), HVACAction.HEATING)
        self.assertEqual(self.ctrl.get_space_target_temp(data), 38.0)
        self.assertEqual(self.ctrl.get_space_fan_mode(data), "eco")
        self.assertEqual(self.ctrl.get_dhw_hvac_mode(data), HVACMode.HEAT)
        self.assertEqual(self.ctrl.get_dhw_hvac_action(data), HVACAction.IDLE)

        # Turning space OFF while in Heat+DHW switches to DHW-only (2) keeping power ON
        coord = MagicMock()
        coord.async_read_register = AsyncMock(return_value=4)
        coord.async_read_coil = AsyncMock(return_value=True)
        coord.async_write_coil = AsyncMock()
        coord.async_write_register = AsyncMock()

        await self.ctrl.async_set_space_hvac_mode(coord, HVACMode.OFF, data)
        coord.async_write_register.assert_called_once_with(address=0, value=2.0, key="unit_mode", scale=1)

        # Writing space temperature in cooling mode writes Holding 2 with INT16 scale 0.1
        coord.async_read_register = AsyncMock(return_value=0)
        coord.async_write_register.reset_mock()
        await self.ctrl.async_set_space_temperature(coord, 18.5, data)
        coord.async_write_register.assert_called_once_with(
            address=2, value=185.0, key="cooling_setpoint", scale=1, cached_value=18.5
        )

        # Writing DHW temperature writes Holding 3 with INT16 scale 0.1
        coord.async_write_register.reset_mock()
        await self.ctrl.async_set_dhw_temperature(coord, 50.5)
        coord.async_write_register.assert_called_once_with(
            address=3, value=505.0, key="hotwater_setpoint", scale=1, cached_value=50.5
        )

    async def test_active_alarms_sensor_exposes_extra_attributes(self) -> None:
        coord = MagicMock()
        coord.controller = self.ctrl
        coord.last_update_success = True
        coord.data = {
            "active_alarms": {"value": "AL129: High pressure alarm", "updated_at": 100.0},
            "active_alarms_list": {"value": ["AL129: High pressure alarm"], "updated_at": 100.0},
        }
        sensor = SPRSUNSensor(coord, self.entry, "active_alarms", "Active Alarms", None, None, diagnostic=True)
        self.assertEqual(sensor.native_value, "AL129: High pressure alarm")
        self.assertEqual(
            sensor.extra_state_attributes,
            {"alarms": ["AL129: High pressure alarm"], "count": 1},
        )

    async def test_coordinator_async_read_coil(self) -> None:
        hass = MagicMock()

        async def run_exec(func, *args, **kwargs):
            return func(*args, **kwargs)

        hass.async_add_executor_job = run_exec
        coord = SPRSUNDataUpdateCoordinator(hass, "192.168.1.50", 502, 1, 10, "carel")
        client = MagicMock()
        client.connected = True
        client.read_coils.return_value = _make_bit_res([True, False, False, False, False, False, False, False])
        coord.client = client

        val = await coord.async_read_coil(40, key="power")
        self.assertTrue(val)
        self.assertTrue(coord.data["power"]["value"])
        client.read_coils.assert_called_once_with(address=40, count=1, device_id=1)

    async def test_offline_coil_read_raises_home_assistant_error(self) -> None:
        coord = MagicMock()
        coord.async_read_register = AsyncMock(return_value=1)
        coord.async_read_coil = AsyncMock(side_effect=ConnectionError("offline"))
        coord.async_write_register = AsyncMock()
        coord.async_write_coil = AsyncMock()

        with self.assertRaises(HomeAssistantError):
            await self.ctrl.async_set_space_hvac_mode(coord, HVACMode.HEAT, {})
        coord.async_write_register.assert_not_called()
        coord.async_write_coil.assert_not_called()


if __name__ == "__main__":
    unittest.main()
