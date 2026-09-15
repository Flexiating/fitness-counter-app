from time import monotonic

from PySide6.QtCore import QObject, QTimer, Signal

from app.timer.session_timer import TimerState


class TimerController(QObject):
    changed = Signal(str, str)
    finished = Signal(float)

    def __init__(self) -> None:
        super().__init__()
        self.mode = "stopwatch"
        self.countdown = 60.0
        self.state = TimerState.READY
        self.elapsed = 0.0
        self._started: float | None = None
        self.tick = QTimer(self)
        self.tick.setInterval(100)
        self.tick.timeout.connect(self._update)

    def configure(self, mode: str, seconds: int) -> None:
        if mode not in {"stopwatch", "countdown"}:
            raise ValueError(f"Unsupported timer mode: {mode}")
        if seconds <= 0:
            raise ValueError("Timer duration must be positive")
        self.mode, self.countdown = mode, float(seconds)
        self.reset()

    def start_on_rep(self) -> None:
        if self.state is TimerState.READY:
            self.state = TimerState.RUNNING
            self._started = monotonic()
            self.tick.start()
            self._emit()

    def pause(self) -> None:
        if self.state is TimerState.RUNNING and self._started is not None:
            self.elapsed += monotonic() - self._started
            self._started = None
            self.state = TimerState.PAUSED
            self.tick.stop()
            self._emit()

    def resume(self) -> None:
        if self.state is TimerState.PAUSED:
            self._started = monotonic()
            self.state = TimerState.RUNNING
            self.tick.start()
            self._emit()

    def reset(self) -> None:
        self.tick.stop()
        self.state = TimerState.READY
        self.elapsed = 0.0
        self._started = None
        self._emit()

    @property
    def elapsed_seconds(self) -> float:
        running = monotonic() - self._started if self.state is TimerState.RUNNING and self._started is not None else 0.0
        return self.elapsed + running

    def _update(self) -> None:
        if self.state is not TimerState.RUNNING or self._started is None:
            return
        total = self.elapsed + (monotonic() - self._started)
        if self.mode == "countdown" and total >= self.countdown:
            self.elapsed = self.countdown
            self._started = None
            self.tick.stop()
            self.state = TimerState.FINISHED
            self._emit()
            self.finished.emit(self.elapsed)
            return
        self._emit()

    def _emit(self) -> None:
        total = self.elapsed_seconds
        value = max(0.0, self.countdown - total) if self.mode == "countdown" else total
        self.changed.emit(self.state.value, f"{int(value)//60:02}:{int(value)%60:02}")
