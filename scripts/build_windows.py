"""Build release/windows/WorkoutTracker.exe on a Windows build host."""

from build_support import build_release


if __name__ == "__main__":
    raise SystemExit(build_release("Windows"))
