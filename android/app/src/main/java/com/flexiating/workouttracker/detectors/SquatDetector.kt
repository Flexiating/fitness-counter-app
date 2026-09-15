package com.flexiating.workouttracker.detectors

import com.flexiating.workouttracker.model.*
import com.flexiating.workouttracker.utils.ExponentialSmoother
import com.flexiating.workouttracker.utils.PoseGeometry
import com.flexiating.workouttracker.utils.TransitionGate
import javax.inject.Inject

class SquatDetector @Inject constructor() : StatefulExerciseDetector(ExerciseType.SQUAT) {
    private var phase = ExercisePhase.WAITING
    private val knees = ExponentialSmoother()
    private val gate = TransitionGate()
    private var downAt = 0L

    override fun process(frame: PoseFrame): DetectorResult {
        val ids = intArrayOf(11, 12, 23, 24, 25, 26, 27, 28)
        val tracking = frame.averageVisibility(ids)
        if (!visible(frame, *ids)) return base(tracking, "Show your full body", "Low visibility")
        val left = PoseGeometry.angle(frame.landmark(23)!!, frame.landmark(25)!!, frame.landmark(27)!!)
        val right = PoseGeometry.angle(frame.landmark(24)!!, frame.landmark(26)!!, frame.landmark(28)!!)
        val knee = knees.update((left + right) / 2f)
        val hip = (PoseGeometry.angle(frame.landmark(11)!!, frame.landmark(23)!!, frame.landmark(25)!!) +
            PoseGeometry.angle(frame.landmark(12)!!, frame.landmark(24)!!, frame.landmark(26)!!)) / 2f
        val upright = PoseGeometry.midpoint(frame.landmark(11)!!, frame.landmark(12)!!).y <
            PoseGeometry.midpoint(frame.landmark(23)!!, frame.landmark(24)!!).y
        var rep = false
        if (!upright) { phase = ExercisePhase.WAITING; gate.clear() }
        else when (phase) {
            ExercisePhase.WAITING -> if (knee > 155f && gate.accepts("ready", frame.timestampMs)) { phase = ExercisePhase.READY; gate.clear() }
            ExercisePhase.READY, ExercisePhase.UP -> if (knee < 105f && hip < 120f && gate.accepts("down", frame.timestampMs)) { phase = ExercisePhase.DOWN; downAt = frame.timestampMs; gate.clear() }
            ExercisePhase.DOWN -> if (knee > 155f && gate.accepts("up", frame.timestampMs)) { phase = ExercisePhase.UP; if (frame.timestampMs - downAt > 350) { count++; rep = true }; gate.clear() }
            else -> Unit
        }
        val valid = upright
        return DetectorResult(type, count, phase, valid, PoseGeometry.normalizedCloseness(knee, if (phase == ExercisePhase.DOWN) 90f else 175f, 55f), tracking,
            if (phase == ExercisePhase.DOWN) "Drive through your heels" else "Keep knees aligned with toes",
            mapOf("Left knee" to left, "Right knee" to right, "Hip" to hip), repCompleted = rep, detectorName = javaClass.simpleName)
    }

    private fun base(tracking: Float, feedback: String, reason: String) = DetectorResult(type, count, ExercisePhase.WAITING, false, 0, tracking, feedback, rejectionReason = reason, detectorName = javaClass.simpleName)
    override fun resetDetector() { phase = ExercisePhase.WAITING; downAt = 0; knees.reset(); gate.clear() }
}

