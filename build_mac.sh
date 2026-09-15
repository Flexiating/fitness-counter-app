#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --windowed --name "Workout Tracker" \
  --add-data "app:app" --collect-all mediapipe --collect-all cv2 \
  app/main.py
echo "Created: $ROOT/dist/Workout Tracker.app"
