#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# MediaPipe's classic Pose API used by this project supports Python 3.9–3.12.
# Prefer the newest compatible interpreter found on the computer.
PYTHON_BIN=""
for candidate in python3.12 python3.11 python3.10 python3.9; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "Python 3.9–3.12 is required to run Fitness Counter."
    echo "Python 3.14 is not supported by the MediaPipe Pose API used by this version."
    echo "Install Python 3.12 from https://www.python.org/downloads/, then run this file again."
    exit 1
fi

PYTHON_VERSION="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
VENV_DIR=".venv-$PYTHON_VERSION"
if [ ! -x "$VENV_DIR/bin/python" ]; then "$PYTHON_BIN" -m venv "$VENV_DIR"; fi
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m app.main
