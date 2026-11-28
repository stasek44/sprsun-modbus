"""Unit tests for CHICO calculated/derived sensors and coordinator integration."""
import unittest
from unittest.mock import MagicMock, patch

from tests.conftest import setup_mocks

setup_mocks()

from homeassistant.const import CONF_NAME, EntityCategory
from custom_components.sprsun_modbus import SPRSUNDataUpdateCoordinator
from custom_components.sprsun_modbus.controllers.chico import ChicoController
from custom_components.sprsun_modbus.controllers.chico_derived import (
    CHICO_DERIVED_SENSORS,
    DEFROST_AMBIENT_HOLD_SECONDS,
    DEFROST_AMBIENT_MAX_HOLD_SECONDS,
    IDLE_AMBIENT_MAX_HOLD_SECONDS,
    ChicoDerivedTracker,
    compute_eco_curve_setpoint,
    compute_estimated_power,
    compute_operating_state,
)
from custom_components.sprsun_modbus.controllers.chico_registers import (
    CHICO_CONTROL_REGISTER_KEYS,
    CHICO_STATUS_REGISTER_KEYS,
)
from custom_components.sprsun_modbus.sensor import SPRSUNDerivedSensor


class TestChicoDerivedSensors(unittest.TestCase):
    """Test suite for CHICO derived sensor specs, formulas, and stateful trackers."""

    def test_derived_keys_unique_and_non_overlapping(self):
        """Ensure derived sensor keys never collide with physical CHICO keys."""
        controller = ChicoController()
        derived_keys = [s.key for s in controller.get_derived_sensors()]
        self.assertEqual(len(derived_keys), 18)
        self.assertEqual(len(derived_keys), len(set(derived_keys)))

        hardware_keys = (
            {s.key for s in controller.get_sensors()}
            | {s.key for s in controller.get_expert_sensors()}
            | {s.key for s in controller.get_binary_sensors()}
            | {s.key for s in controller.get_expert_binary_sensors()}
            | {s.key for s in controller.get_numbers()}
            | {s.key for s in controller.get_selects()}
            | {s.key for s in controller.get_switches()}
            | {s.key for s in controller.get_buttons()}
            | set(CHICO_STATUS_REGISTER_KEYS.values())
            | set(CHICO_CONTROL_REGISTER_KEYS.values())
        )
        self.assertFalse(set(derived_keys) & hardware_keys)
        self.assertTrue(all(s.enabled_default for s in controller.get_derived_sensors()))

    def test_ambient_temp_filtered_during_and_after_defrost(self):
        """Hold pre-defrost ambient during defrost and post-defrost cooldown until cooled."""
        tracker = ChicoDerivedTracker()

        # Normal pre-defrost reading
        d0 = {"ambient_temp": -1.0, "working_status_register": 0}
        self.assertEqual(tracker.compute(d0, now=1000.0)["ambient_temp_filtered"], -1.0)

        # Defrost starts and outdoor sensor spikes up to +5.0°C
        d1 = {"ambient_temp": 3.5, "working_status_register": 1 << 7}
        self.assertEqual(tracker.compute(d1, now=1060.0)["ambient_temp_filtered"], -1.0)
        d2 = {"ambient_temp": 5.0, "working_status_register": 1 << 7}
        self.assertEqual(tracker.compute(d2, now=1240.0)["ambient_temp_filtered"], -1.0)

        # Defrost ends at t=1260; sensor still warm (+4.0°C) within 420s cooldown
        d3 = {"ambient_temp": 4.0, "working_status_register": 0}
        self.assertEqual(tracker.compute(d3, now=1320.0)["ambient_temp_filtered"], -1.0)

        # Early exit when sensor cools down below/to held ambient before cooldown expires
        d4 = {"ambient_temp": -1.5, "working_status_register": 0}
        self.assertEqual(tracker.compute(d4, now=1500.0)["ambient_temp_filtered"], -1.5)

        # Verify timeout release if sensor stays warmer than held value past cooldown
        tracker2 = ChicoDerivedTracker()
        tracker2.compute({"ambient_temp": 1.0, "working_status_register": 0}, now=100.0)
        tracker2.compute({"ambient_temp": 8.0, "working_status_register": 1 << 7}, now=200.0)
        tracker2.compute({"ambient_temp": 6.0, "working_status_register": 0}, now=300.0)
        self.assertEqual(
            tracker2.compute({"ambient_temp": 5.0, "working_status_register": 0}, now=300.0 + 120.0)[
                "ambient_temp_filtered"
            ],
            1.0,
        )
        self.assertEqual(
            tracker2.compute(
                {"ambient_temp": 4.5, "working_status_register": 0},
                now=300.0 + DEFROST_AMBIENT_HOLD_SECONDS + 1.0,
            )["ambient_temp_filtered"],
            4.5,
        )

    def test_ambient_temp_filtered_fan_aware_idle_hold(self):
        """Pause post-defrost 7m cooldown while fan is OFF, release after 7m fan runtime or 45m cap."""
        tracker = ChicoDerivedTracker()

        # Pre-defrost heating with fan ON (output_symbol_1 bit 5)
        self.assertEqual(
            tracker.compute(
                {"ambient_temp": -1.5, "working_status_register": 0, "output_symbol_1": 1 << 5},
                now=1000.0,
            )["ambient_temp_filtered"],
            -1.5,
        )

        # Defrost active -> held at -1.5°C
        self.assertEqual(
            tracker.compute(
                {"ambient_temp": 4.0, "working_status_register": 1 << 7, "output_symbol_1": 0},
                now=1200.0,
            )["ambient_temp_filtered"],
            -1.5,
        )

        # Defrost finishes at t=1300 and pump goes IDLE (fan OFF); > 420s pass -> still held!
        self.assertEqual(
            tracker.compute(
                {"ambient_temp": 3.5, "working_status_register": 0, "output_symbol_1": 0},
                now=1300.0,
            )["ambient_temp_filtered"],
            -1.5,
        )
        self.assertEqual(
            tracker.compute(
                {"ambient_temp": 4.0, "working_status_register": 0, "output_symbol_1": 0},
                now=1300.0 + DEFROST_AMBIENT_HOLD_SECONDS + 300.0,  # 720s idle, fan OFF
            )["ambient_temp_filtered"],
            -1.5,
        )

        # Fan turns back ON at t=2100 -> accumulates fan runtime, releases after 420s fan ON
        self.assertEqual(
            tracker.compute(
                {"ambient_temp": 3.0, "working_status_register": 0, "output_symbol_1": 1 << 5},
                now=2100.0,
            )["ambient_temp_filtered"],
            -1.5,
        )
        self.assertEqual(
            tracker.compute(
                {"ambient_temp": 2.5, "working_status_register": 0, "output_symbol_1": 1 << 5},
                now=2100.0 + DEFROST_AMBIENT_HOLD_SECONDS + 10.0,
            )["ambient_temp_filtered"],
            2.5,
        )

        # Hard 45m wall-clock cap releases hold even if fan never turns back on
        tracker_cap = ChicoDerivedTracker()
        tracker_cap.compute(
            {"ambient_temp": -2.0, "working_status_register": 0, "output_symbol_1": 1 << 5},
            now=100.0,
        )
        tracker_cap.compute(
            {"ambient_temp": 5.0, "working_status_register": 1 << 7, "output_symbol_1": 0},
            now=200.0,
        )
        tracker_cap.compute(
            {"ambient_temp": 4.0, "working_status_register": 0, "output_symbol_1": 0},
            now=300.0,
        )
        self.assertEqual(
            tracker_cap.compute(
                {"ambient_temp": 3.8, "working_status_register": 0, "output_symbol_1": 0},
                now=300.0 + DEFROST_AMBIENT_MAX_HOLD_SECONDS + 1.0,
            )["ambient_temp_filtered"],
            3.8,
        )

    def test_ambient_temp_filtered_enhanced_idle_defrost_and_cooling(self):
        """Filter upward spikes during idle/standby and defrost, track cooling, and enforce 4h cap."""
        tracker = ChicoDerivedTracker()

        # Running with fan ON
        res0 = tracker.compute(
            {"ambient_temp": -1.5, "working_status_register": 0, "output_symbol_1": 1 << 5},
            now=1000.0,
        )
        self.assertEqual(res0["ambient_temp_filtered_enhanced"], -1.5)

        # Enters idle (fan OFF) and sensor heat-soaks up to +4.0°C -> frozen at -1.5°C
        res1 = tracker.compute(
            {"ambient_temp": 1.0, "working_status_register": 0, "output_symbol_1": 0},
            now=1300.0,
        )
        self.assertEqual(res1["ambient_temp_filtered_enhanced"], -1.5)
        res2 = tracker.compute(
            {"ambient_temp": 4.0, "working_status_register": 0, "output_symbol_1": 0},
            now=2000.0,
        )
        self.assertEqual(res2["ambient_temp_filtered_enhanced"], -1.5)

        # Fan restarts at t=3000 -> holds -1.5°C for 7m of fan runtime despite long idle jump
        res3 = tracker.compute(
            {"ambient_temp": 3.0, "working_status_register": 0, "output_symbol_1": 1 << 5},
            now=3000.0,
        )
        self.assertEqual(res3["ambient_temp_filtered_enhanced"], -1.5)
        res4 = tracker.compute(
            {"ambient_temp": 2.0, "working_status_register": 0, "output_symbol_1": 1 << 5},
            now=3000.0 + 300.0,
        )
        self.assertEqual(res4["ambient_temp_filtered_enhanced"], -1.5)

        # Releases after 7m of fan runtime
        res5 = tracker.compute(
            {"ambient_temp": -2.0, "working_status_register": 0, "output_symbol_1": 1 << 5},
            now=3000.0 + DEFROST_AMBIENT_HOLD_SECONDS + 10.0,
        )
        self.assertEqual(res5["ambient_temp_filtered_enhanced"], -2.0)

        # Downward cooling during idle is tracked, then subsequent upward spike is blocked
        res6 = tracker.compute(
            {"ambient_temp": -3.0, "working_status_register": 0, "output_symbol_1": 0},
            now=4000.0,
        )
        self.assertEqual(res6["ambient_temp_filtered_enhanced"], -3.0)
        res7 = tracker.compute(
            {"ambient_temp": 1.5, "working_status_register": 0, "output_symbol_1": 0},
            now=4300.0,
        )
        self.assertEqual(res7["ambient_temp_filtered_enhanced"], -3.0)

        # 4h idle cap releases hold after IDLE_AMBIENT_MAX_HOLD_SECONDS
        res8 = tracker.compute(
            {"ambient_temp": 5.5, "working_status_register": 0, "output_symbol_1": 0},
            now=4000.0 + IDLE_AMBIENT_MAX_HOLD_SECONDS + 1.0,
        )
        self.assertEqual(res8["ambient_temp_filtered_enhanced"], 5.5)

        # Defrost -> idle -> heating transition preserves pre-defrost ambient
        tracker_defrost = ChicoDerivedTracker()
        tracker_defrost.compute(
            {"ambient_temp": -2.5, "working_status_register": 0, "output_symbol_1": 1 << 5},
            now=100.0,
        )
        self.assertEqual(
            tracker_defrost.compute(
                {"ambient_temp": 6.0, "working_status_register": 1 << 7, "output_symbol_1": 0},
                now=200.0,
            )["ambient_temp_filtered_enhanced"],
            -2.5,
        )
        self.assertEqual(
            tracker_defrost.compute(
                {"ambient_temp": 4.5, "working_status_register": 0, "output_symbol_1": 0},
                now=3200.0,  # 50 min idle after defrost (< 4h cap)
            )["ambient_temp_filtered_enhanced"],
            -2.5,
        )
        self.assertEqual(
            tracker_defrost.compute(
                {"ambient_temp": 3.0, "working_status_register": 0, "output_symbol_1": 1 << 5},
                now=3300.0,
            )["ambient_temp_filtered_enhanced"],
            -2.5,
        )

    def test_coil_ambient_delta_non_negative_and_defrost_clamped(self):
        """Ensure coil_ambient_delta reports 0.0 during defrost or when coil >= outdoor."""
        tracker = ChicoDerivedTracker()
        # Heating with frosted coil -> positive frost load
        res_heat = tracker.compute(
            {"ambient_temp": 1.0, "coil_temp": -6.5, "working_status_register": 1 << 1},
            now=100.0,
        )
        self.assertEqual(res_heat["coil_ambient_delta"], 7.5)

        # Active defrost heats coil to +43°C -> must clamp to 0.0 (never negative)
        res_def = tracker.compute(
            {"ambient_temp": 4.0, "coil_temp": 43.0, "working_status_register": 1 << 7},
            now=200.0,
        )
        self.assertEqual(res_def["coil_ambient_delta"], 0.0)

        # Post-defrost still-warm coil (coil > ambient) -> clamped to 0.0
        res_post = tracker.compute(
            {"ambient_temp": 1.0, "coil_temp": 12.0, "working_status_register": 0},
            now=300.0,
        )
        self.assertEqual(res_post["coil_ambient_delta"], 0.0)

    def test_operating_state_priority_and_modes(self):
        """Verify operating_state priority across alarm, off, defrost, antilegionella, demands."""
        base = {
            "_control_0032": 1,
            "working_status_register": 0,
            "output_symbol_1": 0,
            "output_symbol_2": 0,
            "unit_mode": 1,
        }
        self.assertEqual(compute_operating_state(base), "idle")
        self.assertEqual(compute_operating_state({**base, "_control_0032": 0}), "off")
        self.assertEqual(
            compute_operating_state({**base, "working_status_register": 1 << 6}),
            "alarm",
        )
        self.assertEqual(
            compute_operating_state({**base, "working_status_register": 1 << 7, "output_symbol_1": 1}),
            "defrost",
        )
        self.assertEqual(
            compute_operating_state({**base, "working_status_register": 1 << 4, "output_symbol_1": 1}),
            "antilegionella",
        )
        self.assertEqual(
            compute_operating_state({**base, "working_status_register": 1 << 1, "output_symbol_1": 1}),
            "heating",
        )
        self.assertEqual(
            compute_operating_state({**base, "working_status_register": 1 << 5, "output_symbol_1": 1}),
            "cooling",
        )
        self.assertEqual(
            compute_operating_state({**base, "working_status_register": 1 << 0, "output_symbol_1": 1}),
            "hot_water",
        )
        self.assertEqual(
            compute_operating_state(
                {**base, "working_status_register": (1 << 0) | (1 << 1), "output_symbol_1": 1}
            ),
            "heating_hot_water",
        )
        self.assertIsNone(compute_operating_state({"_control_0032": 1}))

    def test_eco_curve_setpoint_interpolation_sorting_and_clamping(self):
        """Verify E01-E24 piecewise-linear interpolation, clamping, and out-of-order sorting."""
        curve_data = {
            "ambient_temp_filtered": 0.0,
            "working_status_register": 1 << 1,  # heating demand
            "output_symbol_2": 0,
            "unit_mode": 1,
            # Intentionally out-of-order ambient breakpoints (like older firmware defaults)
            "econ_heat_ambi_1": -15,
            "econ_heat_ambi_2": 18,
            "econ_heat_ambi_3": 7,
            "econ_heat_ambi_4": -5,
            "econ_heat_temp_1": 50.0,
            "econ_heat_temp_2": 32.0,
            "econ_heat_temp_3": 38.0,
            "econ_heat_temp_4": 44.0,
        }
        # Between (-5, 44.0) and (7, 38.0) at 0.0 => 44.0 + (5/12)*(-6.0) = 41.5
        self.assertEqual(compute_eco_curve_setpoint(curve_data), 41.5)
        # Clamp below min
        self.assertEqual(
            compute_eco_curve_setpoint({**curve_data, "ambient_temp_filtered": -25.0}),
            50.0,
        )
        # Clamp above max
        self.assertEqual(
            compute_eco_curve_setpoint({**curve_data, "ambient_temp_filtered": 25.0}),
            32.0,
        )

    def test_duration_trackers(self):
        """Verify live and held cycle duration tracking for compressor and defrost."""
        tracker = ChicoDerivedTracker()
        # Idle initially -> 0.0 and no completed cycle yet
        res0 = tracker.compute({"working_status_register": 0, "output_symbol_1": 0}, now=1000.0)
        self.assertEqual(res0["compressor_last_run_duration"], 0.0)
        self.assertNotIn("compressor_last_completed_duration", res0)
        self.assertEqual(res0["defrost_last_duration"], 0.0)
        self.assertEqual(res0["defrost_last_interval"], 0.0)

        # Compressor starts at t=1000, defrost starts at t=1300
        res1 = tracker.compute({"working_status_register": 0, "output_symbol_1": 1}, now=1000.0)
        self.assertEqual(res1["compressor_last_run_duration"], 0.0)
        self.assertNotIn("compressor_last_completed_duration", res1)
        self.assertEqual(res1["defrost_last_interval"], 0.0)

        res2 = tracker.compute({"working_status_register": 1 << 7, "output_symbol_1": 1}, now=1300.0)
        self.assertEqual(res2["compressor_last_run_duration"], 5.0)
        self.assertNotIn("compressor_last_completed_duration", res2)
        self.assertEqual(res2["defrost_last_duration"], 0.0)
        self.assertEqual(res2["defrost_last_interval"], 0.0)

        # Defrost ends at t=1540 (4.0 min), compressor stops at t=1900 (15.0 min)
        res3 = tracker.compute({"working_status_register": 0, "output_symbol_1": 1}, now=1540.0)
        self.assertEqual(res3["defrost_last_duration"], 4.0)
        self.assertEqual(res3["defrost_last_interval"], 0.0)
        self.assertEqual(res3["compressor_last_run_duration"], 9.0)

        res4 = tracker.compute({"working_status_register": 0, "output_symbol_1": 0}, now=1900.0)
        self.assertEqual(res4["compressor_last_run_duration"], 15.0)
        self.assertEqual(res4["compressor_last_completed_duration"], 15.0)
        self.assertEqual(res4["defrost_last_duration"], 4.0)
        self.assertEqual(res4["defrost_last_interval"], 6.0)

        # Remains held while idle for compressor, while defrost_last_interval continues counting live
        res5 = tracker.compute({"working_status_register": 0, "output_symbol_1": 0}, now=2500.0)
        self.assertEqual(res5["compressor_last_run_duration"], 15.0)
        self.assertEqual(res5["compressor_last_completed_duration"], 15.0)
        self.assertEqual(res5["defrost_last_interval"], 16.0)

        # New compressor cycle starts at t=5500 -> live duration resets to 0..2 min, completed stays 15.0
        res6 = tracker.compute({"working_status_register": 1 << 7, "output_symbol_1": 1}, now=5500.0)
        self.assertEqual(res6["defrost_last_interval"], 66.0)
        self.assertEqual(res6["compressor_last_run_duration"], 0.0)
        self.assertEqual(res6["compressor_last_completed_duration"], 15.0)
        res7 = tracker.compute({"working_status_register": 1 << 7, "output_symbol_1": 1}, now=5620.0)
        self.assertEqual(res7["defrost_last_interval"], 66.0)
        self.assertEqual(res7["compressor_last_run_duration"], 2.0)
        self.assertEqual(res7["compressor_last_completed_duration"], 15.0)
        res8 = tracker.compute({"working_status_register": 0, "output_symbol_1": 1}, now=5740.0)
        self.assertEqual(res8["defrost_last_duration"], 4.0)
        self.assertEqual(res8["defrost_last_interval"], 0.0)

    def test_thermodynamic_diffs_and_estimated_power(self):
        """Verify delta T, condenser approach, superheats, and experimental power estimate."""
        controller = ChicoController()
        data = {
            "inlet_temp": 29.9,
            "outlet_temp": 32.0,
            "cond_temp": 33.8,
            "suction_gas_temp": -3.0,
            "evap_temp": -5.0,
            "exhaust_temp": 68.0,
            "ambient_temp": 0.5,
            "coil_temp": -4.5,
            "compressor_frequency": 29,
            "working_status_register": 1 << 1,
            "output_symbol_1": 1,
            "output_symbol_2": 1,  # chassis_heater ON
            "unit_mode": 1,
            "econ_heat_ambi_1": -15,
            "econ_heat_ambi_2": 18,
            "econ_heat_ambi_3": 7,
            "econ_heat_ambi_4": -5,
            "econ_heat_temp_1": 50.0,
            "econ_heat_temp_2": 32.0,
            "econ_heat_temp_3": 38.0,
            "econ_heat_temp_4": 44.0,
        }
        res = controller.compute_derived_data(data, now=1000.0)
        self.assertEqual(res["water_delta_t"], 2.1)
        self.assertEqual(res["condenser_approach_temp"], 1.8)
        self.assertEqual(res["suction_superheat"], 2.0)
        self.assertEqual(res["discharge_superheat"], 34.2)
        self.assertEqual(res["coil_ambient_delta"], 5.0)
        self.assertEqual(res["eco_active_setpoint"], 41.2)
        self.assertEqual(res["eco_setpoint_delta"], -9.2)
        self.assertGreater(res["estimated_power"], 900.0)
        self.assertLess(res["estimated_power"], 1100.0)

        # Idle with and without chassis heater
        self.assertEqual(
            compute_estimated_power({"compressor_frequency": 0, "output_symbol_2": 0}),
            90.0,
        )
        self.assertEqual(
            compute_estimated_power({"compressor_frequency": 0, "output_symbol_2": 1}),
            133.0,
        )

    def test_derived_sensor_entity_metadata_and_attributes(self):
        """Verify SPRSUNDerivedSensor exposes descriptions, formulas, and disclaimers."""
        coordinator = MagicMock()
        coordinator.last_update_success = True
        coordinator.data = {
            "outlet_temp": {"value": 34.0, "updated_at": 1000.0},
            "inlet_temp": {"value": 30.0, "updated_at": 1000.0},
            "compressor_frequency": {"value": 0, "updated_at": 1000.0},
            "output_symbol_2": {"value": 0, "updated_at": 1000.0},
        }
        config_entry = MagicMock()
        config_entry.entry_id = "entry_derived"
        config_entry.data = {CONF_NAME: "SPRSUN Heat Pump"}

        by_key = {spec.key: spec for spec in CHICO_DERIVED_SENSORS}

        delta_ent = SPRSUNDerivedSensor(coordinator, config_entry, by_key["water_delta_t"])
        self.assertTrue(delta_ent.available)
        self.assertEqual(delta_ent.native_value, 4.0)
        self.assertTrue(getattr(delta_ent, "_attr_entity_registry_enabled_default", True))
        self.assertIn("description", delta_ent.extra_state_attributes)
        self.assertIn("formula", delta_ent.extra_state_attributes)
        self.assertNotIn("experimental", delta_ent.extra_state_attributes)

        power_ent = SPRSUNDerivedSensor(coordinator, config_entry, by_key["estimated_power"])
        self.assertEqual(power_ent.native_value, 90.0)
        self.assertTrue(power_ent.extra_state_attributes["experimental"])
        self.assertIn("EXPERIMENTAL APPROXIMATION ONLY", power_ent.extra_state_attributes["disclaimer"])

        approach_ent = SPRSUNDerivedSensor(coordinator, config_entry, by_key["condenser_approach_temp"])
        self.assertEqual(approach_ent.entity_category, EntityCategory.DIAGNOSTIC)
        self.assertFalse(approach_ent.available)

        cycle_ent = SPRSUNDerivedSensor(
            coordinator, config_entry, by_key["compressor_last_run_duration"]
        )
        self.assertNotIn("last_completed_minutes", cycle_ent.extra_state_attributes)
        coordinator.data["compressor_last_completed_duration"] = 24.5
        self.assertEqual(cycle_ent.extra_state_attributes["last_completed_minutes"], 24.5)

    def test_coordinator_sync_update_populates_derived_data(self):
        """Verify SPRSUNDataUpdateCoordinator._sync_update populates derived sensor keys."""
        hass = MagicMock()
        coord = SPRSUNDataUpdateCoordinator(hass, "127.0.0.1", 502, 1, 10, "chico")

        def fake_read(client, device_address, initial_read=False):
            return {
                "inlet_temp": 30.0,
                "outlet_temp": 33.5,
                "ambient_temp": 2.0,
                "cond_temp": 35.0,
                "evap_temp": -4.0,
                "suction_gas_temp": -1.5,
                "exhaust_temp": 65.0,
                "compressor_frequency": 35,
                "working_status_register": 1 << 1,
                "output_symbol_1": 1,
                "output_symbol_2": 0,
                "_control_0032": 1,
                "unit_mode": 1,
            }

        with (
            patch.object(coord, "_ensure_connection", return_value=True),
            patch.object(coord.controller, "read_all_registers", side_effect=fake_read),
        ):
            updated = coord._sync_update()

        self.assertEqual(updated["water_delta_t"]["value"], 3.5)
        self.assertEqual(updated["operating_state"]["value"], "heating")
        self.assertEqual(updated["ambient_temp_filtered"]["value"], 2.0)
        self.assertIn("estimated_power", updated)
        self.assertEqual(updated["compressor_starts_24h"]["value"], 1)
        self.assertEqual(updated["defrost_count_24h"]["value"], 0)

    def test_rolling_24h_counters_pruning_and_persistence(self):
        """Verify 24h rolling counters track intervals, prune >24h history, and restore safely."""
        tracker = ChicoDerivedTracker()
        t0 = 100_000.0
        # Cycle 1: defrost 4 min (t0..t0+240), compressor on (t0..t0+600), heating heater on (t0+60..t0+360)
        tracker.compute({"working_status_register": 1 << 7, "output_symbol_1": 1, "output_symbol_2": 0}, now=t0)
        tracker.compute({"working_status_register": 1 << 7, "output_symbol_1": 1, "output_symbol_2": 1 << 5}, now=t0 + 60)
        tracker.compute({"working_status_register": 0, "output_symbol_1": 1, "output_symbol_2": 1 << 5}, now=t0 + 240)
        res = tracker.compute({"working_status_register": 0, "output_symbol_1": 1, "output_symbol_2": 0}, now=t0 + 360)
        self.assertEqual(res["defrost_count_24h"], 1)
        self.assertEqual(res["defrost_time_24h"], 4.0)
        self.assertEqual(res["compressor_starts_24h"], 1)
        self.assertEqual(res["heaters_time_24h"], 5.0)

        # Export at t0+500 while compressor is still active, then restore after short 45s HA restart
        snapshot = tracker.export_state(now=t0 + 500)
        restored = ChicoDerivedTracker()
        restored.restore_state(snapshot, now=t0 + 545)
        res_after_restart = restored.compute(
            {"working_status_register": 0, "output_symbol_1": 1, "output_symbol_2": 0},
            now=t0 + 545,
        )
        # Continues the same compressor cycle without adding a fake start, then stops at t0+600
        self.assertEqual(res_after_restart["compressor_starts_24h"], 1)
        self.assertEqual(res_after_restart["defrost_count_24h"], 1)
        restored.compute(
            {"working_status_register": 0, "output_symbol_1": 0, "output_symbol_2": 0},
            now=t0 + 600,
        )

        # After 24h + 601s, Cycle 1 falls completely out of the rolling 24h window
        res_expired = restored.compute(
            {"working_status_register": 0, "output_symbol_1": 0, "output_symbol_2": 0},
            now=t0 + 86400.0 + 601.0,
        )
        self.assertEqual(res_expired["defrost_count_24h"], 0)
        self.assertEqual(res_expired["defrost_time_24h"], 0.0)
        self.assertEqual(res_expired["compressor_starts_24h"], 0)
        self.assertEqual(res_expired["heaters_time_24h"], 0.0)

        # Long outage (> 3 min) closes pre-shutdown active run cleanly at last_seen
        long_gap = ChicoDerivedTracker()
        long_gap.restore_state(snapshot, now=t0 + 500 + 600)
        res_gap = long_gap.compute(
            {"working_status_register": 0, "output_symbol_1": 1, "output_symbol_2": 0},
            now=t0 + 1100,
        )
        self.assertEqual(res_gap["compressor_starts_24h"], 2)


if __name__ == "__main__":
    unittest.main()
