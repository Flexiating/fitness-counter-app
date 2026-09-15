from app.utils.paths import resource_path


def load_theme(name: str = "dark") -> str:
    return resource_path("theme", f"{name}.qss").read_text(encoding="utf-8")
