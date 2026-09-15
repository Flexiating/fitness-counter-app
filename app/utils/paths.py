"""Portable paths for development and PyInstaller releases."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "WorkoutTracker"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resource_path(*parts: str | Path) -> Path:
    """Return a read-only bundled resource path in development or PyInstaller."""
    bundle_root = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    return bundle_root.joinpath(*(str(part) for part in parts))


def app_data_dir() -> Path:
    """Return the platform-appropriate, writable application-data directory."""
    override = os.environ.get("WORKOUT_TRACKER_DATA_DIR")
    if override:
        base = Path(override)
    elif sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def app_data_path(*parts: str | Path) -> Path:
    """Return a writable file location below the application-data directory."""
    path = app_data_dir().joinpath(*(str(part) for part in parts))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
