package com.flexiating.workouttracker.detectors

import com.flexiating.workouttracker.model.*
import com.flexiating.workouttracker.utils.PoseGeometry
import javax.inject.Inject

class PlankDetector @Inject constructor() : StatefulExerciseDetector(ExerciseType.PLANK) {
    private var phase = ExercisePhase.WAITING
    private var holdStarted = 0L

    override fun process(frame: PoseFrame): DetectorResult {
        val ids = intArrayOf(11, 12, 23, 24, 25, 26, 27, 28)
        val tracking = frame.averageVisibility(ids)
        if (!visible(frame, *ids)) { phase = ExercisePhase.WAITING; holdStarted = 0; return base(tracking, "Show your full body", "Low visibility") }
        val shoulder = PoseGeometry.midpoint(frame.landmark(11)!!, frame.landmark(12)!!)
        val hipPoint = PoseGeometry.midpoint(frame.landmark(23)!!, frame.landmark(24)!!)
        val kneePoint = PoseGeometry.midpoint(frame.landmark(25)!!, frame.landmark(26)!!)
        val ankle = PoseGeometry.midpoint(frame.landmark(27)!!, frame.landmark(28)!!)
        val hipAngle = PoseGeometry.angle(shoulder, hipPoint, kneePoint)
        val horizontal = PoseGeometry.bodyHorizontalDeviation(shoulder, ankle)
        val valid = hipAngle > 155f && horizontal < 35f
        if (valid) {
            if (holdStarted == 0L) holdStarted = frame.timestampMs
            phase = ExercisePhase.HOLDING
        } else { holdStarted = 0; phase = ExercisePhase.WAITING }
        val seconds = if (holdStarted == 0L) 0 else ((frame.timestampMs - holdStarted) / 1000).toInt()
        return DetectorResult(type, 0, phase, valid,
            ((PoseGeometry.normalizedCloseness(hipAngle, 175f, 35f) + (100f - horizontal * 2f).coerceIn(0f, 100f)) / 2f).toInt(),
            tracking, if (valid) "Hold steady and breathe" else "Align shoulders, hips and ankles",
            mapOf("Hip" to hipAngle, "Body tilt" to horizontal), if (valid) "" else "Body is not straight", holdSeconds = seconds, detectorName = javaClass.simpleName)
    }

    private fun base(tracking: Float, feedback: String, reason: String) = DetectorResult(type, 0, ExercisePhase.WAITING, false, 0, tracking, feedback, rejectionReason = reason, detectorName = javaClass.simpleName)
    override fun resetDetector() { phase = ExercisePhase.WAITING; holdStarted = 0 }
}

