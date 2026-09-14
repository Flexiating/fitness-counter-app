import numpy as np

from app.exercises.exercise_manager import ExerciseManager
from app.pose.pose_landmarks import Landmark, LandmarkName
from app.pose.angles import calculate_joint_angles
from app.ui.main_window import CameraWorker


def up_pose():
    return {
        LandmarkName.LEFT_SHOULDER: Landmark(.2, .5), LandmarkName.LEFT_ELBOW: Landmark(.5, .5), LandmarkName.LEFT_WRIST: Landmark(.8, .5),
        LandmarkName.RIGHT_SHOULDER: Landmark(.2, .6), LandmarkName.RIGHT_ELBOW: Landmark(.5, .6), LandmarkName.RIGHT_WRIST: Landmark(.8, .6),
        LandmarkName.LEFT_HIP: Landmark(.3, .75), LandmarkName.RIGHT_HIP: Landmark(.3, .8),
        LandmarkName.LEFT_KNEE: Landmark(.4, .9), LandmarkName.RIGHT_KNEE: Landmark(.4, .9),
        LandmarkName.LEFT_ANKLE: Landmark(.45, .98), LandmarkName.RIGHT_ANKLE: Landmark(.45, .98),
    }


def test_camera_worker_reports_no_person_and_processes_pose(monkeypatch) -> None:
    frames = [np.zeros((64, 96, 3), dtype=np.uint8), np.zeros((64, 96, 3), dtype=np.uint8)]

    class FakeCamera:
        def open(self): pass
        def read(self): return frames.pop(0) if frames else None
        def release(self): pass

    class FakePoseDetector:
        def start(self): pass
        def detect(self, _frame): return {} if len(frames) == 1 else up_pose()
        def close(self): pass

    monkeypatch.setattr("app.ui.main_window.Camera", FakeCamera)
    monkeypatch.setattr("app.ui.main_window.PoseDetector", FakePoseDetector)
    worker = CameraWorker(ExerciseManager())
    statuses, images = [], []
    worker.result_ready.connect(lambda _reps, state, status: statuses.append((state, status)))
    worker.frame_ready.connect(images.append)
    worker.run()

    assert ("NO PERSON", "No person detected") in statuses
    assert any(state == "UP" for state, _status in statuses)
    assert len(images) == 2


def test_skeleton_overlay_draws_connections() -> None:
    worker = CameraWorker(ExerciseManager())
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    worker._draw(frame, up_pose(), {})
    assert frame.sum() > 0


def test_pose_debug_metrics_include_requested_joint_types() -> None:
    angles = calculate_joint_angles(up_pose())
    assert {"Left elbow", "Left shoulder", "Left hip", "Left knee"}.issubset(angles)
