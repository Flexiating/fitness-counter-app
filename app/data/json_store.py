"""Small, thread-safe JSON persistence helpers."""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Mapping


_WRITE_LOCK = Lock()


def append_record(path: Path, record: Mapping[str, object]) -> None:
    """Atomically append a mapping to a JSON list stored at *path*."""
    with _WRITE_LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        rows: list[object] = []
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}") from exc
            if not isinstance(loaded, list):
                raise ValueError(f"Expected a JSON list in {path}")
            rows = loaded
        rows.append(dict(record))
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        temporary.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
