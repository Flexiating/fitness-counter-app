package com.flexiating.workouttracker.mediapipe

import android.content.Context
import android.graphics.Bitmap
import androidx.core.graphics.createBitmap
import android.graphics.Matrix
import android.os.SystemClock
import androidx.camera.core.ImageProxy
import com.flexiating.workouttracker.model.Landmark3D
import com.flexiating.workouttracker.model.PoseFrame
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.framework.image.MPImage
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.core.Delegate
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarkerResult
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PoseLandmarkerEngine @Inject constructor(
    @param:ApplicationContext private val context: Context
) : AutoCloseable {
    @Volatile private var landmarker: PoseLandmarker? = null
    @Volatile private var listener: Listener? = null
    @Volatile private var lastWidth = 0
    @Volatile private var lastHeight = 0
    @Volatile private var mirrored = false

    interface Listener {
        fun onPose(frame: PoseFrame)
        fun onPoseError(message: String)
    }

    fun setListener(listener: Listener?) { this.listener = listener }

    @Synchronized private fun ensureInitialized() {
        if (landmarker != null) return
        val options = PoseLandmarker.PoseLandmarkerOptions.builder()
            .setBaseOptions(BaseOptions.builder().setDelegate(Delegate.CPU).setModelAssetPath(MODEL).build())
            .setRunningMode(RunningMode.LIVE_STREAM)
            .setNumPoses(1)
            .setMinPoseDetectionConfidence(0.55f)
            .setMinPosePresenceConfidence(0.55f)
            .setMinTrackingConfidence(0.55f)
            .setResultListener(::onResult)
            .setErrorListener { listener?.onPoseError(it.message ?: "MediaPipe pose error") }
            .build()
        landmarker = PoseLandmarker.createFromOptions(context, options)
    }

    fun detect(imageProxy: ImageProxy, isFrontCamera: Boolean) {
        ensureInitialized()
        val timestamp = SystemClock.uptimeMillis()
        val rotation = imageProxy.imageInfo.rotationDegrees
        val bitmap = createBitmap(imageProxy.width, imageProxy.height, Bitmap.Config.ARGB_8888)
        try {
            bitmap.copyPixelsFromBuffer(imageProxy.planes[0].buffer)
        } finally {
            imageProxy.close()
        }
        val matrix = Matrix().apply {
            postRotate(rotation.toFloat())
            if (isFrontCamera) postScale(-1f, 1f, bitmap.width / 2f, bitmap.height / 2f)
        }
        val transformed = Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
        if (transformed !== bitmap) bitmap.recycle()
        lastWidth = transformed.width
        lastHeight = transformed.height
        mirrored = isFrontCamera
        val image = BitmapImageBuilder(transformed).build()
        landmarker?.detectAsync(image, timestamp)
    }

    private fun onResult(result: PoseLandmarkerResult, input: MPImage) {
        val normalized = result.landmarks().firstOrNull().orEmpty().map {
            Landmark3D(
                x = it.x(), y = it.y(), z = it.z(),
                visibility = it.visibility().orElse(0f),
                presence = it.presence().orElse(0f)
            )
        }
        listener?.onPose(
            PoseFrame(
                landmarks = normalized,
                timestampMs = result.timestampMs(),
                inferenceMs = (SystemClock.uptimeMillis() - result.timestampMs()).coerceAtLeast(0L),
                imageWidth = input.width.takeIf { it > 0 } ?: lastWidth,
                imageHeight = input.height.takeIf { it > 0 } ?: lastHeight,
                mirrored = mirrored
            )
        )
    }

    @Synchronized override fun close() {
        landmarker?.close()
        landmarker = null
    }

    companion object { private const val MODEL = "pose_landmarker_full.task" }
}
