# Developer & Agent Guidelines for SPRSUN Modbus Integration

These rules apply to all contributors and AI agents operating in this repository.

## Hardware & Architecture Invariants

- **Controller Separation:** Keep controller-specific Modbus registers and logic isolated inside `custom_components/sprsun_modbus/controllers/` behind `ControllerBase`.
- **Modbus Stability & EEPROM Safety:**
  - Respect `INTER_WRITE_DELAY` (`const.py`) between consecutive write operations.
  - Bitfield/shared registers (`0x0032–0x0034`, `0x00CA–0x00CC`, `0x01A4–0x01AC`) must use bit-masking (`async_write_bit` / `async_write_masked_register`) to avoid clobbering adjacent bits or upper bytes.
  - Parameter writes target Modbus Device Address `#1` per the hardware protocol.
- **Expert / Sensitive Parameters Safety:**
  - Engineering/factory parameters (`H`/`A`/`B`/`D`/`F`/`R`, Timebands, expert control bits) stay hidden (`enabled_default=False`) or gated behind `enable_expert_writes` (`NumberMode.BOX`).
  - Never unlock `parameters_reset_flag` (`0x0033` bit 6) or unconfirmed `Invalid` gaps for writing.

## Branching & Workflow Rules

- **Never work, commit, tag, or push directly on `main`.** Always branch from `main` using `feat/<topic>`, `fix/<topic>`, `refactor/<topic>`, `docs/<topic>`, or `chore/<topic>`.
- **Task Planning Gate:** Before editing code for any task from `docs/ROADMAP.md`, feature, or bugfix, load and follow skill **`.agents/skills/sprsun-task-plan/SKILL.md`** (analyze code/protocol, propose plan with trade-offs, and wait for user approval).
- **Implementation, Verification & Beta Staging:** After plan approval, load and follow skill **`.agents/skills/sprsun-beta-staging/SKILL.md`**.
  - Run `.agents/skills/sprsun-beta-staging/scripts/verify.sh` (runs `.venv/bin/pytest`, `.venv/bin/ruff`, JSON validation, and `compileall`) — 100% must pass.
  - Update `README.md`, relevant guides in `docs/`, and `strings.json` / `translations/*.json` whenever behavior, registers, options, or user-facing text change.
  - Stage risky/hardware changes as a beta tag (`vX.Y.Z-beta.N` with `manifest.json` `"X.Y.ZbN"`) on the feature branch, open a Draft PR, and verify live in Home Assistant (`ha-mcp` if available).
  - **Never** merge to `main` or publish a stable `vX.Y.Z` release without explicit maintainer approval after live verification.
