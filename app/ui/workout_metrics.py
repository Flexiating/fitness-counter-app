from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkoutSnapshot:
    repetitions: int
    duration: float
    current_rep_seconds: float | None
    average_rep_seconds: float | None
    fastest_rep: float | None
    slowest_rep: float | None
    reps_per_minute: float
    accuracy: float
    form_score: float
    best_streak: int


class LiveWorkoutMetrics:
    """Small, UI-facing session accumulator with no camera dependencies."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.repetitions = 0
        self._rep_times: list[float] = []
        self._form_score = 0.0
        self._quality_samples = 0
        self._valid_samples = 0
        self._current_streak = 0
        self.best_streak = 0

    def update_quality(self, form_score: float, posture_valid: bool) -> None:
        score = max(0.0, min(100.0, form_score))
        self._form_score = score if self._quality_samples == 0 else self._form_score * 0.82 + score * 0.18
        self._quality_samples += 1
        if posture_valid:
            self._valid_samples += 1

    def record_repetitions(self, amount: int, timestamp: float) -> None:
        for _ in range(max(0, amount)):
            self.repetitions += 1
            self._rep_times.append(timestamp)
            if self._form_score >= 75:
                self._current_streak += 1
                self.best_streak = max(self.best_streak, self._current_streak)
            else:
                self._current_streak = 0

    def snapshot(self, duration: float) -> WorkoutSnapshot:
        intervals = [right - left for left, right in zip(self._rep_times, self._rep_times[1:])]
        current = intervals[-1] if intervals else None
        average = sum(intervals) / len(intervals) if intervals else None
        rpm = self.repetitions * 60.0 / duration if duration > 0 else 0.0
        accuracy = 100.0 * self._valid_samples / self._quality_samples if self._quality_samples else 0.0
        return WorkoutSnapshot(
            repetitions=self.repetitions,
            duration=max(0.0, duration),
            current_rep_seconds=current,
            average_rep_seconds=average,
            fastest_rep=min(intervals) if intervals else None,
            slowest_rep=max(intervals) if intervals else None,
            reps_per_minute=rpm,
            accuracy=accuracy,
            form_score=self._form_score,
            best_streak=self.best_streak,
        )


def speed_label(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    pace = "Nhanh" if seconds < 1.2 else "Chậm" if seconds > 3.0 else "Bình thường"
    return f"{seconds:.1f}s · {pace}"
