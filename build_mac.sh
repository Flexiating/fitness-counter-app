#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PYTHON_BIN=""
for candidate in python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1; then PYTHON_BIN="$candidate"; break; fi
done
if [ -z "$PYTHON_BIN" ]; then echo "Python 3.10 or 3.11 is required."; exit 1; fi
PYTHON_VERSION="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
VENV_DIR=".venv-$PYTHON_VERSION"
if [ ! -x "$VENV_DIR/bin/python" ]; then "$PYTHON_BIN" -m venv "$VENV_DIR"; fi
source "$VENV_DIR/bin/activate"
python -m pip install -r requirements.txt
python scripts/build_macos.py --skip-install
