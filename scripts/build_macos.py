"""Build release/macos/WorkoutTracker.app on a macOS build host."""

from build_support import build_release


if __name__ == "__main__":
    raise SystemExit(build_release("Darwin"))
