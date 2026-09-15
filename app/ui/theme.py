from pathlib import Path


THEME_DIR = Path(__file__).parents[2] / "theme"


def load_theme(name: str = "dark") -> str:
    return (THEME_DIR / f"{name}.qss").read_text()
