"""Shared, native-platform PyInstaller release helpers."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


APP_NAME = "WorkoutTracker"
ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
SPEC_FILE = ROOT / "WorkoutTracker.spec"


def _run(command: list[str], *, cwd: Path = ROOT) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def _icon_image():
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("Pillow is required to generate release icons.") from exc

    image = Image.new("RGBA", (1024, 1024), "#0b1220")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((32, 32, 992, 992), radius=210, fill="#0f172a", outline="#22c55e", width=24)
    draw.line(((190, 545), (335, 545), (420, 335), (550, 700), (650, 445), (835, 445)),
              fill="#3b82f6", width=76, joint="curve")
    return image


def ensure_windows_icon() -> Path:
    icon = ROOT / "icons" / "app.ico"
    if icon.exists():
        return icon
    icon.parent.mkdir(parents=True, exist_ok=True)
    image = _icon_image()
    image.save(icon, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return icon


def ensure_macos_icon() -> Path:
    icon = ROOT / "icons" / "app.icns"
    if icon.exists():
        return icon
    if shutil.which("iconutil") is None:
        raise RuntimeError("macOS iconutil is required to create app.icns.")
    iconset = ROOT / "icons" / f"{APP_NAME}.iconset"
    shutil.rmtree(iconset, ignore_errors=True)
    iconset.mkdir(parents=True)
    image = _icon_image()
    sizes = ((16, 1), (16, 2), (32, 1), (32, 2), (128, 1), (128, 2), (256, 1), (256, 2), (512, 1), (512, 2))
    for base_size, scale in sizes:
        pixels = base_size * scale
        suffix = "@2x" if scale == 2 else ""
        output = iconset / f"icon_{base_size}x{base_size}{suffix}.png"
        image.resize((pixels, pixels)).save(output)
    _run(["iconutil", "-c", "icns", str(iconset), "-o", str(icon)])
    shutil.rmtree(iconset)
    return icon


def _install_dependencies(python: str) -> None:
    _run([python, "-m", "pip", "install", "--upgrade", "pip"])
    _run([python, "-m", "pip", "install", "-r", str(REQUIREMENTS)])


def _run_tests(python: str) -> None:
    _run([python, "-m", "pytest", "-q"])


def _clear_build_outputs() -> None:
    for path in (ROOT / "build", ROOT / "dist"):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        (path / ".gitkeep").touch()


def _copy_release(system: str) -> Path:
    if system == "Windows":
        source = ROOT / "dist" / f"{APP_NAME}.exe"
        target_dir = ROOT / "release" / "windows"
        target = target_dir / f"{APP_NAME}.exe"
        target_dir.mkdir(parents=True, exist_ok=True)
        if not source.is_file():
            raise FileNotFoundError(f"PyInstaller did not create {source}")
        shutil.copy2(source, target)
        return target

    source = ROOT / "dist" / f"{APP_NAME}.app"
    target_dir = ROOT / "release" / "macos"
    target = target_dir / f"{APP_NAME}.app"
    if not source.is_dir():
        raise FileNotFoundError(f"PyInstaller did not create {source}")
    if target.exists():
        shutil.rmtree(target)
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, symlinks=True)
    return target


def build_release(expected_system: str | None = None, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a native Workout Tracker release.")
    parser.add_argument("--skip-install", action="store_true", help="Use already installed dependencies.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip the pre-build test suite.")
    parser.add_argument("--target-arch", choices=("x86_64", "arm64", "universal2"),
                        help="macOS architecture; use a matching Python/PyInstaller environment.")
    args = parser.parse_args(argv)
    system = platform.system()
    if system not in {"Windows", "Darwin"}:
        print(f"Unsupported build host: {system}. Build natively on Windows or macOS.")
        return 2
    if expected_system and system != expected_system:
        print(f"This script must run on {expected_system}; detected {system}.")
        return 2
    if args.target_arch and system != "Darwin":
        print("--target-arch is available only for macOS builds.")
        return 2

    python = sys.executable
    if not args.skip_install:
        _install_dependencies(python)
    if not args.skip_tests:
        _run_tests(python)
    if system == "Windows":
        ensure_windows_icon()
    else:
        ensure_macos_icon()

    _clear_build_outputs()
    command = [python, "-m", "PyInstaller", "--noconfirm", "--clean", str(SPEC_FILE)]
    if args.target_arch:
        command.extend(["--target-architecture", args.target_arch])
    _run(command)
    release = _copy_release(system)
    print(f"Release created: {release}")
    return 0
