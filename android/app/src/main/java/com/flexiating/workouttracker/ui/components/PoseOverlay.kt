package com.flexiating.workouttracker.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import com.flexiating.workouttracker.model.PoseFrame

private val connections = listOf(
    0 to 7, 0 to 8, 7 to 11, 8 to 12, 11 to 12,
    11 to 13, 13 to 15, 12 to 14, 14 to 16,
    11 to 23, 12 to 24, 23 to 24,
    23 to 25, 25 to 27, 27 to 29, 29 to 31,
    24 to 26, 26 to 28, 28 to 30, 30 to 32
)

@Composable
fun PoseOverlay(frame: PoseFrame?, modifier: Modifier = Modifier) {
    Canvas(modifier) {
        val pose = frame ?: return@Canvas
        val landmarks = pose.landmarks
        val imageWidth = pose.imageWidth.toFloat().coerceAtLeast(1f)
        val imageHeight = pose.imageHeight.toFloat().coerceAtLeast(1f)
        val scale = minOf(size.width / imageWidth, size.height / imageHeight)
        val renderedWidth = imageWidth * scale
        val renderedHeight = imageHeight * scale
        val offsetX = (size.width - renderedWidth) / 2f
        val offsetY = (size.height - renderedHeight) / 2f
        fun point(x: Float, y: Float) = Offset(offsetX + x * renderedWidth, offsetY + y * renderedHeight)
        connections.forEach { (aIndex, bIndex) ->
            val a = landmarks.getOrNull(aIndex) ?: return@forEach
            val b = landmarks.getOrNull(bIndex) ?: return@forEach
            if (a.visibility > 0.45f && b.visibility > 0.45f) {
                drawLine(Color(0xFF38BDF8), point(a.x, a.y), point(b.x, b.y), 5f, StrokeCap.Round)
            }
        }
        landmarks.forEach {
            if (it.visibility > 0.45f) drawCircle(Color(0xFF22C55E), 5.5f, point(it.x, it.y))
        }
    }
}
