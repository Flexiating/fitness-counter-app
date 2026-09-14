from app.processing.repetition_counter import MovementState, RepetitionCounter


def update(counter, state, frames=3):
    for _ in range(frames): counter.update(state)


def test_complete_cycle_counts_once() -> None:
    counter = RepetitionCounter(3)
    update(counter, MovementState.EXTENDED); update(counter, MovementState.CONTRACTED); update(counter, MovementState.EXTENDED)
    assert counter.repetitions == 1


def test_incomplete_and_noisy_movement_do_not_count() -> None:
    counter = RepetitionCounter(3)
    update(counter, MovementState.EXTENDED); update(counter, MovementState.CONTRACTED)
    assert counter.repetitions == 0
    counter.update(MovementState.EXTENDED); counter.update(MovementState.CONTRACTED); counter.update(MovementState.EXTENDED)
    assert counter.repetitions == 0
