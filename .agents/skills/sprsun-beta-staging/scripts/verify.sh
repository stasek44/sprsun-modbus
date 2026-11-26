#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN=".venv/bin/python"
PYTEST_BIN=".venv/bin/pytest"
RUFF_BIN=".venv/bin/ruff"

if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

echo "==> Running unit tests..."
if [ -x "$PYTEST_BIN" ]; then
  "$PYTEST_BIN" tests/ -v
else
  "$PYTHON_BIN" -m unittest discover -s tests -v
fi

echo "==> Running Ruff linter..."
if [ -x "$RUFF_BIN" ]; then
  "$RUFF_BIN" check custom_components/
elif command -v ruff >/dev/null 2>&1; then
  ruff check custom_components/
else
  echo "ERROR: ruff not found in .venv/bin/ruff or PATH. Install requirements_dev.txt." >&2
  exit 1
fi

echo "==> Checking Python syntax & JSON files..."
"$PYTHON_BIN" -m compileall -q custom_components tests
"$PYTHON_BIN" -c "import json, pathlib; [json.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('custom_components').rglob('*.json')]"

echo "ALL CHECKS PASSED"
