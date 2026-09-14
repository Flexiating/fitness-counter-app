from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class Workout:
    exercise: str
    repetitions: int
    started_at: str
    ended_at: str
    duration_seconds: float

    @classmethod
    def create(cls, exercise: str, repetitions: int, start: datetime, end: datetime) -> "Workout":
        return cls(exercise, repetitions, start.isoformat(), end.isoformat(), round((end - start).total_seconds(), 1))

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
