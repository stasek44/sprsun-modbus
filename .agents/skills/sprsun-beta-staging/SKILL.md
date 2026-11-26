---
name: sprsun-beta-staging
description: >-
  End-to-end implementation, local verification, beta release staging, Draft PR,
  and live Home Assistant verification workflow for approved SPRSUN Modbus
  changes. Use after a plan is approved or when staging/verifying a beta release.
---

# SPRSUN Implementation, Beta Staging & Live HA Verification

Execute after the user approves the implementation plan (see `sprsun-task-plan`).

## Steps

1. **Create a Dedicated Branch:**
   - Ensure working tree is clean on `main` and create a prefixed branch: `feat/<topic>`, `fix/<topic>`, `refactor/<topic>`, `docs/<topic>`, or `chore/<topic>`.
   - Never commit or push code directly to `main`.

2. **Implement Code, Tests & Mandatory Documentation:**
   - Implement the approved changes keeping controller details inside `custom_components/sprsun_modbus/controllers/`.
   - Add/update unit tests in `tests/` covering register decoding/encoding, edge cases, and HA platform behavior.
   - Update `README.md`, relevant `docs/*.md`, `strings.json`, and `translations/*.json` (`en.json`, `pl.json`) when behavior, options, or user-facing strings change.
   - If `docs/ROADMAP.md` exists, record concise status/decisions for the completed item.

3. **Local Verification Gate:**
   - Run the verification script from the repo root:
     ```bash
     ./.agents/skills/sprsun-beta-staging/scripts/verify.sh
     ```
   - 100% of unit tests (`pytest`) and lint/JSON/syntax checks (`ruff`) must pass before committing.

4. **Stage Beta Release & Draft PR (for functional/Modbus/HA changes):**
   - For doc-only or tooling-only (`chore/`/`docs/`) changes without runtime code changes, skip beta tagging and open a PR directly.
   - For functional/runtime changes:
     1. Bump `custom_components/sprsun_modbus/manifest.json` `"version"` to `"X.Y.ZbN"` (SemVer `PATCH` for fixes, `MINOR` for features).
     2. Commit all changes on the feature branch and create annotated/lightweight tag `vX.Y.Z-beta.N`.
     3. Push branch and tag (`git push -u origin <branch> vX.Y.Z-beta.N`) and open a **Draft PR** targeting `main` (`gh pr create --draft`).
     4. Verify GitHub Actions (`Release`, `Unit Tests`, `Validation & Quality`) pass (`gh run list`).

5. **Live Home Assistant Verification (when `homeassistant` MCP is available):**
   - Refresh Marketplace/HACS metadata: `ha_manage_hacs(action="update_information", repository_id="stasek44/sprsun-modbus")`.
   - Install the beta tag: `ha_manage_hacs(action="download", repository_id="stasek44/sprsun-modbus", version="vX.Y.Z-beta.N")`.
   - Restart Home Assistant (`ha_restart(confirm=True)`), wait ~45–60s using `schedule`, then verify:
     - Integration state is `loaded` (`ha_get_integration(domain="sprsun_modbus")`).
     - `system_log` has `0` unexpected errors or warnings (`ha_get_logs(source="system", search="sprsun")`).
     - `diagnostics` and entity states (`ha_get_state`) reflect expected behavior; test harmless reversible writes if applicable and restore original values afterward.

6. **Stop Before Production Release:**
   - Do **not** mark the PR ready, merge to `main`, or bump to stable `vX.Y.Z` until the maintainer explicitly confirms after live observation.
