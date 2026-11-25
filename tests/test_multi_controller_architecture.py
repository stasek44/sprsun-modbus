"""Unit tests for the multi-controller architecture, codecs, and protocol helpers."""
import struct
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import setup_mocks

setup_mocks()

from homeassistant.components.climate import HVACAction, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, CONF_PORT, EntityCategory, Platform
from custom_components.sprsun_modbus import (
    SPRSUNDataUpdateCoordinator,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.sprsun_modbus.binary_sensor import async_setup_entry as bs_setup_entry
from custom_components.sprsun_modbus.button import async_setup_entry as button_setup_entry
from custom_components.sprsun_modbus.climate import (
    SPRSUNClimate,
    async_setup_entry as climate_setup_entry,
)
from custom_components.sprsun_modbus.config_flow import validate_connection
from custom_components.sprsun_modbus.const import (
    CONF_CONTROLLER_TYPE,
    CONF_DEVICE_ADDRESS,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    INTER_WRITE_DELAY,
)
from custom_components.sprsun_modbus.controllers import (
    BinarySensorSpec,
    ButtonSpec,
    ClimateCapabilities,
    ControllerBase,
    DataType,
    ModbusBatchSpec,
    NumberSpec,
    RegisterSpace,
    SelectSpec,
    SensorSpec,
    SwitchSpec,
    WordOrder,
    decode_registers,
    encode_registers,
    get_supported_controllers,
    resolve_controller,
)
from custom_components.sprsun_modbus.controllers.modbus_helpers import (
    ModbusBatchError,
    ModbusDesyncError,
    decode_batch_into_data,
    read_modbus_batch,
)
from custom_components.sprsun_modbus.number import async_setup_entry as number_setup_entry
from custom_components.sprsun_modbus.select import async_setup_entry as select_setup_entry
from custom_components.sprsun_modbus.sensor import async_setup_entry as sensor_setup_entry
from custom_components.sprsun_modbus.switch import async_setup_entry as switch_setup_entry


class SyntheticAltController(ControllerBase):
    """Synthetic non-CHICO controller exercising coils, discrete inputs, and 32-bit types."""

    @property
    def name(self) -> str:
        return "ALT"

    @property
    def manufacturer(self) -> str:
        return "SPRSUN (ALT Controller)"

    def get_platforms(self) -> list[str]:
        return ["sensor", "binary_sensor", "number", "select", "switch", "button", "climate"]

    def get_device_info(self, entry_id: str) -> dict:
        return {
            "identifiers": {(DOMAIN, entry_id)},
            "name": "SPRSUN ALT Pump",
            "manufacturer": "SPRSUN",
            "model": "Heat Pump (ALT Controller)",
        }

    @classmethod
    def detect(cls, client, device_address: int) -> bool:
        return False

    def read_all_registers(self, client, device_address: int, initial_read: bool = False) -> dict:
        return {
            "alt_energy": 123.5,
            "alt_power": 2450.0,
            "alt_alarm": True,
            "alt_output_inv": False,
            "alt_coil_switch": True,
            "alt_float_setp": 55.0,
            "alt_mode": 0,
            "alt_inlet": 30.0,
            "alt_unit_on": True,
        }

    def write_register(self, client, device_address: int, address: int, value: int) -> bool:
        return True

    def get_sensors(self) -> tuple[SensorSpec, ...]:
        return (
            SensorSpec(
                key="alt_energy",
                name="Total Energy",
                address=384,
                space=RegisterSpace.HOLDING_REGISTER,
                data_type=DataType.FLOAT32,
                unit="kWh",
                device_class="energy",
                state_class="total_increasing",
            ),
            SensorSpec(
                key="alt_power",
                name="Unit Power",
                address=387,
                space=RegisterSpace.HOLDING_REGISTER,
                data_type=DataType.UINT32,
                unit="W",
                device_class="power",
            ),
        )

    def get_binary_sensors(self) -> tuple[BinarySensorSpec, ...]:
        return (
            BinarySensorSpec(
                key="alt_alarm",
                name="Flow Alarm",
                address=149,
                space=RegisterSpace.DISCRETE_INPUT,
                diagnostic=True,
                device_class="problem",
            ),
            BinarySensorSpec(
                key="alt_output_inv",
                name="Inverted Output",
                address=5,
                space=RegisterSpace.DISCRETE_INPUT,
                inverted=True,
            ),
        )

    def get_numbers(self) -> tuple[NumberSpec, ...]:
        return (
            NumberSpec(
                key="alt_float_setp",
                name="Antilegionella Float Setpoint",
                address=471,
                space=RegisterSpace.HOLDING_REGISTER,
                data_type=DataType.FLOAT32,
                word_order=WordOrder.LITTLE_ENDIAN,
                scale=1.0,
                unit="°C",
                min_value=30.0,
                max_value=70.0,
                step=0.5,
                device_class="temperature",
                is_primary=True,
            ),
        )

    def get_selects(self) -> tuple[SelectSpec, ...]:
        return (
            SelectSpec(
                key="alt_mode",
                name="ALT Mode",
                address=0,
                options={0: "Cooling", 1: "Heating", 2: "DHW"},
                is_config=False,
            ),
        )

    def get_switches(self) -> tuple[SwitchSpec, ...]:
        return (
            SwitchSpec(
                key="alt_coil_switch",
                name="Manual Defrost",
                address=105,
                bit=None,
                space=RegisterSpace.COIL,
                is_config=True,
            ),
        )

    def get_buttons(self) -> tuple[ButtonSpec, ...]:
        return (
            ButtonSpec(
                key="alt_meter_reset",
                name="Reset Energy Meter",
                address=68,
                bit=None,
                space=RegisterSpace.COIL,
                write_value=True,
                diagnostic=True,
            ),
        )

    def get_space_climate_capabilities(self) -> ClimateCapabilities:
        return ClimateCapabilities(
            enabled=True,
            hvac_modes=("off", "heat", "cool"),
            fan_modes=(),
            preset_modes=(),
            supports_target_temperature=True,
            supports_fan_mode=False,
            supports_preset_mode=False,
            min_temp=15.0,
            max_temp=50.0,
            supports_dhw=False,
        )

    def get_space_min_temp(self, hvac_mode) -> float:
        return 12.0 if str(hvac_mode) == "cool" else 15.0

    def get_space_max_temp(self, hvac_mode) -> float:
        return 35.0 if str(hvac_mode) == "cool" else 50.0

    def get_space_hvac_mode(self, data) -> HVACMode:
        if not (data and data.get("alt_unit_on", {}).get("value")):
            return HVACMode.OFF
        mode = (data.get("alt_mode") or {}).get("value", 1)
        return HVACMode.COOL if mode == 0 else HVACMode.HEAT

    def get_space_hvac_action(self, data) -> HVACAction:
        return HVACAction.IDLE

    def get_space_current_temp(self, data) -> float | None:
        return (data or {}).get("alt_inlet", {}).get("value")

    def get_space_target_temp(self, data) -> float | None:
        return (data or {}).get("alt_float_setp", {}).get("value")

    async def async_write_power(self, coordinator, state: bool) -> None:
        await coordinator.async_write_coil(1, state, key="alt_unit_on")

    async def async_set_space_hvac_mode(self, coordinator, hvac_mode, data, write_power_fn=None) -> None:
        writer = write_power_fn or (lambda st: self.async_write_power(coordinator, st))
        if hvac_mode == HVACMode.OFF:
            await writer(False)
        elif hvac_mode == HVACMode.COOL:
            await writer(True)
            await coordinator.async_write_register(address=0, value=0, key="alt_mode", scale=1)
        elif hvac_mode == HVACMode.HEAT:
            await writer(True)
            await coordinator.async_write_register(address=0, value=1, key="alt_mode", scale=1)

    async def async_set_space_temperature(self, coordinator, temperature: float, data) -> None:
        regs = encode_registers(temperature, DataType.FLOAT32, scale=1.0, word_order=WordOrder.LITTLE_ENDIAN)
        await coordinator.async_write_registers(address=471, registers=regs, key="alt_float_setp", value=temperature)


class TestCodecAndModels(unittest.TestCase):
    """Test binary codecs and typed specs."""

    def test_decode_and_encode_16bit(self):
        self.assertEqual(decode_registers([65516], DataType.INT16, scale=0.5), -10.0)
        self.assertEqual(decode_registers([65516], DataType.UINT16, scale=1), 65516)
        self.assertEqual(decode_registers([65535], DataType.INT16, scale=1, clamp_min=0), 0)
        self.assertEqual(decode_registers([500], DataType.UINT16, scale=1, clamp_max=300), 300)
        self.assertEqual(encode_registers(-10.0, DataType.INT16, scale=0.5), [65516])
        self.assertEqual(encode_registers(42.5, DataType.UINT16, scale=0.5), [85])

    def test_decode_and_encode_32bit_ints(self):
        # 0x00010002 = 65538
        self.assertEqual(decode_registers([1, 2], DataType.UINT32, word_order=WordOrder.BIG_ENDIAN), 65538)
        self.assertEqual(decode_registers([2, 1], DataType.UINT32, word_order=WordOrder.LITTLE_ENDIAN), 65538)
        # -2 in 32-bit two's complement = 0xFFFFFFFE
        self.assertEqual(decode_registers([0xFFFF, 0xFFFE], DataType.INT32, word_order=WordOrder.BIG_ENDIAN), -2)
        self.assertEqual(encode_registers(65538, DataType.UINT32, word_order=WordOrder.LITTLE_ENDIAN), [2, 1])
        self.assertEqual(encode_registers(-2, DataType.INT32, word_order=WordOrder.BIG_ENDIAN), [0xFFFF, 0xFFFE])

    def test_decode_and_encode_float32(self):
        packed = struct.pack(">f", 55.25)
        hi, lo = struct.unpack(">HH", packed)

        self.assertAlmostEqual(
            decode_registers([hi, lo], DataType.FLOAT32, word_order=WordOrder.BIG_ENDIAN),
            55.25,
            places=4,
        )
        self.assertAlmostEqual(
            decode_registers([lo, hi], DataType.FLOAT32, word_order=WordOrder.LITTLE_ENDIAN),
            55.25,
            places=4,
        )
        self.assertEqual(encode_registers(55.25, DataType.FLOAT32, word_order=WordOrder.BIG_ENDIAN), [hi, lo])
        self.assertEqual(encode_registers(55.25, DataType.FLOAT32, word_order=WordOrder.LITTLE_ENDIAN), [lo, hi])

    def test_decode_float32_nan_raises(self):
        # IEEE-754 NaN: 0x7FC0 0x0000
        with self.assertRaises(ValueError):
            decode_registers([0x7FC0, 0x0000], DataType.FLOAT32)

    def test_decode_32bit_short_words_raises(self):
        with self.assertRaises(ValueError):
            decode_registers([1], DataType.UINT32)


class TestModbusBatchHelpers(unittest.TestCase):
    """Test shared Modbus batch reader and declarative decoder."""

    def test_read_discrete_inputs_slices_padded_bits(self):
        client = MagicMock()
        res = MagicMock()
        res.isError.return_value = False
        # pymodbus pads discrete input responses to 8-bit boundaries
        res.bits = [True, False, True, False, False, False, False, False]
        client.read_discrete_inputs.return_value = res

        batch = ModbusBatchSpec(RegisterSpace.DISCRETE_INPUT, 10, 3, "Discrete Test")
        bits = read_modbus_batch(client, 1, batch)
        self.assertEqual(bits, [True, False, True])
        client.read_discrete_inputs.assert_called_once_with(address=10, count=3, device_id=1)

    def test_read_coils_and_input_registers(self):
        client = MagicMock()
        coil_res = MagicMock(isError=lambda: False, bits=[False, True, False, False, False, False, False, False])
        in_res = MagicMock(isError=lambda: False, registers=[11, 22])
        client.read_coils.return_value = coil_res
        client.read_input_registers.return_value = in_res

        self.assertEqual(
            read_modbus_batch(client, 1, ModbusBatchSpec(RegisterSpace.COIL, 38, 2)),
            [False, True],
        )
        self.assertEqual(
            read_modbus_batch(client, 1, ModbusBatchSpec(RegisterSpace.INPUT_REGISTER, 0, 2)),
            [11, 22],
        )

    def test_read_batch_errors_and_desync(self):
        client = MagicMock()
        client.read_holding_registers.return_value = MagicMock(isError=lambda: True)
        with self.assertRaises(ModbusBatchError):
            read_modbus_batch(client, 1, ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 0, 2))

        client.read_holding_registers.return_value = MagicMock(isError=lambda: False, registers=[1])
        with self.assertRaises(ModbusDesyncError):
            read_modbus_batch(client, 1, ModbusBatchSpec(RegisterSpace.HOLDING_REGISTER, 0, 2))

    def test_decode_batch_into_data_mixed_specs(self):
        controller = SyntheticAltController()
        hi, lo = struct.unpack(">HH", struct.pack(">f", 123.5))
        # Simulate holding registers 384..388: 384-385=float32(123.5), 386=pad, 387-388=uint32(2450)
        hr_words = [hi, lo, 0, 0, 2450]
        data = {}
        decode_batch_into_data(controller.get_sensors(), RegisterSpace.HOLDING_REGISTER, 384, hr_words, data)
        self.assertAlmostEqual(data["alt_energy"], 123.5, places=3)
        self.assertEqual(data["alt_power"], 2450)

        # Simulate discrete inputs 5 and 149 individually
        decode_batch_into_data(controller.get_binary_sensors(), RegisterSpace.DISCRETE_INPUT, 5, [True], data)
        decode_batch_into_data(controller.get_binary_sensors(), RegisterSpace.DISCRETE_INPUT, 149, [True], data)
        # alt_output_inv is inverted=True, raw=True -> False
        self.assertFalse(data["alt_output_inv"])
        self.assertTrue(data["alt_alarm"])

        # Simulate coil 105
        decode_batch_into_data(controller.get_switches(), RegisterSpace.COIL, 105, [True], data)
        self.assertTrue(data["alt_coil_switch"])


