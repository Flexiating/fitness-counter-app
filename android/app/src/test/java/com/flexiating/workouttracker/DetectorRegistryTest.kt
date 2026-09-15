package com.flexiating.workouttracker

import com.flexiating.workouttracker.detectors.*
import com.flexiating.workouttracker.model.ExerciseType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotSame
import org.junit.Test

class DetectorRegistryTest {
    @Test fun everyExerciseHasAnIndependentDetector() {
        val registry = DetectorRegistry(PushUpDetector(), CrunchDetector(), SquatDetector(), PlankDetector(), LungeDetector())
        val pushUp = registry.select(ExerciseType.PUSH_UP)
        val crunch = registry.select(ExerciseType.CRUNCH)
        assertNotSame(pushUp, crunch)
        assertEquals(ExerciseType.CRUNCH, crunch.type)
        assertEquals("CrunchDetector", crunch.javaClass.simpleName)
        assertEquals(ExerciseType.PUSH_UP, registry.select(ExerciseType.PUSH_UP).type)
    }
}

