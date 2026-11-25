"""Unit tests for opt-in CHICO expert write support."""

import types
import unittest
from unittest.mock import AsyncMock, MagicMock

import tests.mock_ha  # noqa: F401 - register mock Home Assistant modules
from homeassistant.const import CONF_HOST, CONF_PORT, EntityCategory

from custom_components.sprsun_modbus import SPRSUNDataUpdateCoordinator
from custom_components.sprsun_modbus.config_flow import SPRSUNOptionsFlowHandler
from custom_components.sprsun_modbus.const import (
    CONF_DEVICE_ADDRESS,
    CONF_ENABLE_EXPERT_WRITES,
    CONF_SCAN_INTERVAL,
    CONF_TEMP_STEP,
    DEFAULT_ENABLE_EXPERT_WRITES,
    is_expert_writes_enabled,
)
from custom_components.sprsun_modbus.controllers.chico import ChicoController
from custom_components.sprsun_modbus.controllers.models import decode_registers, encode_registers
from custom_components.sprsun_modbus.number import NumberMode, async_setup_entry as number_setup_entry
from custom_components.sprsun_modbus.select import async_setup_entry as select_setup_entry
from custom_components.sprsun_modbus.switch import async_setup_entry as switch_setup_entry


def _make_entry(*, data=None, options=None):
    """Build a mock ConfigEntry with data/options and real ChicoController coordinator."""
    coordinator = SPRSUNDataUpdateCoordinator(
        MagicMock(), "192.168.10.150", 502, 1, 10, "chico"
    )
    entry = MagicMock()
    entry.entry_id = "test_expert_entry"
    entry.data = data if data is not None else {CONF_HOST: "192.168.10.150"}
    entry.options = options if options is not None else {}
    entry.runtime_data = coordinator
    return entry, coordinator


class TestExpertWritesConfigAndSpecs(unittest.TestCase):
    """Verify opt-in helpers, option flow, and CHICO expert write spec safety."""

    def test_is_expert_writes_enabled_defaults_and_overrides(self):
        """Option defaults to False and options take precedence over data."""
        self.assertFalse(DEFAULT_ENABLE_EXPERT_WRITES)

        entry_default, _ = _make_entry()
        self.assertFalse(is_expert_writes_enabled(entry_default))

        entry_data, _ = _make_entry(data=types.MappingProxyType({CONF_ENABLE_EXPERT_WRITES: True}))
        self.assertTrue(is_expert_writes_enabled(entry_data))

        entry_override, _ = _make_entry(
            data={CONF_ENABLE_EXPERT_WRITES: True},
            options=types.MappingProxyType({CONF_ENABLE_EXPERT_WRITES: False}),
        )
        self.assertFalse(is_expert_writes_enabled(entry_override))

    def test_chico_expert_specs_safety_and_roundtrip(self):
        """All CHICO expert specs exclude dangerous reset bits and round-trip cleanly."""
        controller = ChicoController()
        nums = controller.get_expert_numbers()
        sels = controller.get_expert_selects()
        sws = controller.get_expert_switches()

        self.assertEqual(len(nums), 322)
        self.assertEqual(len(sels), 2)
        self.assertEqual(len(sws), 13)

        # Dangerous factory reset flag (0x0033 bit 6) must NOT be exposed as a switch
        self.assertFalse(any(spec.key == "parameters_reset_flag" for spec in sws))

        # No key collisions across core and expert entities
        core_keys = (
            {s.key for s in controller.get_numbers()}
            | {s.key for s in controller.get_selects()}
            | {s.key for s in controller.get_switches()}
        )
        exp_keys = {s.key for s in nums} | {s.key for s in sels} | {s.key for s in sws}
        self.assertEqual(len(nums) + len(sels) + len(sws), len(exp_keys))
        self.assertFalse(core_keys & exp_keys)

        # Boundary round-trip checks for INT16, raw_offset, and standard registers
        for spec in nums:
            if spec.bit_mask is not None:
                continue
            for val in (spec.min_value, spec.max_value):
                regs = encode_registers(
                    val,
                    data_type=spec.data_type,
                    scale=spec.scale,
                    raw_offset=spec.raw_offset,
                )
                decoded = decode_registers(
                    regs,
                    data_type=spec.data_type,
                    scale=spec.scale,
                    raw_offset=spec.raw_offset,
                )
                self.assertAlmostEqual(decoded, val, places=5, msg=spec.key)


