package com.flexiating.workouttracker.detectors

import com.flexiating.workouttracker.model.*
import com.flexiating.workouttracker.utils.ExponentialSmoother
import com.flexiating.workouttracker.utils.PoseGeometry
import com.flexiating.workouttracker.utils.TransitionGate
import javax.inject.Inject
import kotlin.math.abs

class CrunchDetector @Inject constructor() : StatefulExerciseDetector(ExerciseType.CRUNCH) {
    private var phase = ExercisePhase.WAITING
    private val torsoSmoother = ExponentialSmoother(0.3f)
    private val gate = TransitionGate(180)
    private var liftedAt = 0L

    override fun process(frame: PoseFrame): DetectorResult {
        val leftVisibility = frame.averageVisibility(intArrayOf(7, 11, 23, 25))
        val rightVisibility = frame.averageVisibility(intArrayOf(8, 12, 24, 26))
        val left = leftVisibility >= rightVisibility
        val ear = frame.landmark(if (left) 7 else 8)
        val shoulder = frame.landmark(if (left) 11 else 12)
        val hip = frame.landmark(if (left) 23 else 24)
        val knee = frame.landmark(if (left) 25 else 26)
        val tracking = maxOf(leftVisibility, rightVisibility)
        if (listOf(ear, shoulder, hip, knee).any { it == null || it.visibility < visibilityThreshold }) {
            phase = ExercisePhase.WAITING
            return result(tracking, "crunch_sideways", "crunch_landmarks_missing")
        }
        val torsoAngle = torsoSmoother.update(PoseGeometry.angle(shoulder!!, hip!!, knee!!))
        val neckAngle = PoseGeometry.angle(ear!!, shoulder, hip)
        val torsoLength = PoseGeometry.distance(shoulder, hip).coerceAtLeast(0.01f)
        val shoulderToKnee = PoseGeometry.distance(shoulder, knee) / torsoLength
        val hipToKnee = PoseGeometry.distance(hip, knee)
        val lying = torsoAngle >= 132f && shoulderToKnee >= 1.15f
        val curled = torsoAngle <= 112f && shoulderToKnee <= 1.35f
        val standing = abs(shoulder.y - hip.y) > hipToKnee * 0.9f && torsoAngle > 145f
        val rotated = abs(frame.landmark(11)!!.z - frame.landmark(12)!!.z) > 0.28f
        val valid = !standing && !rotated
        val rejection = when {
            standing -> "lie_down"
            rotated -> "avoid_twisting"
            !lying && !curled && phase == ExercisePhase.WAITING -> "extend_torso"
            else -> ""
        }

        var rep = false
        if (!valid) {
            phase = ExercisePhase.WAITING; gate.clear()
        } else when (phase) {
            ExercisePhase.WAITING -> if (lying && gate.accepts("ready", frame.timestampMs)) {
                phase = ExercisePhase.READY; gate.clear(); lastTransitionMs = frame.timestampMs
            }
            ExercisePhase.READY, ExercisePhase.DOWN -> if (curled && gate.accepts("lifted", frame.timestampMs)) {
                phase = ExercisePhase.UP; liftedAt = frame.timestampMs; gate.clear(); lastTransitionMs = frame.timestampMs
            }
            ExercisePhase.UP -> if (lying && gate.accepts("lowered", frame.timestampMs)) {
                phase = ExercisePhase.DOWN
                if (frame.timestampMs - liftedAt >= 300L) { count++; rep = true; lastRepMs = frame.timestampMs }
                gate.clear(); lastTransitionMs = frame.timestampMs
            }
        }
        val rangeScore = when {
            phase == ExercisePhase.UP -> PoseGeometry.normalizedCloseness(torsoAngle, 90f, 45f)
            else -> PoseGeometry.normalizedCloseness(torsoAngle, 160f, 45f)
        }
        val neckScore = PoseGeometry.normalizedCloseness(neckAngle, 165f, 55f)
        val score = (rangeScore * 0.7f + neckScore * 0.3f).toInt().coerceIn(0, 100)
        val feedback = when {
            !valid -> rejection
            neckAngle < 105f -> "neutral_neck"
            phase == ExercisePhase.UP -> "lower_shoulders"
            phase == ExercisePhase.READY || phase == ExercisePhase.DOWN -> "lift_shoulders"
            else -> "starting_position"
        }
        return DetectorResult(type, count, phase, valid, score, tracking, feedback,
            mapOf("Torso flexion" to torsoAngle, "Neck" to neckAngle, "Shoulder-knee ratio" to shoulderToKnee),
            rejection, rep, detectorName = javaClass.simpleName)
    }

    private fun result(tracking: Float, feedback: String, reason: String) = DetectorResult(
        type, count, ExercisePhase.WAITING, false, 0, tracking, feedback,
        rejectionReason = reason, detectorName = javaClass.simpleName
    )

    override fun resetDetector() {
        phase = ExercisePhase.WAITING; liftedAt = 0L; torsoSmoother.reset(); gate.clear()
    }
}
