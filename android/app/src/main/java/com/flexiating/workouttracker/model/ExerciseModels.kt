package com.flexiating.workouttracker.model

enum class ExerciseType(val title: String) {
    PUSH_UP("Push-up"),
    CRUNCH("Crunch"),
    SQUAT("Squat"),
    PLANK("Plank"),
    LUNGE("Lunge")
}

enum class ExercisePhase { WAITING, READY, UP, DOWN, HOLDING }

data class Landmark3D(
    val x: Float,
    val y: Float,
    val z: Float,
    val visibility: Float,
    val presence: Float = 1f
)

object PoseIndex {
    const val NOSE = 0
    const val LEFT_EAR = 7
    const val RIGHT_EAR = 8
    const val LEFT_SHOULDER = 11
    const val RIGHT_SHOULDER = 12
    const val LEFT_ELBOW = 13
    const val RIGHT_ELBOW = 14
    const val LEFT_WRIST = 15
    const val RIGHT_WRIST = 16
    const val LEFT_HIP = 23
    const val RIGHT_HIP = 24
    const val LEFT_KNEE = 25
    const val RIGHT_KNEE = 26
    const val LEFT_ANKLE = 27
    const val RIGHT_ANKLE = 28
    const val LEFT_HEEL = 29
    const val RIGHT_HEEL = 30
    const val LEFT_FOOT = 31
    const val RIGHT_FOOT = 32
}

data class PoseFrame(
    val landmarks: List<Landmark3D>,
    val timestampMs: Long,
    val inferenceMs: Long,
    val imageWidth: Int,
    val imageHeight: Int,
    val mirrored: Boolean
) {
    val personDetected: Boolean get() = landmarks.size >= 33

    fun landmark(index: Int): Landmark3D? = landmarks.getOrNull(index)

    fun averageVisibility(indices: IntArray): Float {
        var total = 0f
        var found = 0
        indices.forEach { index ->
            landmark(index)?.let { total += it.visibility; found++ }
        }
        return if (found == 0) 0f else total / found
    }
}

data class DetectorResult(
    val type: ExerciseType,
    val count: Int,
    val phase: ExercisePhase,
    val postureValid: Boolean,
    val formScore: Int,
    val trackingConfidence: Float,
    val feedback: String,
    val angles: Map<String, Float> = emptyMap(),
    val rejectionReason: String = "",
    val repCompleted: Boolean = false,
    val holdSeconds: Int = 0,
    val detectorName: String = ""
)

data class WorkoutSettings(
    val darkMode: Boolean = true,
    val useFrontCamera: Boolean = true,
    val targetFps: Int = 30,
    val showFps: Boolean = true,
    val debugMode: Boolean = false,
    val soundEnabled: Boolean = true,
    val vibrationEnabled: Boolean = true,
    val language: String = "English"
)

data class WorkoutUiState(
    val exercise: ExerciseType = ExerciseType.PUSH_UP,
    val result: DetectorResult = DetectorResult(
        type = ExerciseType.PUSH_UP,
        count = 0,
        phase = ExercisePhase.WAITING,
        postureValid = false,
        formScore = 0,
        trackingConfidence = 0f,
        feedback = "Move into the camera frame"
    ),
    val poseFrame: PoseFrame? = null,
    val fps: Float = 0f,
    val elapsedMs: Long = 0L,
    val cameraRunning: Boolean = false,
    val cameraError: String? = null,
    val settings: WorkoutSettings = WorkoutSettings()
)
