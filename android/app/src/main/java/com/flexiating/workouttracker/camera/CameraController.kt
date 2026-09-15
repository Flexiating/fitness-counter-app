package com.flexiating.workouttracker.camera

import android.content.Context
import android.annotation.SuppressLint
import android.util.Size
import android.util.Range
import android.hardware.camera2.CaptureRequest
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.camera2.interop.Camera2Interop
import androidx.camera.camera2.interop.Camera2CameraInfo
import androidx.core.content.ContextCompat
import androidx.lifecycle.LifecycleOwner
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
@SuppressLint("UnsafeOptInUsageError")
class CameraController @Inject constructor(
    @param:ApplicationContext private val context: Context
) {
    private val analysisExecutor: ExecutorService = Executors.newSingleThreadExecutor { runnable ->
        Thread(runnable, "WorkoutCameraAnalysis").apply { priority = Thread.NORM_PRIORITY }
    }
    private var provider: ProcessCameraProvider? = null
    private var analysis: ImageAnalysis? = null
    private var running = false

    fun start(
        lifecycleOwner: LifecycleOwner,
        surfaceProvider: Preview.SurfaceProvider,
        frontCamera: Boolean,
        targetFps: Int,
        onFrame: (ImageProxy, Boolean) -> Unit,
        onReady: () -> Unit,
        onError: (Throwable) -> Unit
    ) {
        if (running) return
        val future = ProcessCameraProvider.getInstance(context)
        future.addListener({
            try {
                val cameraProvider = future.get()
                provider = cameraProvider
                val selector = CameraSelector.Builder()
                    .requireLensFacing(if (frontCamera) CameraSelector.LENS_FACING_FRONT else CameraSelector.LENS_FACING_BACK)
                    .build()
                val preview = Preview.Builder().build().also { it.setSurfaceProvider(surfaceProvider) }
                val analysisBuilder = ImageAnalysis.Builder()
                    .setTargetResolution(Size(1280, 720))
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .setOutputImageFormat(ImageAnalysis.OUTPUT_IMAGE_FORMAT_RGBA_8888)
                val requested = targetFps.coerceIn(15, 60)
                val supportedRanges = selector.filter(cameraProvider.availableCameraInfos).firstOrNull()
                    ?.let(Camera2CameraInfo::from)
                    ?.getCameraCharacteristic(android.hardware.camera2.CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES)
                    .orEmpty()
                val fpsRange = supportedRanges.filter { it.contains(requested) }
                    .minByOrNull { (it.upper - requested) + (requested - it.lower) }
                    ?: supportedRanges.maxByOrNull { it.upper }
                    ?: Range(15, requested)
                Camera2Interop.Extender(analysisBuilder).setCaptureRequestOption(
                    CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE,
                    fpsRange
                )
                analysis = analysisBuilder.build().also { useCase ->
                        useCase.setAnalyzer(analysisExecutor) { image ->
                            try { onFrame(image, frontCamera) } catch (error: Throwable) {
                                image.close()
                                onError(error)
                            }
                        }
                    }
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(lifecycleOwner, selector, preview, analysis)
                running = true
                onReady()
            } catch (error: Throwable) {
                running = false
                onError(error)
            }
        }, ContextCompat.getMainExecutor(context))
    }

    fun stop() {
        analysis?.clearAnalyzer()
        analysis = null
        provider?.unbindAll()
        running = false
    }

    fun restart(
        lifecycleOwner: LifecycleOwner,
        surfaceProvider: Preview.SurfaceProvider,
        frontCamera: Boolean,
        targetFps: Int,
        onFrame: (ImageProxy, Boolean) -> Unit,
        onReady: () -> Unit,
        onError: (Throwable) -> Unit
    ) {
        stop()
        start(lifecycleOwner, surfaceProvider, frontCamera, targetFps, onFrame, onReady, onError)
    }
}
