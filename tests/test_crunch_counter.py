from app.exercise.crunch_counter import CrunchCounter


def angles(value): return {"Left hip": value, "Right hip": value}
def coords(): return {"nose": (.1, .1), "left_shoulder": (.2, .5), "left_hip": (.5, .5), "left_knee": (.8, .5)}
def visible(): return {key: 1.0 for key in coords()}


def test_ten_slow_crunches_count() -> None:
    counter = CrunchCounter(); timestamp = 0.0
    for _ in range(10):
        counter.update(angles(160), coords(), visible(), timestamp); timestamp += .3
        counter.update(angles(100), coords(), visible(), timestamp); timestamp += .5
        result = counter.update(angles(160), coords(), visible(), timestamp); timestamp += .3
    assert result.count == 10


def test_partial_and_standing_crunches_rejected() -> None:
    counter = CrunchCounter()
    assert counter.update(angles(135), coords(), visible(), 0).count == 0
    standing = coords(); standing["left_hip"] = (.2, .9)
    assert not counter.update(angles(160), standing, visible(), 1).posture_valid
