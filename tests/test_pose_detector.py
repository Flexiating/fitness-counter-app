import pytest

from app.models.pose_model import PoseModel
from app.models.mediapipe_model import MediaPipePoseModel
from app.pose.pose_detector import PoseDetector
from app.pose.pose_landmarks import Landmark, LandmarkName


class FakePoseModel(PoseModel):
    def __init__(self) -> None:
        self.loaded = False
        self.closed = False

    def load(self) -> None:
        self.loaded = True

    def predict(self, frame: object):
        assert self.loaded
        return {LandmarkName.NOSE: Landmark(.5, .2)} if frame == "person" else {}

    def close(self) -> None:
        self.closed = True


def test_pose_detector_standardizes_detection_lifecycle() -> None:
    model = FakePoseModel()
    detector = PoseDetector(model)
    with pytest.raises(RuntimeError, match="not been started"):
        detector.detect("person")
    detector.start()
    assert detector.detect("person")[LandmarkName.NOSE] == Landmark(.5, .2)
    assert detector.detect("empty") == {}
    detector.close()
    assert model.closed


def test_mediapipe_mapping_covers_all_pose_landmarks() -> None:
    assert len(MediaPipePoseModel._mapping) == 33
    assert set(MediaPipePoseModel._mapping) == set(LandmarkName)
