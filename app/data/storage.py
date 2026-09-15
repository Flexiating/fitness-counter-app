from __future__ import annotations

from pathlib import Path

from app.data.json_store import append_record
from app.data.workout import Workout


class WorkoutStorage:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path("data") / "workouts.json"

    def append(self, workout: Workout) -> None:
        append_record(self.path, workout.to_dict())
