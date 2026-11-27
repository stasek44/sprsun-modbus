"""Unit tests for the built-in Lovelace dashboard strategy and i18n assets."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import setup_mocks

setup_mocks()

from custom_components.sprsun_modbus.const import (  # noqa: E402
    CONF_CONTROLLER_TYPE,
    CONF_ENABLE_DERIVED_SENSORS,
    CONF_ENABLE_EXPERT_WRITES,
    DOMAIN,
)
from custom_components.sprsun_modbus.controllers.chico import ChicoController  # noqa: E402
from custom_components.sprsun_modbus.dashboard import (  # noqa: E402
    STATIC_URL_PATH,
    STRATEGY_JS_FILENAME,
    async_register_dashboard,
    build_dashboard_context,
)

FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "sprsun_modbus"
    / "frontend"
)
I18N_DIR = FRONTEND_DIR / "i18n"

TRANSLATION_TOKEN_RE = re.compile(r"\[\[t:([a-z0-9_]+)\]\]")
ENTITY_TOKEN_RE = re.compile(r"\[\[ent:([a-z_]+):([a-z0-9_]+)\]\]")
ANY_UNRESOLVED_RE = re.compile(r"\[\[[^\]]+\]\]")


def _collect_strings(node: object) -> list[str]:
    """Recursively collect all string values from a JSON structure."""
    if isinstance(node, str):
        return [node]
    if isinstance(node, list):
        out: list[str] = []
        for item in node:
            out.extend(_collect_strings(item))
        return out
    if isinstance(node, dict):
        out = []
        for val in node.values():
            out.extend(_collect_strings(val))
        return out
    return []


class TestDashboardTemplatesAndI18n(unittest.TestCase):
    """Verify single-source templates, i18n JSON parity, and entity key validity."""

    def test_i18n_files_have_identical_keys(self):
        """All dashboard i18n files must have the exact same key set as en.json."""
        en_data = json.loads((I18N_DIR / "en.json").read_text(encoding="utf-8"))
        self.assertGreater(len(en_data), 200)

        i18n_files = sorted(I18N_DIR.glob("*.json"))
        self.assertGreaterEqual(len(i18n_files), 2)
        for path in i18n_files:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(
                set(data.keys()),
                set(en_data.keys()),
                f"Key mismatch in {path.name}",
            )
            for key, val in data.items():
                self.assertIsInstance(val, str, f"{path.name}:{key} must be a string")
                self.assertTrue(val.strip(), f"{path.name}:{key} must not be empty")

    def test_templates_resolve_all_tokens_without_leftovers(self):
        """Every [[t:...]] and [[ent:...]] token in templates must resolve cleanly."""
        ctrl = ChicoController()
        valid_entities = {
            ("sensor", s.key) for s in ctrl.get_sensors()
        } | {
            ("sensor", s.key) for s in ctrl.get_expert_sensors()
        } | {
            ("sensor", s.key) for s in ctrl.get_derived_sensors()
        } | {
            ("binary_sensor", s.key) for s in ctrl.get_binary_sensors()
        } | {
            ("binary_sensor", s.key) for s in ctrl.get_expert_binary_sensors()
        } | {
            ("number", s.key) for s in ctrl.get_numbers()
        } | {
            ("number", s.key) for s in ctrl.get_expert_numbers()
        } | {
            ("select", s.key) for s in ctrl.get_selects()
        } | {
            ("select", s.key) for s in ctrl.get_expert_selects()
        } | {
            ("switch", s.key) for s in ctrl.get_switches()
        } | {
            ("switch", s.key) for s in ctrl.get_expert_switches()
        } | {
            ("button", s.key) for s in ctrl.get_buttons()
        } | {
            ("climate", "climate"),
            ("climate", "dhw_climate"),
        }

        i18n_by_lang = {
            path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in I18N_DIR.glob("*.json")
        }

        for tpl_name in ("sprsun_dashboard_chico.json", "sprsun_control_card_chico.json"):
            tpl_path = FRONTEND_DIR / tpl_name
            self.assertTrue(tpl_path.is_file(), f"Missing template {tpl_name}")
            tpl_data = json.loads(tpl_path.read_text(encoding="utf-8"))
            strings = _collect_strings(tpl_data)

            for lang, tr in i18n_by_lang.items():
                for s in strings:
                    resolved = TRANSLATION_TOKEN_RE.sub(lambda m: tr[m.group(1)], s)
                    for m in ENTITY_TOKEN_RE.finditer(resolved):
                        pair = (m.group(1), m.group(2))
                        self.assertIn(
                            pair,
                            valid_entities,
                            f"Unknown entity token {pair} in {tpl_name} ({lang})",
                        )
                    resolved = ENTITY_TOKEN_RE.sub(
                        lambda m: f"{m.group(1)}.sprsun_heat_pump_{m.group(2)}",
                        resolved,
                    )
                    self.assertIsNone(
                        ANY_UNRESOLVED_RE.search(resolved),
                        f"Unresolved placeholder in {tpl_name} ({lang}): {resolved}",
                    )

    def test_strategy_js_defines_custom_elements_and_registrations(self):
        """Strategy JS must register dashboard & section custom elements."""
        js_text = (FRONTEND_DIR / STRATEGY_JS_FILENAME).read_text(encoding="utf-8")
        self.assertIn("ll-strategy-dashboard-sprsun", js_text)
        self.assertIn("ll-strategy-section-sprsun-control", js_text)
        self.assertIn("window.customStrategies", js_text)
        self.assertIn("sprsun_modbus/get_dashboard_context", js_text)


class TestDashboardBackend(unittest.IsolatedAsyncioTestCase):
    """Test backend entity context builder and static/WS registration."""

    def test_build_dashboard_context_resolves_renamed_entities(self):
        """Entity map must resolve renamed device/entity IDs via unique_id keys."""
        from homeassistant.helpers import entity_registry as er

        entry = MagicMock()
        entry.entry_id = "entry_abc"
        entry.title = "Pompa Ciepła"
        entry.data = {CONF_CONTROLLER_TYPE: "chico"}
        entry.options = {
            CONF_ENABLE_DERIVED_SENSORS: True,
            CONF_ENABLE_EXPERT_WRITES: False,
        }

        hass = MagicMock()
        hass.data = {}
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries.return_value = [entry]

        reg_entries = [
            MagicMock(
                domain="sensor",
                unique_id="entry_abc_inlet_temp",
                entity_id="sensor.pompa_ciepla_inlet_water_temperature",
            ),
            MagicMock(
                domain="sensor",
                unique_id="entry_abc_operating_state",
                entity_id="sensor.custom_state_entity",
            ),
            MagicMock(
                domain="climate",
                unique_id="entry_abc_climate",
                entity_id="climate.pompa_ciepla_co",
            ),
        ]

        with (
            patch.object(er, "async_get", return_value=MagicMock()),
            patch.object(er, "async_entries_for_config_entry", return_value=reg_entries),
        ):
            ctx = build_dashboard_context(hass)

        self.assertEqual(ctx["entry_id"], "entry_abc")
        self.assertEqual(ctx["controller_type"], "chico")
        self.assertTrue(ctx["enable_derived_sensors"])
        self.assertFalse(ctx["enable_expert_writes"])
        # Exact registered overrides:
        self.assertEqual(ctx["entities"]["sensor:operating_state"], "sensor.custom_state_entity")
        self.assertEqual(ctx["entities"]["climate:climate"], "climate.pompa_ciepla_co")
        # Disabled/unregistered entities inherit inferred device prefix "pompa_ciepla":
        self.assertEqual(
            ctx["entities"]["number:h01_defrost_freq"],
            "number.pompa_ciepla_h01_defrost_frequency",
        )

    def test_build_dashboard_context_without_entries(self):
        """Context returns clean defaults when no config entry is present."""
        hass = MagicMock()
        hass.data = {}
        hass.config_entries = MagicMock()
        hass.config_entries.async_entries.return_value = []

        ctx = build_dashboard_context(hass)
        self.assertIsNone(ctx["entry_id"])
        self.assertEqual(ctx["controller_type"], "chico")
        self.assertEqual(ctx["entities"], {})

    async def test_async_register_dashboard_idempotent(self):
        """Static path, extra JS URL, and WS command register once idempotently."""
        from homeassistant.components import frontend, websocket_api

        hass = MagicMock()
        hass.data = {}
        hass.http = MagicMock()
        hass.http.async_register_static_paths = AsyncMock()

        with (
            patch.object(frontend, "add_extra_js_url") as mock_add_js,
            patch.object(websocket_api, "async_register_command") as mock_ws,
        ):
            await async_register_dashboard(hass, "5.5.0b1")
            await async_register_dashboard(hass, "5.5.0b1")

        hass.http.async_register_static_paths.assert_awaited_once()
        mock_add_js.assert_called_once_with(
            hass, f"{STATIC_URL_PATH}/{STRATEGY_JS_FILENAME}?v=5.5.0b1"
        )
        mock_ws.assert_called_once()
        # DOMAIN dict must remain untouched so async_unload_entry keeps working
        self.assertNotIn(DOMAIN, hass.data)


if __name__ == "__main__":
    unittest.main()
