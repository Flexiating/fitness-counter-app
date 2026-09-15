"""Safely remove generated PyInstaller output and Python cache files."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove generated build artifacts.")
    parser.add_argument("--release", action="store_true", help="Also remove release/ output.")
    args = parser.parse_args()

    targets = [ROOT / "build", ROOT / "dist", ROOT / ".pytest_cache", ROOT / ".coverage", ROOT / "htmlcov"]
    if args.release:
        targets.append(ROOT / "release")
    for target in targets:
        remove_path(target)
    for name in ("build", "dist"):
        marker_directory = ROOT / name
        marker_directory.mkdir(parents=True, exist_ok=True)
        (marker_directory / ".gitkeep").touch()
    if args.release:
        marker_directory = ROOT / "release"
        marker_directory.mkdir(parents=True, exist_ok=True)
        (marker_directory / ".gitkeep").touch()
    for cache_dir in ROOT.rglob("__pycache__"):
        if ".venv" not in cache_dir.parts:
            remove_path(cache_dir)
    for temporary in ROOT.rglob("*.pyc"):
        if ".venv" not in temporary.parts:
            remove_path(temporary)
    print("Generated build artifacts removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
