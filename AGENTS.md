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

---

## Release & Deployment Protocol

Never create or push a stable release tag (`vX.Y.Z`) directly after making code changes. Always follow this staged procedure:

1. **Local Verification:**
   - 100% of unit tests must pass (`python3 -m unittest discover tests`).
   - Linter checks must pass cleanly (`ruff check .`).

2. **Pre-release Staging (Beta):**
   - Bump version in `custom_components/sprsun_modbus/manifest.json` with a beta suffix (e.g. `5.1.7b1`).
   - Create a pre-release tag (e.g. `v5.1.7-beta.1`) and push to GitHub.
   - GitHub Actions runs full unit tests (Python 3.12/3.13), Hassfest, HACS validation, and Ruff on the tag. Only upon 100% success does it publish the release, automatically marked as Pre-release (`prerelease: true`).

3. **Live Testing & Verification via MCP:**
   - Refresh HACS repository info: `ha_manage_hacs(action="update_information", repository_id="stasek44/sprsun-modbus")`.
   - Download the beta version: `ha_manage_hacs(action="download", repository_id="stasek44/sprsun-modbus", version="v5.1.7-beta.1")`.
   - Restart Home Assistant: `ha_restart(confirm=True)`.
   - Verify post-restart health:
     - Check integration state is `loaded` (`ha_get_integration`).
     - Check logs for any exceptions or warnings (`ha_get_logs(search="sprsun")`).
     - Verify entity states and attributes match expectations (`ha_get_state`).

4. **Production Release (Stable):**
   - Only after live verification passes cleanly and the user confirms, bump `manifest.json` to the final stable version (`5.1.7`).
   - Create the clean stable tag `v5.1.7` and push to GitHub.
   - GitHub Actions executes unit tests and quality validations before publishing the stable release as Latest.
