from math import sqrt
from typing import Protocol


class PointLike(Protocol):
    x: float
    y: float


def distance(a: PointLike, b: PointLike) -> float:
    return sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
