#!/usr/bin/env python3
"""Stop hook enforcing local test/lint verification when code files have uncommitted edits."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )


def main() -> int:
    raw = ""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    if payload.get("continuationActive"):
        print("{}")
        return 0

    termination_reason = payload.get("terminationReason", "NO_TOOL_CALL")
    if termination_reason != "NO_TOOL_CALL":
        print("{}")
        return 0

    repo_root = Path(__file__).resolve().parents[2]
    dirty = _git(repo_root, "status", "--porcelain", "--", "custom_components/", "tests/")
    if dirty.returncode != 0 or not dirty.stdout.strip():
        print("{}")
        return 0

    branch_res = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch_res.stdout.strip()
    if branch == "main":
        print(
            json.dumps(
                {
                    "decision": "continue",
                    "reason": (
                        "Uncommitted code/test edits were detected while on branch 'main'. "
                        "Per AGENTS.md, never work on 'main' — create or switch to a dedicated "
                        "feat/fix/refactor/chore branch and verify before finishing."
                    ),
                }
            )
        )
        return 0

    verify_script = (
        repo_root / ".agents" / "skills" / "sprsun-beta-staging" / "scripts" / "verify.sh"
    )
    if not verify_script.is_file():
        print("{}")
        return 0

    res = subprocess.run(
        ["bash", str(verify_script)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=50,
        check=False,
    )
    if res.returncode == 0:
        print("{}")
        return 0

    combined = ((res.stdout or "") + "\n" + (res.stderr or "")).strip()
    tail = "\n".join(combined.splitlines()[-25:])
    print(
        json.dumps(
            {
                "decision": "continue",
                "reason": (
                    "Local verification (.agents/skills/sprsun-beta-staging/scripts/verify.sh) "
                    "failed on uncommitted changes in custom_components/ or tests/. "
                    f"Fix the failures before finishing:\n{tail}"
                ),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