class TestExpertWritesAsyncPlatforms(unittest.IsolatedAsyncioTestCase):
    """Verify entity platform setup and write routing when opt-in is disabled/enabled."""

    async def test_options_flow_exposes_and_persists_enable_expert_writes(self):
        """Options flow exposes opt-in checkbox defaulting to False and saves True."""
        entry, _ = _make_entry(
            data={
                CONF_HOST: "192.168.10.150",
                CONF_PORT: 502,
                CONF_DEVICE_ADDRESS: 1,
                CONF_SCAN_INTERVAL: 10,
                CONF_TEMP_STEP: 1.0,
            }
        )
        flow = SPRSUNOptionsFlowHandler(entry)
        res_form = await flow.async_step_init(user_input=None)
        self.assertEqual(res_form["type"], "form")
        schema_keys = {k.schema: k for k in res_form["data_schema"].schema}
        self.assertIn(CONF_ENABLE_EXPERT_WRITES, schema_keys)
        self.assertFalse(schema_keys[CONF_ENABLE_EXPERT_WRITES].default())

        res_save = await flow.async_step_init(
            user_input={
                CONF_HOST: "192.168.10.150",
                CONF_PORT: 502.0,
                CONF_DEVICE_ADDRESS: 1.0,
                CONF_SCAN_INTERVAL: 10.0,
                CONF_TEMP_STEP: "1.0",
                CONF_ENABLE_EXPERT_WRITES: True,
            }
        )
        self.assertEqual(res_save["type"], "create_entry")
        self.assertTrue(res_save["data"][CONF_ENABLE_EXPERT_WRITES])
        self.assertIs(type(res_save["data"][CONF_PORT]), int)
        self.assertIs(type(res_save["data"][CONF_DEVICE_ADDRESS]), int)
        self.assertIs(type(res_save["data"][CONF_SCAN_INTERVAL]), int)
        self.assertEqual(res_save["data"][CONF_DEVICE_ADDRESS], 1)

    def test_coordinator_coerces_float_connection_args_to_int(self):
        """Coordinator coerces legacy float options (e.g. 1.0) to int for pymodbus."""
        coord = SPRSUNDataUpdateCoordinator(
            MagicMock(), "192.168.10.150", 502.0, 1.0, 10.0, "chico"
        )
        self.assertIs(type(coord.port), int)
        self.assertIs(type(coord.device_address), int)
        self.assertEqual(coord.port, 502)
        self.assertEqual(coord.device_address, 1)
        self.assertEqual(coord.cache_staleness_seconds, 20)

    async def test_platforms_gate_expert_entities_by_option(self):
        """Disabled by default (42/3/3), enabled adds 322/2/13 Config entities."""
        entry_off, _ = _make_entry(options={CONF_ENABLE_EXPERT_WRITES: False})
        nums_off, sels_off, sws_off = [], [], []
        await number_setup_entry(MagicMock(), entry_off, nums_off.extend)
        await select_setup_entry(MagicMock(), entry_off, sels_off.extend)
        await switch_setup_entry(MagicMock(), entry_off, sws_off.extend)
        self.assertEqual(len(nums_off), 42)
        self.assertEqual(len(sels_off), 3)
        self.assertEqual(len(sws_off), 3)

        entry_on, _ = _make_entry(options={CONF_ENABLE_EXPERT_WRITES: True})
        nums_on, sels_on, sws_on = [], [], []
        await number_setup_entry(MagicMock(), entry_on, nums_on.extend)
        await select_setup_entry(MagicMock(), entry_on, sels_on.extend)
        await switch_setup_entry(MagicMock(), entry_on, sws_on.extend)
        self.assertEqual(len(nums_on), 364)
        self.assertEqual(len(sels_on), 5)
        self.assertEqual(len(sws_on), 16)

        # Verify expert entities use EntityCategory.CONFIG and BOX input mode for numbers
        by_num_key = {e._key: e for e in nums_on}
        tb_min = by_num_key["timeband_3_on_minute"]
        self.assertEqual(tb_min._attr_entity_category, EntityCategory.CONFIG)
        self.assertEqual(tb_min._attr_mode, NumberMode.BOX)

        by_sel_key = {e._key: e for e in sels_on}
        self.assertEqual(by_sel_key["f13_dc_pump_mode"]._attr_entity_category, EntityCategory.CONFIG)

        by_sw_key = {e._key: e for e in sws_on}
        self.assertEqual(by_sw_key["timeband_3_enable"]._attr_entity_category, EntityCategory.CONFIG)

    async def test_expert_number_write_routing(self):
        """Standard, INT16 negative, raw_offset, and bit_mask numbers route properly."""
        entry, coord = _make_entry(options={CONF_ENABLE_EXPERT_WRITES: True})
        coord.async_write_register = AsyncMock(return_value=True)
        coord.async_write_masked_register = AsyncMock(return_value=True)

        entities = []
        await number_setup_entry(MagicMock(), entry, entities.extend)
        by_key = {e._key: e for e in entities}

        # 1. Plain UINT16 expert register
        await by_key["timeband_3_on_minute"].async_set_native_value(5.0)
        coord.async_write_register.assert_called_with(
            address=0x0122, value=5.0, key="timeband_3_on_minute", scale=1
        )

        # 2. Signed INT16 negative register (raw two's complement + explicit cached_value)
        coord.async_write_register.reset_mock()
        await by_key["h03_defrost_in_stp"].async_set_native_value(-5.0)
        coord.async_write_register.assert_called_with(
            address=0x00D4,
            value=65531.0,
            key="h03_defrost_in_stp",
            scale=1,
            cached_value=-5.0,
        )

        # 3. raw_offset + fractional scale register (F02: raw = 42.0/0.1 - 250 = 170)
        coord.async_write_register.reset_mock()
        await by_key["f02_hp_protect_value"].async_set_native_value(42.0)
        coord.async_write_register.assert_called_with(
            address=0x0082,
            value=170.0,
            key="f02_hp_protect_value",
            scale=1,
            cached_value=42.0,
        )

        # 4. bit_mask write (Timeband 3 heat setpoint low byte 0xFF)
        await by_key["timeband_3_heat_setp"].async_set_native_value(35.0)
        coord.async_write_masked_register.assert_called_with(
            address=0x01AB,
            raw_value=70,
            mask=0x00FF,
            key="timeband_3_heat_setp",
            cached_value=35.0,
        )


if __name__ == "__main__":
    unittest.main()
