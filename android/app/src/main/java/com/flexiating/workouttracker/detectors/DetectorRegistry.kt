package com.flexiating.workouttracker.detectors

import com.flexiating.workouttracker.model.ExerciseType
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DetectorRegistry @Inject constructor(
    pushUp: PushUpDetector,
    crunch: CrunchDetector
) {
    private val detectors: Map<ExerciseType, BaseExerciseDetector> = listOf(pushUp, crunch).associateBy { it.type }
    private var selected = ExerciseType.PUSH_UP

    @Synchronized fun select(type: ExerciseType): BaseExerciseDetector {
        if (selected != type) {
            detectors.values.forEach { it.reset() }
            selected = type
        }
        return requireNotNull(detectors[type])
    }

    @Synchronized fun current(): BaseExerciseDetector = requireNotNull(detectors[selected])
    @Synchronized fun resetCurrent() = current().reset()
}
