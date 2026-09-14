"""Reusable joint-angle calculations for pose-driven exercises."""

from __future__ import annotations

from math import acos, degrees

from app.pose.pose_landmarks import Landmark, LandmarkName, PoseLandmarks


JointTriple = tuple[LandmarkName, LandmarkName, LandmarkName]

JOINT_ANGLE_TRIPLES: dict[str, JointTriple] = {
    "Left elbow": (LandmarkName.LEFT_SHOULDER, LandmarkName.LEFT_ELBOW, LandmarkName.LEFT_WRIST),
    "Right elbow": (LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_ELBOW, LandmarkName.RIGHT_WRIST),
    "Left shoulder": (LandmarkName.LEFT_ELBOW, LandmarkName.LEFT_SHOULDER, LandmarkName.LEFT_HIP),
    "Right shoulder": (LandmarkName.RIGHT_ELBOW, LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_HIP),
    "Left hip": (LandmarkName.LEFT_SHOULDER, LandmarkName.LEFT_HIP, LandmarkName.LEFT_KNEE),
    "Right hip": (LandmarkName.RIGHT_SHOULDER, LandmarkName.RIGHT_HIP, LandmarkName.RIGHT_KNEE),
    "Left knee": (LandmarkName.LEFT_HIP, LandmarkName.LEFT_KNEE, LandmarkName.LEFT_ANKLE),
    "Right knee": (LandmarkName.RIGHT_HIP, LandmarkName.RIGHT_KNEE, LandmarkName.RIGHT_ANKLE),
}


def angle(a: Landmark, b: Landmark, c: Landmark) -> float:
    """Return the angle ABC in degrees, constrained to the inclusive 0–180 range."""
    ab = (a.x - b.x, a.y - b.y)
    cb = (c.x - b.x, c.y - b.y)
    magnitude_ab = (ab[0] ** 2 + ab[1] ** 2) ** 0.5
    magnitude_cb = (cb[0] ** 2 + cb[1] ** 2) ** 0.5
    if magnitude_ab == 0 or magnitude_cb == 0:
        return 0.0
    cosine = max(-1.0, min(1.0, (ab[0] * cb[0] + ab[1] * cb[1]) / (magnitude_ab * magnitude_cb)))
    return degrees(acos(cosine))


def calculate_joint_angles(landmarks: PoseLandmarks) -> dict[str, float]:
    """Calculate every supported bilateral joint angle present in a pose."""
    return {
        name: angle(*(landmarks[point] for point in points))
        for name, points in JOINT_ANGLE_TRIPLES.items()
        if all(point in landmarks for point in points)
    }
