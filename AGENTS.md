# Agent Guidelines for SPRSUN Modbus Integration

These instructions are mandatory for all AI agents, coding assistants, and contributors working on this repository.

---

## ⚡ Mandatory Workflow (After Every Change)

For **every code, logic, or configuration change**, you MUST execute the following three steps before finalizing:

### 1. Test Updates (`aktualizacja testów`)
- **Always update existing tests or add new unit tests** in `tests/` for any modified or newly added functionality.
- Ensure all new code paths, error handling, parameter mappings, and edge cases are covered.
- Never delete or disable failing tests unless the requirement they test was intentionally deprecated or altered.

### 2. Test Execution (`testy`)
- Run the full test suite locally before finishing:
  ```bash
  python3 -m unittest discover tests
  ```
  *(or `pytest tests/ -v` if pytest is installed in your environment)*
- **Requirement:** 100% of tests must pass (0 failures, 0 errors). If any test fails, fix the issue immediately before proceeding.

### 3. Documentation Updates (`aktualizacja dokumentacji`)
- **Always synchronize documentation** with code changes:
  - If register addresses, parameters, scales, or behaviors change, update [docs/CHICO_PARAMETERS_GUIDE.md](docs/CHICO_PARAMETERS_GUIDE.md) and [docs/CHICO_MODBUS_REFERENCE.md](docs/CHICO_MODBUS_REFERENCE.md).
  - If integration features, configuration options, or platforms change, update [README.md](README.md).
  - If new strings are added, update `strings.json`, `translations/en.json`, and `translations/pl.json`.

---

## 🌐 Language & Localization Standards

- **English is the Native Language:**
  - All source code, constant identifiers, entity names, comments, docstrings, commit messages, and documentation (`docs/*.md`, `README.md`) MUST be in English.
- **Polish is Exclusively for Home Assistant Translation:**
  - The ONLY permitted place for Polish text in the entire repository is:
    ```
    custom_components/sprsun_modbus/translations/pl.json
    ```
  - Do NOT create external Polish markdown files, documentation translation folders, or duplicate dashboard files.
  - When modifying `strings.json`, ensure both `translations/en.json` (English) and `translations/pl.json` (Polish) are kept in parity.

---

## 🏗️ Architecture & Communication Rules

- **Modbus Stability & Safety:**
  - Respect `INTER_WRITE_DELAY` (defined in `const.py`) between consecutive write operations to allow the heat pump MCU to commit changes to EEPROM.
  - Use bit-masking operations for bitfield registers (`0x0032`, `0x0033`, `0x0034`) to prevent clobbering adjacent flags.
  - Modbus parameter write commands are strictly restricted to Device Address `#1` per the hardware protocol.
- **Controller Separation:**
  - Controller-specific Modbus logic belongs in `custom_components/sprsun_modbus/controllers/`. CHICO is the exclusively supported controller driver.
