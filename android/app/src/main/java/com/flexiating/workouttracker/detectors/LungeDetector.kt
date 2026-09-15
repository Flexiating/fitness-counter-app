package com.flexiating.workouttracker.detectors

import com.flexiating.workouttracker.model.*
import com.flexiating.workouttracker.utils.ExponentialSmoother
import com.flexiating.workouttracker.utils.PoseGeometry
import com.flexiating.workouttracker.utils.TransitionGate
import javax.inject.Inject

class LungeDetector @Inject constructor() : StatefulExerciseDetector(ExerciseType.LUNGE) {
    private var phase = ExercisePhase.WAITING
    private val kneeSmoother = ExponentialSmoother()
    private val gate = TransitionGate()
    private var downAt = 0L

    override fun process(frame: PoseFrame): DetectorResult {
        val ids = intArrayOf(23, 24, 25, 26, 27, 28)
        val tracking = frame.averageVisibility(ids)
        if (!visible(frame, *ids)) return base(tracking, "Show both legs", "Low leg visibility")
        val left = PoseGeometry.angle(frame.landmark(23)!!, frame.landmark(25)!!, frame.landmark(27)!!)
        val right = PoseGeometry.angle(frame.landmark(24)!!, frame.landmark(26)!!, frame.landmark(28)!!)
        val front = kneeSmoother.update(minOf(left, right))
        val rear = maxOf(left, right)
        val stance = kotlin.math.abs(frame.landmark(27)!!.x - frame.landmark(28)!!.x) > 0.12f
        var rep = false
        if (!stance) { phase = ExercisePhase.WAITING; gate.clear() }
        else when (phase) {
            ExercisePhase.WAITING -> if (front > 150f && gate.accepts("ready", frame.timestampMs)) { phase = ExercisePhase.READY; gate.clear() }
            ExercisePhase.READY, ExercisePhase.UP -> if (front < 105f && gate.accepts("down", frame.timestampMs)) { phase = ExercisePhase.DOWN; downAt = frame.timestampMs; gate.clear() }
            ExercisePhase.DOWN -> if (front > 150f && gate.accepts("up", frame.timestampMs)) { phase = ExercisePhase.UP; if (frame.timestampMs - downAt > 350) { count++; rep = true }; gate.clear() }
            else -> Unit
        }
        return DetectorResult(type, count, phase, stance, PoseGeometry.normalizedCloseness(front, if (phase == ExercisePhase.DOWN) 90f else 170f, 55f), tracking,
            if (stance) "Keep your front knee over your ankle" else "Step into a split stance",
            mapOf("Left knee" to left, "Right knee" to right, "Rear knee" to rear), if (stance) "" else "Stance is too narrow", rep, detectorName = javaClass.simpleName)
    }

    private fun base(tracking: Float, feedback: String, reason: String) = DetectorResult(type, count, ExercisePhase.WAITING, false, 0, tracking, feedback, rejectionReason = reason, detectorName = javaClass.simpleName)
    override fun resetDetector() { phase = ExercisePhase.WAITING; downAt = 0; kneeSmoother.reset(); gate.clear() }
}

