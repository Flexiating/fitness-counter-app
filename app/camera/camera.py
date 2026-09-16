from __future__ import annotations

import platform
from typing import Any

from app.config.settings import SETTINGS
from app.utils.logger import get_logger

log = get_logger(__name__)


class Camera:
    def __init__(self, index: int | None = None) -> None:
        self.index, self._capture = SETTINGS.camera_index if index is None else index, None

    def open(self) -> None:
        import cv2

        self._capture = cv2.VideoCapture(self.index)
        if not self._capture.isOpened():
            self.release()
            hint = " Check that it is connected and camera permission is allowed."
            if platform.system() == "Darwin":
                hint = " Allow Python (or your terminal) in System Settings → Privacy & Security → Camera, then restart the app."
            raise RuntimeError("Could not open camera." + hint)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, SETTINGS.camera_width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, SETTINGS.camera_height)
        self._capture.set(cv2.CAP_PROP_FPS, SETTINGS.target_fps)
        self._capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        log.info("Camera %s initialized", self.index)

    def read(self) -> Any | None:
        if self._capture is None:
            return None
        ok, frame = self._capture.read()
        return frame if ok else None

    def release(self) -> None:
        if self._capture is not None:
            try:
                self._capture.release()
            finally:
                self._capture = None
