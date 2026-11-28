"""Protocol safety invariants, AST write guards, and multi-controller contract tests.

These tests enforce Modbus safety rules across CHICO and any future controller
registered in ``CONTROLLER_REGISTRY`` (e.g. Carel). Failures are formatted to give
clear actionable diagnostics to developers and AI agents before code is released.
"""
from __future__ import annotations

import ast
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, MagicMock

from tests.conftest import setup_mocks

setup_mocks()

from homeassistant.components.climate import HVACMode  # noqa: E402
from homeassistant.exceptions import HomeAssistantError  # noqa: E402

from custom_components.sprsun_modbus.controllers import (  # noqa: E402
    CONTROLLER_REGISTRY,
    DataType,
    RegisterSpace,
    decode_registers,
    encode_registers,
)

_INTEGRATION_DIR = (
    Path(__file__).resolve().parents[1] / "custom_components" / "sprsun_modbus"
)
_WRITE_METHOD_PREFIXES = (
    "async_set_",
    "_async_set_",
    "async_write_",
    "async_select_",
    "async_turn_",
    "async_press",
)

# Registers/bits that must NEVER be exposed as writable entities.
_FORBIDDEN_WRITE_KEYS: dict[str, set[str]] = {
    "chico": {"parameters_reset_flag"},
    "carel": {"factory_reset", "parameters_reset", "insert_bldc_default"},
}
_FORBIDDEN_WRITE_ADDRESSES: dict[str, set[tuple[RegisterSpace, int]]] = {
    "carel": {
        (RegisterSpace.COIL, 57),              # Reset parametrów (00058)
        (RegisterSpace.HOLDING_REGISTER, 332), # Insert BLDC default (40333)
    },
}
_FORBIDDEN_WRITE_BITS: dict[str, set[tuple[RegisterSpace, int, int]]] = {
    "chico": {
        (RegisterSpace.HOLDING_REGISTER, 0x0033, 6),  # parameters_reset_flag
        (RegisterSpace.HOLDING_REGISTER, 0x0034, 2),  # unconfirmed PDF Invalid
        (RegisterSpace.HOLDING_REGISTER, 0x0034, 3),  # unconfirmed PDF Invalid
        (RegisterSpace.HOLDING_REGISTER, 0x0034, 4),  # unconfirmed PDF Invalid
    },
}


def _iter_write_source_files() -> list[Path]:
    """Return integration Python files that perform entity or controller writes."""
    files = [
        _INTEGRATION_DIR / "climate.py",
        _INTEGRATION_DIR / "number.py",
        _INTEGRATION_DIR / "select.py",
        _INTEGRATION_DIR / "switch.py",
        _INTEGRATION_DIR / "button.py",
    ]
    files.extend(sorted((_INTEGRATION_DIR / "controllers").glob("*.py")))
    return [path for path in files if path.is_file()]


def _is_non_none_constant(node: ast.AST) -> bool:
    """Return True when an AST node is anything other than literal None."""
    return not (isinstance(node, ast.Constant) and node.value is None)


