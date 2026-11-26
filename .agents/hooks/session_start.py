#!/usr/bin/env python3
"""SessionStart hook injecting SPRSUN repository branch, tooling, and skill pointers."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def _git_branch(repo_root: Path) -> str:
    try:
        res = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        branch = res.stdout.strip()
        return branch if res.returncode == 0 and branch else "unknown"
    except Exception:
        return "unknown"


def main() -> int:
    try:
        sys.stdin.read()
    except Exception:
        pass

    repo_root = Path(__file__).resolve().parents[2]
    branch = _git_branch(repo_root)
    has_pytest = (repo_root / ".venv" / "bin" / "pytest").is_file()
    has_ruff = (repo_root / ".venv" / "bin" / "ruff").is_file()
    has_roadmap = (repo_root / "docs" / "ROADMAP.md").is_file()

    msg = (
        f"SPRSUN Modbus repo context: branch='{branch}', "
        f"venv_tools=(pytest:{has_pytest}, ruff:{has_ruff}), "
        f"roadmap_present={has_roadmap}. "
        "Workflow: load skill 'sprsun-task-plan' before editing code for any roadmap/feature/fix task "
        "(stop for user approval before coding), and load 'sprsun-beta-staging' for implementation, "
        "verification (.agents/skills/sprsun-beta-staging/scripts/verify.sh), beta tagging, and live HA checks. "
        "Never commit, tag, or push directly on 'main'."
    )
    if branch == "main":
        msg += " WARNING: currently on 'main' — create a dedicated branch after plan approval."

    print(
        json.dumps(
            {
                "injectSteps": [
                    {
                        "systemMessage": {
                            "systemMessage": msg,
                        }
                    }
                ]
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
