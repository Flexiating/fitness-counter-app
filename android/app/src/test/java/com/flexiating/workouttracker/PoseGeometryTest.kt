package com.flexiating.workouttracker

import com.flexiating.workouttracker.model.Landmark3D
import com.flexiating.workouttracker.utils.PoseGeometry
import org.junit.Assert.assertEquals
import org.junit.Test

class PoseGeometryTest {
    @Test fun angleReturnsAngleAtMiddlePoint() {
        val a = Landmark3D(0f, 1f, 0f, 1f)
        val b = Landmark3D(0f, 0f, 0f, 1f)
        val c = Landmark3D(1f, 0f, 0f, 1f)
        assertEquals(90f, PoseGeometry.angle(a, b, c), 0.01f)
    }

    @Test fun straightLineIsOneHundredEightyDegrees() {
        assertEquals(180f, PoseGeometry.angle(
            Landmark3D(0f, 0f, 0f, 1f), Landmark3D(1f, 0f, 0f, 1f), Landmark3D(2f, 0f, 0f, 1f)
        ), 0.01f)
    }
}

