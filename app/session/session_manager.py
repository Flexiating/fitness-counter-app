from __future__ import annotations

from pathlib import Path

from app.data.json_store import append_record


class SessionManager:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or "data/sessions.json")

    def save(self, data: dict[str, object]) -> None:
        append_record(self.path, data)
