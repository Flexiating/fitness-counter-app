package com.flexiating.workouttracker.detectors

import com.flexiating.workouttracker.model.*
import com.flexiating.workouttracker.utils.ExponentialSmoother
import com.flexiating.workouttracker.utils.PoseGeometry
import com.flexiating.workouttracker.utils.TransitionGate
import javax.inject.Inject

class PushUpDetector @Inject constructor() : StatefulExerciseDetector(ExerciseType.PUSH_UP) {
    private var phase = ExercisePhase.WAITING
    private val elbowSmoother = ExponentialSmoother()
    private val hipSmoother = ExponentialSmoother()
    private val gate = TransitionGate(180)
    private var downStartedMs = 0L

    override fun process(frame: PoseFrame): DetectorResult {
        val required = intArrayOf(11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28)
        val tracking = frame.averageVisibility(required)
        if (!visible(frame, *required)) return result(false, tracking, "show_full_body_arms", "low_visibility")

        val leftElbow = PoseGeometry.angle(frame.landmark(11)!!, frame.landmark(13)!!, frame.landmark(15)!!)
        val rightElbow = PoseGeometry.angle(frame.landmark(12)!!, frame.landmark(14)!!, frame.landmark(16)!!)
        val leftHip = PoseGeometry.angle(frame.landmark(11)!!, frame.landmark(23)!!, frame.landmark(25)!!)
        val rightHip = PoseGeometry.angle(frame.landmark(12)!!, frame.landmark(24)!!, frame.landmark(26)!!)
        val leftKnee = PoseGeometry.angle(frame.landmark(23)!!, frame.landmark(25)!!, frame.landmark(27)!!)
        val rightKnee = PoseGeometry.angle(frame.landmark(24)!!, frame.landmark(26)!!, frame.landmark(28)!!)
        val elbow = elbowSmoother.update((leftElbow + rightElbow) / 2f)
        val hip = hipSmoother.update((leftHip + rightHip) / 2f)
        val knee = (leftKnee + rightKnee) / 2f
        val shoulder = PoseGeometry.midpoint(frame.landmark(11)!!, frame.landmark(12)!!)
        val ankle = PoseGeometry.midpoint(frame.landmark(27)!!, frame.landmark(28)!!)
        val horizontal = PoseGeometry.bodyHorizontalDeviation(shoulder, ankle)
        val postureValid = hip >= 145f && knee >= 145f && horizontal <= 38f
        val rejection = when {
            horizontal > 38f -> "pushup_position"
            hip < 145f -> "hips_aligned"
            knee < 145f -> "straighten_legs"
            else -> ""
        }

        var rep = false
        if (!postureValid) {
            phase = ExercisePhase.WAITING
            gate.clear()
        } else when (phase) {
            ExercisePhase.WAITING -> if (elbow >= 150f && gate.accepts("ready", frame.timestampMs)) {
                phase = ExercisePhase.READY; lastTransitionMs = frame.timestampMs; gate.clear()
            }
            ExercisePhase.READY, ExercisePhase.UP -> if (elbow <= 85f && gate.accepts("down", frame.timestampMs)) {
                phase = ExercisePhase.DOWN; downStartedMs = frame.timestampMs; lastTransitionMs = frame.timestampMs; gate.clear()
            }
            ExercisePhase.DOWN -> if (elbow >= 150f && gate.accepts("up", frame.timestampMs)) {
                phase = ExercisePhase.UP
                if (frame.timestampMs - downStartedMs >= 300L) { count++; rep = true; lastRepMs = frame.timestampMs }
                lastTransitionMs = frame.timestampMs; gate.clear()
            }
        }
        val score = ((PoseGeometry.normalizedCloseness(hip, 175f, 40f) * 0.55f) +
            (PoseGeometry.normalizedCloseness(knee, 175f, 35f) * 0.25f) +
            ((100f - horizontal * 2f).coerceAtLeast(0f) * 0.20f)).toInt().coerceIn(0, 100)
        return DetectorResult(type, count, phase, postureValid, score, tracking,
            if (postureValid) if (phase == ExercisePhase.DOWN) "push_back_up" else "lower_chest" else rejection,
            mapOf("Left elbow" to leftElbow, "Right elbow" to rightElbow, "Hip" to hip, "Knee" to knee),
            rejection, rep, detectorName = javaClass.simpleName)
    }

    private fun result(valid: Boolean, tracking: Float, feedback: String, reason: String) = DetectorResult(
        type, count, ExercisePhase.WAITING, valid, 0, tracking, feedback,
        rejectionReason = reason, detectorName = javaClass.simpleName
    )

    override fun resetDetector() {
        phase = ExercisePhase.WAITING; downStartedMs = 0L; elbowSmoother.reset(); hipSmoother.reset(); gate.clear()
    }
}
