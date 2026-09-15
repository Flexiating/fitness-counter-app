package com.flexiating.workouttracker.detectors

import com.flexiating.workouttracker.model.DetectorResult
import com.flexiating.workouttracker.model.ExerciseType
import com.flexiating.workouttracker.model.PoseFrame

interface BaseExerciseDetector {
    val type: ExerciseType
    fun process(frame: PoseFrame): DetectorResult
    fun reset()
}

abstract class StatefulExerciseDetector(
    final override val type: ExerciseType,
    protected val visibilityThreshold: Float = 0.55f
) : BaseExerciseDetector {
    protected var count = 0
    protected var lastTransitionMs = 0L
    protected var lastRepMs = 0L

    protected fun visible(frame: PoseFrame, vararg indices: Int): Boolean =
        frame.personDetected && indices.all { (frame.landmark(it)?.visibility ?: 0f) >= visibilityThreshold }

    protected fun confidence(frame: PoseFrame, vararg indices: Int): Float =
        frame.averageVisibility(indices)

    override fun reset() {
        count = 0
        lastTransitionMs = 0L
        lastRepMs = 0L
        resetDetector()
    }

    protected abstract fun resetDetector()
}

