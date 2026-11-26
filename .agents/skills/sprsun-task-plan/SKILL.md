---
name: sprsun-task-plan
description: >-
  Mandatory analysis and planning protocol before modifying code for any SPRSUN
  Modbus roadmap item, feature, or bugfix. Use whenever the user asks to start,
  design, or implement a P0/P1/P2 task, bugfix, or new controller/entity feature.
---

# SPRSUN Task Analysis & Planning Gate

Follow every step in order. Do **not** create a branch or edit source files until Step 5 is explicitly approved by the user.

## Steps

1. **Load Architecture & Backlog Context:**
   - Read [CONTROLLER_ARCHITECTURE.md](../../../docs/CONTROLLER_ARCHITECTURE.md).
   - Read [ROADMAP.md](../../../docs/ROADMAP.md) if present to check scope, acceptance criteria, and prior hardware decisions.

2. **Full Code & Call-Site Analysis:**
   - Locate and read **in full** every function, class, and method touched by the task.
   - Trace the full data flow end-to-end: HA platform (`sensor`, `binary_sensor`, `number`, `select`, `switch`, `button`, `climate`) -> `ControllerBase` / `ChicoController` -> `SPRSUNDataUpdateCoordinator` -> `modbus_helpers` / `pymodbus`.
   - Check affected tests in `tests/` and existing `unique_id` / `coordinator.data` keys to prevent regressions or Home Assistant Recorder mismatches.

3. **Protocol & Hardware Safety Verification:**
   - Check register addresses, `INT16` vs `UINT16`, `scale`, `raw_offset`, `bit_mask`, and word order in [CHICO_MODBUS_REFERENCE.md](../../../docs/CHICO_MODBUS_REFERENCE.md) (or the relevant controller doc).
   - Verify RS485 / Elfin EW11 impact: batch size (`<= 62` registers), `INTER_WRITE_DELAY`, `cache_staleness_seconds`, and expert safety gates (`enable_expert_writes`, `NumberMode.BOX`, `parameters_reset_flag` locked).
   - If `homeassistant` MCP tools are available and read-only checks help (e.g., `ha_get_state`, `ha_get_history`), inspect live entity values/units without modifying device settings.
   - Never copy community register maps uncritically; verify scaling and signedness first.

4. **Present Proposal for Challenge:**
   Provide a concise plan covering:
   - Findings from the current code (and live HA data, if checked).
   - Proposed architectural approach plus concrete alternatives and trade-offs.
   - Exact list of files/symbols to modify, edge cases, and backward-compatibility notes.
   - Planned unit tests and required doc/translation updates (`README.md`, `docs/`, `strings.json`, `translations/*.json`).

5. **Approval Gate (HARD STOP):**
   - Stop and wait for explicit user approval (or answers to open design choices) before creating any branch or editing any file.
   - Once approved, switch to skill `sprsun-beta-staging`.