def _extract_literal_int(node: ast.AST) -> int | None:
    """Extract an integer literal from an AST node if statically known."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return node.value
    return None


def _collect_protected_holding_addresses() -> set[int]:
    """Collect all holding register addresses requiring masked/bitfield writes."""
    protected: set[int] = set()
    for controller_cls in CONTROLLER_REGISTRY.values():
        ctrl = controller_cls()
        for spec in ctrl.get_numbers() + ctrl.get_expert_numbers() + ctrl.get_sensors() + ctrl.get_expert_sensors():
            if spec.space == RegisterSpace.HOLDING_REGISTER and getattr(spec, "bit_mask", None) is not None:
                protected.add(spec.address)
        for spec in ctrl.get_switches() + ctrl.get_expert_switches() + ctrl.get_buttons():
            if spec.space == RegisterSpace.HOLDING_REGISTER and spec.bit is not None:
                protected.add(spec.address)
    return protected


class TestProtocolInvariants(unittest.IsolatedAsyncioTestCase):
    """Static AST guards, spec round-trips, and controller contract tests."""

    def test_no_cache_default_fallback_in_write_methods(self) -> None:
        """Write paths must never make decisions from cached default fallbacks."""
        violations: list[str] = []

        for path in _iter_write_source_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if not node.name.startswith(_WRITE_METHOD_PREFIXES):
                    continue

                for child in ast.walk(node):
                    if not isinstance(child, ast.Call):
                        continue

                    # Check extract_cache_value(data, key, default)
                    if isinstance(child.func, ast.Name) and child.func.id == "extract_cache_value":
                        has_pos_default = len(child.args) >= 3 and _is_non_none_constant(child.args[2])
                        has_kw_default = any(
                            kw.arg == "default" and _is_non_none_constant(kw.value)
                            for kw in child.keywords
                        )
                        if has_pos_default or has_kw_default:
                            violations.append(
                                f"{path.name}:{child.lineno} in {node.name}(): "
                                "extract_cache_value() uses a non-None default fallback in a write path. "
                                "Read the live register via coordinator.async_read_register() or raise HomeAssistantError."
                            )

                    # Check data.get(key, default)
                    if (
                        isinstance(child.func, ast.Attribute)
                        and child.func.attr == "get"
                        and isinstance(child.func.value, ast.Name)
                        and "data" in child.func.value.id.lower()
                    ):
                        has_pos_default = len(child.args) >= 2 and _is_non_none_constant(child.args[1])
                        has_kw_default = any(
                            kw.arg == "default" and _is_non_none_constant(kw.value)
                            for kw in child.keywords
                        )
                        if has_pos_default or has_kw_default:
                            violations.append(
                                f"{path.name}:{child.lineno} in {node.name}(): "
                                f"{child.func.value.id}.get() uses a non-None default fallback in a write path. "
                                "Read live state or raise HomeAssistantError when unknown."
                            )

        self.assertEqual(violations, [], "\n".join(violations))

    def test_masked_and_bitfield_writes_never_use_unmasked_write_register(self) -> None:
        """Shared bitfield/masked registers must use async_write_masked_register or async_write_bit."""
        protected_addrs = _collect_protected_holding_addresses()
        violations: list[str] = []

        for path in _iter_write_source_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for child in ast.walk(tree):
                if not isinstance(child, ast.Call):
                    continue
                if not (isinstance(child.func, ast.Attribute) and child.func.attr == "async_write_register"):
                    continue

                addr_node: ast.AST | None = child.args[0] if child.args else None
                if addr_node is None:
                    for kw in child.keywords:
                        if kw.arg == "address":
                            addr_node = kw.value
                            break
                if addr_node is None:
                    continue

                addr_val = _extract_literal_int(addr_node)
                if addr_val is not None and addr_val in protected_addrs:
                    violations.append(
                        f"{path.name}:{child.lineno}: raw async_write_register(0x{addr_val:04X}) targets a "
                        "shared bitfield/masked register. Use async_write_masked_register() or async_write_bit()."
                    )

        self.assertEqual(violations, [], "\n".join(violations))

    def test_number_specs_encode_decode_round_trip_and_bounds(self) -> None:
        """All NumberSpecs across every registered controller must round-trip without overflow or sign loss."""
        for ctrl_key, ctrl_cls in CONTROLLER_REGISTRY.items():
            ctrl = ctrl_cls()
            all_numbers = ctrl.get_numbers() + ctrl.get_expert_numbers()
            for spec in all_numbers:
                self.assertGreater(spec.scale, 0, f"{ctrl_key}.{spec.key}: scale must be > 0")
                self.assertGreater(spec.step, 0, f"{ctrl_key}.{spec.key}: step must be > 0")
                self.assertLessEqual(
                    spec.min_value,
                    spec.max_value,
                    f"{ctrl_key}.{spec.key}: min_value > max_value",
                )

                # Guard against negative raw values encoded as unsigned types (known Carel/CHICO pitfall)
                min_raw = (float(spec.min_value) / float(spec.scale)) - float(spec.raw_offset)
                if min_raw < -1e-6:
                    self.assertNotIn(
                        spec.data_type,
                        (DataType.UINT16, DataType.UINT32),
                        f"{ctrl_key}.{spec.key}: min_value={spec.min_value} yields negative raw {min_raw} "
                        f"but uses unsigned {spec.data_type}; switch to INT16/INT32 or verify raw_offset.",
                    )

                probes = [spec.min_value, spec.max_value]
                mid_val = round(spec.min_value + spec.step, 6)
                if mid_val <= spec.max_value:
                    probes.append(mid_val)

                for probe in probes:
                    words = encode_registers(
                        probe,
                        spec.data_type,
                        scale=spec.scale,
                        word_order=spec.word_order,
                        raw_offset=spec.raw_offset,
                        bit_mask=spec.bit_mask,
                    )
                    for word in words:
                        self.assertTrue(
                            0 <= word <= 0xFFFF,
                            f"{ctrl_key}.{spec.key}: word {word} out of 16-bit range for {probe}",
                        )
                    if spec.bit_mask is not None and len(words) == 1:
                        raw_unmasked = int(round((float(probe) / float(spec.scale)) - float(spec.raw_offset)))
                        if spec.data_type == DataType.UINT16:
                            self.assertTrue(
                                0 <= raw_unmasked <= spec.bit_mask,
                                f"{ctrl_key}.{spec.key}: value {probe} (raw={raw_unmasked}) exceeds bit_mask=0x{spec.bit_mask:X}",
                            )

                    decoded = decode_registers(
                        words,
                        spec.data_type,
                        scale=spec.scale,
                        word_order=spec.word_order,
                        raw_offset=spec.raw_offset,
                        bit_mask=spec.bit_mask,
                    )
                    self.assertAlmostEqual(
                        float(decoded),
                        float(probe),
                        places=3,
                        msg=(
                            f"{ctrl_key}.{spec.key}: encode/decode round-trip mismatch for {probe} "
                            f"(words={words}, decoded={decoded}, data_type={spec.data_type}, scale={spec.scale})"
                        ),
                    )

    def test_selects_switches_and_forbidden_write_targets(self) -> None:
        """Validate SelectSpec options, Switch/Button bit indices, and forbidden write blocks."""
        for ctrl_key, ctrl_cls in CONTROLLER_REGISTRY.items():
            ctrl = ctrl_cls()
            forbidden_keys = _FORBIDDEN_WRITE_KEYS.get(ctrl_key, set())
            forbidden_addrs = _FORBIDDEN_WRITE_ADDRESSES.get(ctrl_key, set())
            forbidden_bits = _FORBIDDEN_WRITE_BITS.get(ctrl_key, set())

            writable_specs = (
                ctrl.get_numbers()
                + ctrl.get_expert_numbers()
                + ctrl.get_selects()
                + ctrl.get_expert_selects()
                + ctrl.get_switches()
                + ctrl.get_expert_switches()
                + ctrl.get_buttons()
            )
            for spec in writable_specs:
                self.assertNotIn(
                    spec.key,
                    forbidden_keys,
                    f"{ctrl_key}: forbidden key '{spec.key}' must never be exposed as writable!",
                )
                self.assertNotIn(
                    (spec.space, spec.address),
                    forbidden_addrs,
                    f"{ctrl_key}.{spec.key}: forbidden address ({spec.space}, {spec.address}) exposed!",
                )
                bit = getattr(spec, "bit", None)
                if bit is not None:
                    self.assertTrue(0 <= bit <= 15, f"{ctrl_key}.{spec.key}: invalid bit index {bit}")
                    self.assertNotIn(
                        (spec.space, spec.address, bit),
                        forbidden_bits,
                        f"{ctrl_key}.{spec.key}: forbidden register/bit (0x{spec.address:04X}.{bit}) exposed!",
                    )

            for spec in ctrl.get_selects() + ctrl.get_expert_selects():
                self.assertTrue(spec.options, f"{ctrl_key}.{spec.key}: SelectSpec options cannot be empty")
                labels = list(spec.options.values())
                self.assertEqual(
                    len(labels),
                    len(set(labels)),
                    f"{ctrl_key}.{spec.key}: duplicate SelectSpec option labels detected: {labels}",
                )
                for raw_code in spec.options:
                    self.assertTrue(
                        0 <= raw_code <= 0xFFFF,
                        f"{ctrl_key}.{spec.key}: option key {raw_code} out of 16-bit range",
                    )

    async def test_controller_contract_on_empty_cache_and_offline_reads(self) -> None:
        """Every registered controller must handle missing cache safely and abort writes cleanly."""
        for ctrl_key, ctrl_cls in CONTROLLER_REGISTRY.items():
            ctrl = ctrl_cls()

            # Read/status guards on empty cache
            self.assertFalse(
                ctrl.has_rw_data({}),
                f"{ctrl_key}.has_rw_data({{}}) must return False",
            )

            # Error Modbus responses must never false-match in detect()
            err_client = MagicMock()
            err_res = MagicMock()
            err_res.isError.return_value = True
            err_client.read_holding_registers.return_value = err_res
            err_client.read_input_registers.return_value = err_res
            err_client.read_discrete_inputs.return_value = err_res
            err_client.read_coils.return_value = err_res
            self.assertFalse(
                ctrl_cls.detect(err_client, 1),
                f"{ctrl_key}.detect() must return False when Modbus returns errors",
            )

            # Non-CHICO controllers (e.g. future Carel) must reject all-zero dummy frames
            if ctrl_key != "chico":
                zero_client = MagicMock()
                zero_res = MagicMock()
                zero_res.isError.return_value = False
                zero_res.registers = [0] * 64
                zero_res.bits = [False] * 64
                zero_client.read_holding_registers.return_value = zero_res
                zero_client.read_input_registers.return_value = zero_res
                zero_client.read_discrete_inputs.return_value = zero_res
                zero_client.read_coils.return_value = zero_res
                self.assertFalse(
                    ctrl_cls.detect(zero_client, 1),
                    f"{ctrl_key}.detect() must reject all-zero frames to avoid false-matches",
                )

            caps = ctrl.get_space_climate_capabilities()
            if not caps.enabled:
                continue

            # Empty cache reads must not fabricate heating/cooling mode or target temp
            self.assertIsNone(
                ctrl.get_space_hvac_mode({}),
                f"{ctrl_key}.get_space_hvac_mode({{}}) must return None instead of fabricating a mode",
            )
            self.assertIsNone(
                ctrl.get_space_target_temp({}),
                f"{ctrl_key}.get_space_target_temp({{}}) must return None on empty cache",
            )

            # Offline pre-write read failure must raise HomeAssistantError and perform zero writes
            coord = MagicMock()
            coord.async_read_register = AsyncMock(side_effect=ConnectionError("offline"))
            coord.async_write_register = AsyncMock()
            coord.async_write_masked_register = AsyncMock()
            coord.async_write_bit = AsyncMock()
            coord.async_write_coil = AsyncMock()

            with self.assertRaises(HomeAssistantError):
                await ctrl.async_set_space_hvac_mode(coord, HVACMode.HEAT, {})
            with self.assertRaises(HomeAssistantError):
                await ctrl.async_set_space_temperature(coord, 30.0, {})

            if caps.supports_dhw:
                self.assertIsNone(
                    ctrl.get_dhw_hvac_mode({}),
                    f"{ctrl_key}.get_dhw_hvac_mode({{}}) must return None on empty cache",
                )
                with self.assertRaises(HomeAssistantError):
                    await ctrl.async_set_dhw_hvac_mode(coord, HVACMode.HEAT, {})

            coord.async_write_register.assert_not_called()
            coord.async_write_masked_register.assert_not_called()
            coord.async_write_bit.assert_not_called()
            coord.async_write_coil.assert_not_called()


if __name__ == "__main__":
    unittest.main()