class TestCoordinatorMultiProtocol(unittest.IsolatedAsyncioTestCase):
    """Test coil and multi-register writes on coordinator."""

    def setUp(self):
        self.hass = MagicMock()

        async def async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)

        self.hass.async_add_executor_job = async_add_executor_job
        self.coordinator = SPRSUNDataUpdateCoordinator(
            hass=self.hass,
            host="192.168.1.100",
            port=502,
            device_address=1,
            scan_interval=10,
            controller_type="chico",
        )

    async def test_async_write_coil_success_and_retry(self):
        client = MagicMock()
        client.connected = True
        err_res = MagicMock(isError=lambda: True)
        ok_res = MagicMock(isError=lambda: False)
        client.write_coil.side_effect = [err_res, ok_res]
        client.connect.return_value = True
        self.coordinator._create_modbus_client = MagicMock(return_value=client)
        self.coordinator.client = client

        with patch("time.sleep") as mock_sleep:
            await self.coordinator.async_write_coil(address=105, value=True, key="manual_defrost")

        self.assertEqual(client.write_coil.call_count, 2)
        client.write_coil.assert_called_with(address=105, value=True, device_id=1)
        mock_sleep.assert_any_call(INTER_WRITE_DELAY)
        self.assertTrue(self.coordinator.data["manual_defrost"]["value"])

    async def test_async_write_registers_fc10(self):
        client = MagicMock()
        client.connected = True
        client.write_registers.return_value = MagicMock(isError=lambda: False)
        self.coordinator.client = client

        with patch("time.sleep") as mock_sleep:
            await self.coordinator.async_write_registers(
                address=471,
                registers=[0x0000, 0x425C],
                key="alt_float_setp",
                value=55.0,
            )

        client.write_registers.assert_called_once_with(
            address=471,
            values=[0x0000, 0x425C],
            device_id=1,
        )
        mock_sleep.assert_called_once_with(INTER_WRITE_DELAY)
        self.assertEqual(self.coordinator.data["alt_float_setp"]["value"], 55.0)


