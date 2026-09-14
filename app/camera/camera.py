from __future__ import annotations

import platform
from typing import Any

import cv2

from app.config.settings import SETTINGS
from app.utils.logger import get_logger

log = get_logger(__name__)


class Camera:
    def __init__(self, index: int = 0) -> None:
        self.index, self._capture = index, None

    def open(self) -> None:
        self._capture = cv2.VideoCapture(self.index)
        if not self._capture.isOpened():
            self.release()
            hint = " Check that it is connected and camera permission is allowed."
            if platform.system() == "Darwin":
                hint = " Allow Python (or your terminal) in System Settings → Privacy & Security → Camera, then restart the app."
            raise RuntimeError("Could not open camera." + hint)
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, SETTINGS.camera_width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, SETTINGS.camera_height)
        log.info("Camera %s initialized", self.index)

    def read(self) -> Any | None:
        if self._capture is None:
            return None
        ok, frame = self._capture.read()
        return frame if ok else None

    def release(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
