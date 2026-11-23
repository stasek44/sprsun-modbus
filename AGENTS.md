# Agent Guidelines for SPRSUN Modbus Integration

These instructions apply to all AI agents and contributors working on this repository.

---

## Mandatory Workflow

For every code, logic, or configuration change, execute the following steps before finalizing:

### 1. Test Updates
- Update existing tests or add new unit tests in `tests/` for modified or newly added functionality.
- Ensure all code paths, error handling, parameter mappings, and edge cases are covered.
- Never delete or disable failing tests unless the requirement was intentionally deprecated.

### 2. Test Execution
- Run the full test suite locally:
  ```bash
  python3 -m unittest discover tests
  ```
- Requirement: 100% of tests must pass (0 failures, 0 errors).

### 3. Documentation Updates
- If integration features, configuration options, or platforms change, update `README.md`.
- If new strings are added, update `strings.json`, `translations/en.json`, and `translations/pl.json`.

---

## Architecture & Communication Rules

- **Modbus Stability & Safety:**
  - Respect `INTER_WRITE_DELAY` (defined in `const.py`) between consecutive write operations to allow the heat pump MCU to commit changes to EEPROM.
  - Use bit-masking operations for bitfield registers (`0x0032`, `0x0033`, `0x0034`) to prevent clobbering adjacent flags.
  - Modbus parameter write commands are strictly restricted to Device Address `#1` per the hardware protocol.
- **Controller Separation:**
  - Controller-specific Modbus logic belongs in `custom_components/sprsun_modbus/controllers/`. CHICO is the exclusively supported controller driver.
