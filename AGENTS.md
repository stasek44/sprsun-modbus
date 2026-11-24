# Developer & Agent Guidelines for SPRSUN Modbus Integration

These guidelines apply to contributors, maintainers, and AI agents working on this repository.

---

## Architecture & Hardware Principles

- **Controller Separation:**
  - Controller-specific Modbus logic belongs exclusively in `custom_components/sprsun_modbus/controllers/`.
  - **CHICO** is the supported controller driver.
  - Adding support for other controllers (e.g., Carel) requires isolating protocol-specific registers and logic within a dedicated controller driver class.
- **Modbus Stability & EEPROM Safety:**
  - Respect `INTER_WRITE_DELAY` (defined in `const.py`) between consecutive write operations to allow the heat pump MCU adequate time to commit values to EEPROM.
  - Bitfield registers (`0x0032`, `0x0033`, `0x0034`) must use bit-masking operations to prevent clobbering adjacent flags during writes.
  - Parameter writes are restricted to Modbus Device Address `#1` per the hardware protocol.

---

## Contributor & Development Workflow

For all bug fixes, features, or configuration modifications:

### 1. Unit Tests
- Add or update tests in `tests/` covering the modified logic, register mappings, and edge cases.
- Never delete or disable failing tests unless the underlying requirement was intentionally deprecated.

### 2. Local Verification
- Run the full test suite locally:
  ```bash
  python3 -m unittest discover tests
  # or using pytest with coverage
  pytest tests/ -v
  ```
- Run code quality checks:
  ```bash
  ruff check .
  ```
- **Requirement:** 100% of tests must pass (0 failures, 0 errors) and Ruff checks must be clean.

### 3. Documentation & Localization
- If configuration options, register behaviors, or features change, update `README.md` and relevant guides in `docs/`.
- If new user-facing strings are added, update `strings.json`, `translations/en.json`, and `translations/pl.json`.

---

## Maintainer Release & Staging Protocol

Only repository maintainers (or authorized automated release agents) publish tags and releases. Releases follow a staged verification pipeline:

1. **Pre-release Staging (Beta):**
   - For changes requiring live hardware/integration validation, bump `manifest.json` to a beta version (e.g. `5.1.8b1`).
   - Create and push a pre-release tag (e.g. `v5.1.8-beta.1`).
   - GitHub Actions executes unit tests (Python 3.12/3.13), Hassfest, HACS validation, and Ruff. Upon 100% pass, it creates a GitHub Release marked as **Pre-release** (hidden from standard HACS users).

2. **Live Environment Verification:**
   - Install/update the beta version on a test Home Assistant instance (via HACS or manually; or automated via `ha-mcp` if available).
   - Verify post-restart health:
     - Integration state is `loaded`.
     - Logs contain 0 unexpected exceptions or warnings.
     - Entity states and controls (climate, numbers, switches) behave accurately.

3. **Production Release (Stable):**
   - Once verified error-free on the live environment, bump `manifest.json` to the final stable version (e.g. `5.1.8`).
   - Create and push the clean stable tag (e.g. `v5.1.8`).
   - GitHub Actions runs the full test and validation suite before publishing the release as **Latest** on GitHub.
