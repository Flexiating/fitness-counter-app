package com.flexiating.workouttracker

import com.flexiating.workouttracker.detectors.CrunchDetector
import com.flexiating.workouttracker.detectors.PushUpDetector
import com.flexiating.workouttracker.model.Landmark3D
import com.flexiating.workouttracker.model.PoseFrame
import org.junit.Assert.assertEquals
import org.junit.Test

class ExerciseDetectorTest {
    @Test fun fullPushUpCountsOnlyAfterReturningUp() {
        val detector = PushUpDetector()
        (0L..400L step 50).forEach { detector.process(pushUpFrame(it, bent = false)) }
        (450L..1_200L step 50).forEach { detector.process(pushUpFrame(it, bent = true)) }
        assertEquals(0, detector.process(pushUpFrame(1_250, bent = false)).count)
        var result = detector.process(pushUpFrame(1_300, bent = false))
        (1_350L..2_300L step 50).forEach { result = detector.process(pushUpFrame(it, bent = false)) }
        assertEquals(1, result.count)
    }

    @Test fun crunchUsesTorsoMotionAndCountsAfterLowering() {
        val detector = CrunchDetector()
        (0L..400L step 50).forEach { detector.process(crunchFrame(it, curled = false)) }
        (450L..1_200L step 50).forEach { detector.process(crunchFrame(it, curled = true)) }
        assertEquals(0, detector.process(crunchFrame(1_250, curled = false)).count)
        var result = detector.process(crunchFrame(1_300, curled = false))
        (1_350L..2_300L step 50).forEach { result = detector.process(crunchFrame(it, curled = false)) }
        assertEquals(1, result.count)
    }

    private fun pushUpFrame(time: Long, bent: Boolean): PoseFrame {
        val points = MutableList(33) { Landmark3D(.5f, .5f, 0f, 1f) }
        points[11] = Landmark3D(.20f, .5f, 0f, 1f); points[12] = Landmark3D(.20f, .52f, 0f, 1f)
        points[13] = Landmark3D(.35f, if (bent) .60f else .5f, 0f, 1f); points[14] = Landmark3D(.35f, if (bent) .62f else .52f, 0f, 1f)
        points[15] = Landmark3D(if (bent) .40f else .50f, if (bent) .45f else .5f, 0f, 1f)
        points[16] = Landmark3D(if (bent) .40f else .50f, if (bent) .47f else .52f, 0f, 1f)
        points[23] = Landmark3D(.50f, .5f, 0f, 1f); points[24] = Landmark3D(.50f, .52f, 0f, 1f)
        points[25] = Landmark3D(.70f, .5f, 0f, 1f); points[26] = Landmark3D(.70f, .52f, 0f, 1f)
        points[27] = Landmark3D(.90f, .5f, 0f, 1f); points[28] = Landmark3D(.90f, .52f, 0f, 1f)
        return PoseFrame(points, time, 10, 1280, 720, true)
    }

    private fun crunchFrame(time: Long, curled: Boolean): PoseFrame {
        val points = MutableList(33) { Landmark3D(.5f, .5f, 0f, 1f) }
        if (curled) {
            points[7] = Landmark3D(.62f, .28f, 0f, 1f); points[8] = Landmark3D(.63f, .29f, 0f, 1f)
            points[11] = Landmark3D(.65f, .38f, 0f, 1f); points[12] = Landmark3D(.66f, .39f, 0f, 1f)
        } else {
            points[7] = Landmark3D(.20f, .5f, 0f, 1f); points[8] = Landmark3D(.21f, .51f, 0f, 1f)
            points[11] = Landmark3D(.30f, .5f, 0f, 1f); points[12] = Landmark3D(.31f, .51f, 0f, 1f)
        }
        points[23] = Landmark3D(.55f, .5f, 0f, 1f); points[24] = Landmark3D(.56f, .51f, 0f, 1f)
        points[25] = Landmark3D(.72f, .5f, 0f, 1f); points[26] = Landmark3D(.73f, .51f, 0f, 1f)
        return PoseFrame(points, time, 10, 1280, 720, true)
    }
}
