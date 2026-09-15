from __future__ import annotations

from enum import Enum


class CounterState(str, Enum):
    WAITING = "WAITING"
    UP = "UP"
    DOWN = "DOWN"


class BaseCounter:
    def __init__(self, debounce_seconds: float, min_rep_seconds: float) -> None:
        self.debounce_seconds, self.min_rep_seconds = debounce_seconds, min_rep_seconds
        self.reset()

    def reset(self) -> None:
        self.count = 0; self.state = CounterState.WAITING
        self.last_transition_at: float | None = None; self.down_at: float | None = None

    def can_transition(self, timestamp: float) -> bool:
        return self.last_transition_at is None or timestamp - self.last_transition_at >= self.debounce_seconds