class TestControllerAgnosticPlatforms(unittest.IsolatedAsyncioTestCase):
    """Verify all HA platforms work seamlessly with a non-CHICO controller."""

    def setUp(self):
        self.controller = SyntheticAltController()
        self.coordinator = MagicMock()
        self.coordinator.controller = self.controller
        self.coordinator.last_update_success = True
        self.coordinator.async_write_register = AsyncMock()
        self.coordinator.async_write_registers = AsyncMock()
        self.coordinator.async_write_coil = AsyncMock()
        self.coordinator.async_write_bit = AsyncMock()
        now = time.time()
        self.coordinator.data = {
            k: {"value": v, "updated_at": now}
            for k, v in self.controller.read_all_registers(None, 1, True).items()
        }

        self.config_entry = MagicMock()
        self.config_entry.entry_id = "alt_entry_1"
        self.config_entry.data = {CONF_NAME: "ALT Pump"}
        self.config_entry.options = {}

        self.hass = MagicMock()
        self.hass.data = {DOMAIN: {self.config_entry.entry_id: self.coordinator}}

    def test_resolve_controller_fallback_for_mock(self):
        mock_coord = MagicMock()
        self.assertEqual(resolve_controller(mock_coord).name, "CHICO")
        self.assertEqual(resolve_controller(self.coordinator).name, "ALT")
        self.assertIn("chico", get_supported_controllers())

    async def test_all_platforms_use_controller_specs(self):
        # Sensor platform
        add_sensors = MagicMock()
        await sensor_setup_entry(self.hass, self.config_entry, add_sensors)
        sensors = add_sensors.call_args[0][0]
        self.assertEqual(len(sensors), 2)
        self.assertEqual(sensors[0].unique_id, "alt_entry_1_alt_energy")
        self.assertEqual(sensors[0].native_value, 123.5)
        self.assertEqual(str(sensors[0].device_class), "energy")
        self.assertEqual(str(sensors[0].state_class), "total_increasing")

        # Binary sensor platform (discrete input & inverted)
        add_bs = MagicMock()
        await bs_setup_entry(self.hass, self.config_entry, add_bs)
        binary_sensors = add_bs.call_args[0][0]
        self.assertEqual(len(binary_sensors), 2)
        self.assertTrue(binary_sensors[0].is_on)
        self.assertEqual(binary_sensors[0].entity_category, EntityCategory.DIAGNOSTIC)
        self.assertEqual(str(binary_sensors[0].device_class), "problem")
        # Raw value in data is already False; inverted=True flips to True
        self.assertTrue(binary_sensors[1].is_on)

        # Number platform (multi-register FLOAT32 write)
        add_nums = MagicMock()
        await number_setup_entry(self.hass, self.config_entry, add_nums)
        numbers = add_nums.call_args[0][0]
        self.assertEqual(len(numbers), 1)
        await numbers[0].async_set_native_value(60.0)
        expected_regs = encode_registers(60.0, DataType.FLOAT32, scale=1.0, word_order=WordOrder.LITTLE_ENDIAN)
        self.coordinator.async_write_registers.assert_called_once_with(
            address=471,
            registers=expected_regs,
            key="alt_float_setp",
            value=60.0,
        )

        # Select platform
        add_selects = MagicMock()
        await select_setup_entry(self.hass, self.config_entry, add_selects)
        selects = add_selects.call_args[0][0]
        self.assertEqual(len(selects), 1)
        self.assertEqual(selects[0].current_option, "Cooling")

        # Switch platform (Modbus Coil)
        add_switches = MagicMock()
        await switch_setup_entry(self.hass, self.config_entry, add_switches)
        switches = add_switches.call_args[0][0]
        self.assertEqual(len(switches), 1)
        self.assertTrue(switches[0].is_on)
        await switches[0].async_turn_off()
        self.coordinator.async_write_coil.assert_called_with(105, False, key="alt_coil_switch")

        # Button platform (Modbus Coil)
        add_buttons = MagicMock()
        await button_setup_entry(self.hass, self.config_entry, add_buttons)
        buttons = add_buttons.call_args[0][0]
        self.assertEqual(len(buttons), 1)
        await buttons[0].async_press()
        self.coordinator.async_write_coil.assert_called_with(68, True, key=None)

        # Climate platform (1 entity only since supports_dhw=False)
        add_climates = MagicMock()
        await climate_setup_entry(self.hass, self.config_entry, add_climates)
        climates = add_climates.call_args[0][0]
        self.assertEqual(len(climates), 1)
        climate = climates[0]
        self.assertIsInstance(climate, SPRSUNClimate)
        self.assertEqual(climate.hvac_modes, [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL])
        self.assertEqual(climate.hvac_mode, HVACMode.COOL)
        self.assertEqual(climate.min_temp, 12.0)
        await climate.async_set_temperature(**{ATTR_TEMPERATURE: 20.0})
        self.assertEqual(self.coordinator.async_write_registers.call_count, 2)

    async def test_setup_and_unload_subset_of_platforms(self):
        class SensorOnlyController(SyntheticAltController):
            def get_platforms(self) -> list[str]:
                return ["sensor"]

        hass = MagicMock()
        hass.data = {}

        async def async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)

        hass.async_add_executor_job = async_add_executor_job
        hass.config_entries = MagicMock()
        hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
        hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

        entry = MagicMock()
        entry.entry_id = "subset_entry"
        entry.options = {}
        entry.data = {
            CONF_NAME: "Sensor Only",
            CONF_HOST: "192.168.1.50",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
            CONF_SCAN_INTERVAL: 10,
            CONF_CONTROLLER_TYPE: "chico",
        }

        with (
            patch("custom_components.sprsun_modbus.get_controller", return_value=SensorOnlyController()),
            patch.object(SPRSUNDataUpdateCoordinator, "async_config_entry_first_refresh", new_callable=AsyncMock),
        ):
            await async_setup_entry(hass, entry)
            hass.config_entries.async_forward_entry_setups.assert_called_once_with(
                entry, [Platform.SENSOR]
            )
            await async_unload_entry(hass, entry)
            hass.config_entries.async_unload_platforms.assert_called_once_with(
                entry, [Platform.SENSOR]
            )

    async def test_validate_connection_non_chico_without_reg0(self):
        hass = MagicMock()

        async def async_add_executor_job(func, *args, **kwargs):
            return func(*args, **kwargs)

        hass.async_add_executor_job = async_add_executor_job
        data = {
            CONF_NAME: "ALT Pump",
            CONF_HOST: "192.168.1.200",
            CONF_PORT: 502,
            CONF_DEVICE_ADDRESS: 1,
        }

        with (
            patch("custom_components.sprsun_modbus.config_flow.ModbusTcpClient") as mock_client_cls,
            patch("custom_components.sprsun_modbus.controllers.detect_controller_type", return_value="alt"),
        ):
            client = MagicMock()
            client.connect.return_value = True
            # Note: read_holding_registers(0x0000) is NOT needed when detection succeeds
            client.read_holding_registers.return_value = MagicMock(isError=lambda: True)
            mock_client_cls.return_value = client

            info = await validate_connection(hass, data)
            self.assertEqual(info["controller_type"], "alt")
            client.close.assert_called_once()

    async def test_expert_spec_promotions_and_mask_offset_codecs(self):
        """Test raw_offset/bit_mask codecs, future-write spec conversion helpers, and diagnostics."""
        from custom_components.sprsun_modbus.controllers.chico_registers import (
            CHICO_EXPERT_BINARY_SENSORS,
            CHICO_EXPERT_SENSORS,
        )
        from custom_components.sprsun_modbus.diagnostics import async_get_config_entry_diagnostics

        self.assertEqual(decode_registers([12], DataType.UINT16, scale=0.1, raw_offset=250), 26.2)
        self.assertEqual(encode_registers(26.2, DataType.UINT16, scale=0.1, raw_offset=250), [12])
        self.assertEqual(decode_registers([0x0244], DataType.UINT16, scale=0.5, bit_mask=0xFF), 34.0)
        self.assertEqual(encode_registers(34.0, DataType.UINT16, scale=0.5, bit_mask=0xFF), [0x44])

        by_sensor_key = {s.key: s for s in CHICO_EXPERT_SENSORS}
        f02_num = by_sensor_key["f02_hp_protect_value"].as_number_spec()
        self.assertEqual(f02_num.address, 0x0082)
        self.assertEqual(f02_num.raw_offset, 250)
        self.assertEqual(f02_num.min_value, 25.0)
        self.assertEqual(f02_num.max_value, 50.0)

        f13_sel = by_sensor_key["f13_dc_pump_mode"].as_select_spec()
        self.assertEqual(f13_sel.options, {0: "Manual", 1: "Auto"})

        by_bin_key = {b.key: b for b in CHICO_EXPERT_BINARY_SENSORS}
        b74_sw = by_bin_key["b74_av_cool_enable"].as_switch_spec()
        self.assertEqual(b74_sw.address, 0x0033)
        self.assertEqual(b74_sw.bit, 2)
        self.assertEqual(b74_sw.coil_address, 0x0332)
        self.assertTrue(b74_sw.inverted)

        hass = MagicMock()
        coord = MagicMock()
        coord.controller = SyntheticAltController()
        coord.last_update_success = True
        coord._rw_loaded = True
        coord._poll_count = 3
        coord.data = {"alt_energy": {"value": 123.5, "updated_at": 10.0}}
        entry = MagicMock()
        entry.entry_id = "diag_entry"
        entry.runtime_data = coord
        entry.data = {CONF_HOST: "192.168.1.99", CONF_PORT: 502}
        entry.options = {}
        hass.data = {DOMAIN: {"diag_entry": coord}}

        diag = await async_get_config_entry_diagnostics(hass, entry)
        self.assertEqual(diag["entry"]["data"][CONF_HOST], "**REDACTED**")
        self.assertEqual(diag["values"]["alt_energy"], 123.5)


if __name__ == "__main__":
    unittest.main()
