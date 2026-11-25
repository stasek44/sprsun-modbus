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
- **Expert / Sensitive Parameters Safety:**
  - Engineering or factory-level parameters that affect compressor limits, protection thresholds, or hardware configuration must be opt-in (e.g., disabled by default in the entity registry or gated behind an integration option) and clearly documented with warnings.

---

## Branching & Pull Request Policy

Keep `main` clean, stable, and always deployable:

1. **Always Work on a Branch:**
   - **Never commit code changes, bug fixes, or new features directly to `main`.**
   - Create a dedicated branch from `main` using a descriptive prefix:
     - `feat/<topic>` — new features (e.g., `feat/expert-settings`)
     - `fix/<topic>` — bug fixes
     - `refactor/<topic>` — internal cleanup/refactoring
     - `docs/<topic>` or `chore/<topic>` — documentation or CI/maintenance updates
2. **Pull Request & CI Checks:**
   - Push the working branch and open a Pull Request targeting `main` (use a **Draft PR** while development or live hardware testing is in progress).
   - Opening a PR triggers GitHub Actions (`test.yaml` and `validate.yaml`) and gives a clear diff for review before merging.
   - Merge into `main` only after local verification and CI checks succeed (and after live verification for behavioral/Modbus changes). Delete temporary branches after merging.

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

### 3. Documentation & Localization (Mandatory Step)
- **Mandatory before commit / handoff / release:** Updating documentation is a required standard step for every change, not an optional follow-up. Before finishing a task or committing a new version, always verify and update:
  - `README.md` (options, features, entity organization, setup notes, documentation links).
  - Relevant guides in `docs/` (`docs/CHICO_MODBUS_REFERENCE.md`, `docs/CHICO_PARAMETERS_GUIDE.md`, `docs/CONTROLLER_ARCHITECTURE.md`) whenever configuration options, register mappings, polling/batching behavior, safety gates, or architecture change.
  - Localization files (`strings.json`, `translations/en.json`, `translations/pl.json`) whenever user-facing strings or options are added or modified.

---

## Maintainer Release & Staging Protocol

Only repository maintainers (or authorized automated release agents) publish tags and releases. Follow SemVer (`PATCH` for fixes/docs, `MINOR` for new features/entities):

1. **Pre-release Staging from Feature Branch (Beta):**
   - Stage and test risky/functional changes **on the feature branch** so `main` stays untouched during testing.
   - Ensure unit tests, Ruff/AST checks, localizations, and documentation updates (`README.md`, `docs/`) are included in the branch commits.
   - Bump `custom_components/sprsun_modbus/manifest.json` to a beta version (e.g. `5.2.0b1`).
   - Commit on the feature branch, create a pre-release tag (e.g. `v5.2.0-beta.1`), and push branch + tag to GitHub.
   - GitHub Actions (`release.yaml`) runs full unit tests (Python 3.12/3.13), Hassfest, HACS validation, and Ruff on the tag, then publishes a **Pre-release** (hidden from standard HACS users).

2. **Live Environment Verification:**
   - Install the beta tag on a test Home Assistant instance (via HACS/Marketplace or manually; automated via `ha-mcp` if available).
   - Restart Home Assistant and verify post-restart health:
     - Integration state is `loaded`.
     - Logs contain 0 unexpected exceptions or warnings.
     - Entity states and Modbus writes/controls behave accurately on hardware.
   - If issues are found, fix them on the same feature branch and stage `vX.Y.Z-beta.2`, etc.

3. **Merge & Production Release (Stable):**
   - Once live verification succeeds, update `manifest.json` on the feature branch to the final stable version (e.g. `5.2.0`).
   - Ensure all PR CI checks (`test.yaml`, `validate.yaml`) are green, then merge the PR into `main` (e.g. squash and merge).
   - Pull the updated `main` locally, create the clean stable tag (e.g. `v5.2.0`), and push the tag to GitHub.
   - GitHub Actions executes unit tests and quality validations on `vX.Y.Z` before publishing the release as **Latest**.
