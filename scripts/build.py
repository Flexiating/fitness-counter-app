"""Build a release for the current supported platform automatically."""

from build_support import build_release


if __name__ == "__main__":
    raise SystemExit(build_release())
