package com.flexiating.workouttracker.utils

import com.flexiating.workouttracker.model.Landmark3D
import kotlin.math.abs
import kotlin.math.acos
import kotlin.math.atan2
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

object PoseGeometry {
    fun angle(a: Landmark3D, b: Landmark3D, c: Landmark3D): Float {
        val bax = a.x - b.x
        val bay = a.y - b.y
        val baz = a.z - b.z
        val bcx = c.x - b.x
        val bcy = c.y - b.y
        val bcz = c.z - b.z
        val dot = bax * bcx + bay * bcy + baz * bcz
        val mag1 = sqrt(bax * bax + bay * bay + baz * baz)
        val mag2 = sqrt(bcx * bcx + bcy * bcy + bcz * bcz)
        if (mag1 < 1e-6f || mag2 < 1e-6f) return Float.NaN
        return Math.toDegrees(acos((dot / (mag1 * mag2)).coerceIn(-1f, 1f)).toDouble()).toFloat()
    }

    fun distance(a: Landmark3D, b: Landmark3D): Float =
        sqrt((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y) + (a.z - b.z) * (a.z - b.z))

    fun midpoint(a: Landmark3D, b: Landmark3D) = Landmark3D(
        x = (a.x + b.x) / 2f,
        y = (a.y + b.y) / 2f,
        z = (a.z + b.z) / 2f,
        visibility = min(a.visibility, b.visibility),
        presence = min(a.presence, b.presence)
    )

    fun torsoInclination(shoulder: Landmark3D, hip: Landmark3D): Float {
        val dx = shoulder.x - hip.x
        val dy = shoulder.y - hip.y
        return abs(Math.toDegrees(atan2(dx.toDouble(), -dy.toDouble())).toFloat())
    }

    fun bodyHorizontalDeviation(shoulder: Landmark3D, ankle: Landmark3D): Float {
        val dx = abs(ankle.x - shoulder.x)
        val dy = abs(ankle.y - shoulder.y)
        return Math.toDegrees(atan2(dy.toDouble(), max(dx, 1e-5f).toDouble())).toFloat()
    }

    fun normalizedCloseness(value: Float, ideal: Float, tolerance: Float): Int =
        (100f * (1f - abs(value - ideal) / tolerance)).coerceIn(0f, 100f).toInt()
}

class ExponentialSmoother(private val alpha: Float = 0.35f) {
    private var value: Float? = null
    fun update(next: Float): Float {
        if (!next.isFinite()) return value ?: next
        value = value?.let { alpha * next + (1f - alpha) * it } ?: next
        return value!!
    }
    fun reset() { value = null }
}

class TransitionGate(private val debounceMs: Long = 200L) {
    private var candidate: String? = null
    private var candidateSince = 0L

    fun accepts(next: String, timestampMs: Long): Boolean {
        if (candidate != next) {
            candidate = next
            candidateSince = timestampMs
            return false
        }
        return timestampMs - candidateSince >= debounceMs
    }

    fun clear() {
        candidate = null
        candidateSince = 0L
    }
}

