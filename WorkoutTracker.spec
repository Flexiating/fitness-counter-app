# -*- mode: python ; coding: utf-8 -*-
"""Cross-platform PyInstaller specification for Workout Tracker."""

from __future__ import annotations

import platform
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


ROOT = Path(SPECPATH).resolve()
APP_NAME = "WorkoutTracker"
IS_MACOS = platform.system() == "Darwin"


def package_contents(package: str):
    """Collect dynamic libraries and data required by packages with lazy imports."""
    try:
        return collect_all(package)
    except Exception:
        return [], [], []


datas = [
    (str(ROOT / "theme"), "theme"),
    (str(ROOT / "assets"), "assets"),
    (str(ROOT / "models"), "models"),
    (str(ROOT / "icons"), "icons"),
    (str(ROOT / "app" / "config"), "app/config"),
]
binaries: list[tuple[str, str]] = []
hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "mediapipe.python.solutions.pose",
    "mediapipe.python.solutions.drawing_utils",
    "mediapipe.python.solutions.drawing_styles",
    "mediapipe.modules.pose_landmark",
]

# MediaPipe and OpenCV load data files and native libraries dynamically.
for package_name in ("mediapipe", "cv2", "numpy"):
    package_datas, package_binaries, package_hiddenimports = package_contents(package_name)
    datas.extend(package_datas)
    binaries.extend(package_binaries)
    hiddenimports.extend(package_hiddenimports)

analysis = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
)
pyz = PYZ(analysis.pure)

if IS_MACOS:
    executable = EXE(
        pyz,
        analysis.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=str(ROOT / "icons" / "app.icns"),
    )
    app = BUNDLE(
        executable,
        analysis.binaries,
        analysis.zipfiles,
        analysis.datas,
        name=f"{APP_NAME}.app",
        icon=str(ROOT / "icons" / "app.icns"),
        bundle_identifier="com.flexiating.workouttracker",
        codesign_identity=None,
        entitlements_file=None,
    )
else:
    executable = EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.zipfiles,
        analysis.datas,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=str(ROOT / "icons" / "app.ico"),
    )
