package com.flexiating.workouttracker.viewmodel

import android.app.Application
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.Build
import android.os.SystemClock
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import androidx.camera.core.Preview
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.viewModelScope
import com.flexiating.workouttracker.camera.CameraController
import com.flexiating.workouttracker.data.SettingsRepository
import com.flexiating.workouttracker.data.local.WorkoutRepository
import com.flexiating.workouttracker.data.local.WorkoutSessionEntity
import com.flexiating.workouttracker.detectors.DetectorRegistry
import com.flexiating.workouttracker.mediapipe.PoseLandmarkerEngine
import com.flexiating.workouttracker.model.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class WorkoutViewModel @Inject constructor(
    application: Application,
    private val camera: CameraController,
    private val poseEngine: PoseLandmarkerEngine,
    private val detectors: DetectorRegistry,
    private val workoutRepository: WorkoutRepository,
    private val settingsRepository: SettingsRepository
) : AndroidViewModel(application), PoseLandmarkerEngine.Listener {
    private val _state = MutableStateFlow(WorkoutUiState())
    val state: StateFlow<WorkoutUiState> = _state.asStateFlow()
    private var sessionStartMs = 0L
    private var timerJob: Job? = null
    private var lastFrameMs = 0L
    private var fpsSmoothed = 0f
    private var scoreTotal = 0L
    private var scoreSamples = 0
    private var fpsTotal = 0.0
    private var fpsSamples = 0
    private val tone = ToneGenerator(AudioManager.STREAM_NOTIFICATION, 65)

    init {
        poseEngine.setListener(this)
        viewModelScope.launch {
            settingsRepository.settings.collectLatest { value -> _state.value = _state.value.copy(settings = value) }
        }
    }

    fun startCamera(owner: LifecycleOwner, surfaceProvider: Preview.SurfaceProvider) {
        val current = _state.value
        camera.start(owner, surfaceProvider, current.settings.useFrontCamera, current.settings.targetFps,
            onFrame = poseEngine::detect,
            onReady = { _state.value = _state.value.copy(cameraRunning = true, cameraError = null) },
            onError = { _state.value = _state.value.copy(cameraRunning = false, cameraError = it.message ?: "Camera error") })
    }

    fun stopCamera() {
        camera.stop()
        _state.value = _state.value.copy(cameraRunning = false)
    }

    fun toggleCamera(owner: LifecycleOwner, surfaceProvider: Preview.SurfaceProvider) {
        viewModelScope.launch {
            val updated = _state.value.settings.copy(useFrontCamera = !_state.value.settings.useFrontCamera)
            settingsRepository.update(updated)
            _state.value = _state.value.copy(settings = updated)
            restartCamera(owner, surfaceProvider)
        }
    }

    fun restartCamera(owner: LifecycleOwner, surfaceProvider: Preview.SurfaceProvider) {
        val current = _state.value
        camera.restart(owner, surfaceProvider, current.settings.useFrontCamera, current.settings.targetFps,
            onFrame = poseEngine::detect,
            onReady = { _state.value = _state.value.copy(cameraRunning = true, cameraError = null) },
            onError = { _state.value = _state.value.copy(cameraRunning = false, cameraError = it.message ?: "Camera error") })
    }

    fun selectExercise(type: ExerciseType) {
        detectors.select(type)
        stopSession(save = true)
        _state.value = _state.value.copy(
            exercise = type,
            elapsedMs = 0L,
            result = DetectorResult(type, 0, ExercisePhase.WAITING, false, 0, 0f, "Move into the camera frame", detectorName = detectors.current().javaClass.simpleName)
        )
        resetStats()
    }

    fun resetWorkout() {
        stopSession(save = false)
        detectors.resetCurrent()
        val type = _state.value.exercise
        _state.value = _state.value.copy(elapsedMs = 0L,
            result = DetectorResult(type, 0, ExercisePhase.WAITING, false, 0, 0f, "Ready", detectorName = detectors.current().javaClass.simpleName))
        resetStats()
    }

    override fun onPose(frame: PoseFrame) {
        val now = frame.timestampMs
        if (lastFrameMs > 0 && now > lastFrameMs) {
            val instant = 1000f / (now - lastFrameMs).toFloat()
            fpsSmoothed = if (fpsSmoothed == 0f) instant else fpsSmoothed * 0.85f + instant * 0.15f
        }
        lastFrameMs = now
        val result = detectors.current().process(frame)
        if (result.repCompleted) {
            if (sessionStartMs == 0L) startSession()
            provideRepFeedback()
        }
        scoreTotal += result.formScore; scoreSamples++
        fpsTotal += fpsSmoothed; fpsSamples++
        _state.value = _state.value.copy(result = result, poseFrame = frame, fps = fpsSmoothed, cameraError = null)
    }

    override fun onPoseError(message: String) {
        _state.value = _state.value.copy(cameraError = message)
    }

    fun saveCurrentSession() = stopSession(save = true)

    private fun startSession() {
        if (sessionStartMs != 0L) return
        sessionStartMs = SystemClock.elapsedRealtime()
        timerJob = viewModelScope.launch {
            while (sessionStartMs != 0L) {
                _state.value = _state.value.copy(elapsedMs = SystemClock.elapsedRealtime() - sessionStartMs)
                delay(100)
            }
        }
    }

    private fun stopSession(save: Boolean) {
        val started = sessionStartMs
        val snapshot = _state.value
        sessionStartMs = 0L
        timerJob?.cancel(); timerJob = null
        if (save && started != 0L && snapshot.result.count > 0) {
            viewModelScope.launch {
                workoutRepository.save(WorkoutSessionEntity(
                    exercise = snapshot.exercise.name,
                    dateEpochMs = System.currentTimeMillis(),
                    reps = snapshot.result.count,
                    durationMs = snapshot.elapsedMs,
                    averageFormScore = if (scoreSamples == 0) 0f else scoreTotal.toFloat() / scoreSamples,
                    averageFps = if (fpsSamples == 0) 0f else (fpsTotal / fpsSamples).toFloat()
                ))
            }
        }
    }

    private fun provideRepFeedback() {
        val settings = _state.value.settings
        if (settings.soundEnabled) tone.startTone(ToneGenerator.TONE_PROP_BEEP, 80)
        if (settings.vibrationEnabled) {
            val app = getApplication<Application>()
            val vibrator = if (Build.VERSION.SDK_INT >= 31) app.getSystemService(VibratorManager::class.java).defaultVibrator
                else @Suppress("DEPRECATION") app.getSystemService(Vibrator::class.java)
            vibrator.vibrate(VibrationEffect.createOneShot(35, VibrationEffect.DEFAULT_AMPLITUDE))
        }
    }

    private fun resetStats() {
        scoreTotal = 0; scoreSamples = 0; fpsTotal = 0.0; fpsSamples = 0; lastFrameMs = 0; fpsSmoothed = 0f
    }

    override fun onCleared() {
        stopSession(save = true)
        camera.stop()
        poseEngine.setListener(null)
        tone.release()
    }
}
