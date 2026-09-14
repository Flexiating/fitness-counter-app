from __future__ import annotations

from enum import Enum


class MovementState(str, Enum):
    EXTENDED = "EXTENDED"
    CONTRACTED = "CONTRACTED"


class RepetitionCounter:
    """Counts only a full extended → contracted → extended motion cycle."""
    def __init__(self, minimum_state_frames: int = 3) -> None:
        self.minimum_state_frames = minimum_state_frames
        self.repetitions = 0
        self._stable_state: MovementState | None = None
        self._candidate: MovementState | None = None
        self._candidate_frames = 0
        self._saw_contracted = False

    def update(self, observed: MovementState | None) -> int:
        if observed is None:
            return self.repetitions
        if observed != self._candidate:
            self._candidate, self._candidate_frames = observed, 1
        else:
            self._candidate_frames += 1
        if self._candidate_frames < self.minimum_state_frames or observed == self._stable_state:
            return self.repetitions
        previous, self._stable_state = self._stable_state, observed
        if observed is MovementState.CONTRACTED and previous is MovementState.EXTENDED:
            self._saw_contracted = True
        elif observed is MovementState.EXTENDED and previous is MovementState.CONTRACTED and self._saw_contracted:
            self.repetitions += 1
            self._saw_contracted = False
        return self.repetitions

    def reset(self) -> None:
        self.__init__(self.minimum_state_frames)
