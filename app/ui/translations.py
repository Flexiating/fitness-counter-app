"""JSON-backed runtime localization for the desktop application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from app.utils.paths import resource_path


class LocalizationManager(QObject):
    language_changed = Signal(str)

    def __init__(self, language: str = "en", locale_dir: Path | None = None) -> None:
        super().__init__()
        self.locale_dir = locale_dir or resource_path("locales")
        self._catalogs = {
            code: json.loads((self.locale_dir / f"{code}.json").read_text(encoding="utf-8"))
            for code in ("en", "vi")
        }
        self._language = language if language in self._catalogs else "en"

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        language = language if language in self._catalogs else "en"
        if language != self._language:
            self._language = language
            self.language_changed.emit(language)

    def text(self, key: str, **values: Any) -> str:
        template = self._catalogs[self._language].get(key)
        if template is None:
            template = self._catalogs["en"].get(key, key)
        try:
            return str(template).format(**values)
        except (KeyError, ValueError):
            return str(template)


_manager: LocalizationManager | None = None


def initialize_localization(language: str = "en") -> LocalizationManager:
    global _manager
    _manager = LocalizationManager(language)
    return _manager


def localization() -> LocalizationManager:
    global _manager
    if _manager is None:
        _manager = LocalizationManager()
    return _manager


def tr(key: str, **values: Any) -> str:
    return localization().text(key, **values)


def translate_exercise(name: str) -> str:
    return tr("exercise.push_up" if name in {"Push Up", "Push-up", "push_up", "PUSH_UP"} else "exercise.crunch")


def translate_state(state: str) -> str:
    return tr(f"state.{state.lower().replace(' ', '_')}")


_STATUS_KEYS = {
    "Opening camera": "status.opening_camera",
    "Loading pose detector": "status.loading_detector",
    "Ready": "status.ready",
    "No person detected": "status.no_person",
    "Move into camera view": "status.move_into_view",
    "Move farther from the camera": "status.move_farther",
    "Posture: GOOD": "status.posture_good",
    "Posture: BAD": "status.posture_bad",
    "Movement between thresholds": "status.between_thresholds",
    "Body not visible": "status.body_not_visible",
    "Only one arm detected or body not visible": "status.arm_or_body_missing",
    "Hips too high or too low": "status.hips_alignment",
    "Not in push-up position (standing or walking)": "status.not_pushup_position",
    "Body not visible or tracking lost": "status.tracking_lost",
    "Standing, sitting, walking, or body rotated": "status.wrong_orientation",
    "Partial crunch ignored": "status.partial_crunch",
    "Rep rejected: too fast": "status.too_fast",
    "Camera frame unavailable. Check the camera connection.": "status.camera_frame_error",
    "Camera unavailable. Check the connection and camera permission.": "status.camera_unavailable",
    "Pose model failed to load. Restart the app or reinstall the dependencies.": "status.model_failed",
    "Camera processing stopped unexpectedly. Press Start Camera to retry.": "status.processing_stopped",
    "Details": "status.details",
    "No complete body side detected": "status.body_side_missing",
    "Required joints unavailable": "status.joints_missing",
    "No complete arm and body side detected": "status.arm_side_missing",
    "No sufficiently visible arm and body side": "status.arm_side_missing",
    "Whole body is not inside the frame": "status.full_body_frame",
    "Posture score below safe push-up range": "status.pushup_form_low",
    "Keep your full body inside the frame": "status.full_body_frame",
    "Move slightly farther from the camera": "status.move_farther",
    "Turn sideways to the camera": "status.turn_sideways",
    "Standing, sitting, or walking is not a crunch position": "status.crunch_position",
    "Standing or sitting is not a crunch position": "status.crunch_position",
    "Lift your shoulders higher.": "status.lift_shoulders",
    "Good lift. Lower your shoulders with control.": "status.lower_shoulders",
    "Good crunch.": "status.good_crunch",
    "Move more slowly.": "status.move_slowly",
    "Complete the full range of motion.": "status.full_range",
    "Avoid pulling your neck.": "status.neutral_neck",
    "Keep your lower back on the floor.": "status.lower_back",
    "Lie back fully before starting.": "status.lie_back",
    "Lower your shoulders with control.": "status.lower_shoulders",
    "Ready for the next crunch.": "status.next_crunch",
    "Good torso lift.": "status.good_lift",
}


def translate_status(status: str) -> str:
    translated = status
    for source, key in _STATUS_KEYS.items():
        translated = translated.replace(source, tr(key))
    return translated.replace("Form score", tr("status.form_score"))


def translate_joint(name: str) -> str:
    key = "joint." + name.lower().replace(" ", "_").replace("-", "_")
    value = tr(key)
    return name if value == key else value


def translate_debug(text: str) -> str:
    return translate_status(text)
