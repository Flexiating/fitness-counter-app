from time import monotonic
from PySide6.QtCore import QObject, QTimer, Signal
from app.timer.session_timer import TimerState

class TimerController(QObject):
    changed=Signal(str, str); finished=Signal(float)
    def __init__(self):
        super().__init__(); self.mode="stopwatch"; self.countdown=60.; self.state=TimerState.READY; self.elapsed=0.; self._started=None
        self.tick=QTimer(self); self.tick.setInterval(100); self.tick.timeout.connect(self._update)
    def configure(self, mode, seconds): self.mode,self.countdown=mode,float(seconds); self.reset()
    def start_on_rep(self):
        if self.state is TimerState.READY: self.state=TimerState.RUNNING; self._started=monotonic(); self.tick.start(); self._emit()
    def pause(self):
        if self.state is TimerState.RUNNING: self.elapsed+=monotonic()-self._started; self.state=TimerState.PAUSED; self.tick.stop(); self._emit()
    def resume(self):
        if self.state is TimerState.PAUSED: self._started=monotonic(); self.state=TimerState.RUNNING; self.tick.start(); self._emit()
    def reset(self): self.tick.stop(); self.state=TimerState.READY; self.elapsed=0.; self._started=None; self._emit()
    def _update(self):
        total=self.elapsed+(monotonic()-self._started)
        if self.mode=="countdown" and total>=self.countdown:
            self.elapsed=self.countdown; self.tick.stop(); self.state=TimerState.FINISHED; self._emit(); self.finished.emit(self.elapsed); return
        self._emit()
    def _emit(self):
        total=self.elapsed+(monotonic()-self._started if self.state is TimerState.RUNNING else 0)
        value=max(0,self.countdown-total) if self.mode=="countdown" else total
        self.changed.emit(self.state.value, f"{int(value)//60:02}:{int(value)%60:02}")
