from __future__ import annotations

import json
from pathlib import Path

from app.data.workout import Workout


class WorkoutStorage:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path("data") / "workouts.json"

    def append(self, workout: Workout) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing = json.loads(self.path.read_text()) if self.path.exists() else []
        existing.append(workout.to_dict())
        self.path.write_text(json.dumps(existing, indent=2))
