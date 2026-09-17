package com.flexiating.workouttracker.ui.components

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.res.stringResource
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.model.ExerciseType
import com.flexiating.workouttracker.ui.theme.Accent
import com.flexiating.workouttracker.ui.theme.Success

@Composable
fun MotionIconButton(onClick: () -> Unit, enabled: Boolean = true, content: @Composable () -> Unit) {
    val interaction = remember { MutableInteractionSource() }
    val pressed by interaction.collectIsPressedAsState()
    val scale by animateFloatAsState(if (pressed) .98f else 1f, tween(150), label = "button")
    FilledTonalIconButton(onClick = onClick, enabled = enabled, interactionSource = interaction,
        modifier = Modifier.size(48.dp).graphicsLayer { scaleX = scale; scaleY = scale }) { content() }
}

@Composable
fun RepCounter(value: Int, modifier: Modifier = Modifier) {
    val description = stringResource(R.string.reps_value, value)
    AnimatedContent(value, modifier.semantics { contentDescription = description }, transitionSpec = { fadeIn(tween(200)) togetherWith fadeOut(tween(150)) }, label = "repetitions") { count ->
        Text(count.toString(), fontSize = 48.sp, fontWeight = FontWeight.Bold, color = Color.White)
    }
}

@Composable
fun GoalRing(fraction: Float, modifier: Modifier = Modifier) {
    val progress by animateFloatAsState(fraction.coerceIn(0f, 1f), tween(200), label = "goal")
    Box(modifier.size(64.dp), contentAlignment = Alignment.Center) {
        CircularProgressIndicator(progress = { progress }, modifier = Modifier.fillMaxSize(),
            color = if (fraction >= 1f) Success else Accent, trackColor = Color(0xFF303744), strokeWidth = 5.dp)
        Text("${(fraction.coerceIn(0f, 1f) * 100).toInt()}%", style = MaterialTheme.typography.labelMedium)
    }
}

@Composable
fun ExerciseIllustration(exercise: ExerciseType, modifier: Modifier = Modifier) {
    Canvas(modifier.fillMaxWidth().height(140.dp)) {
        val scale = minOf(size.width / 340f, size.height / 140f)
        val left = (size.width - 320 * scale) / 2
        fun point(x: Float, y: Float) = Offset(left + x * scale, y * scale)
        fun line(a: Offset, b: Offset) = drawLine(Accent, a, b, 7 * scale, StrokeCap.Round)
        drawLine(Color(0xFF303744), point(10f, 120f), point(310f, 120f), 2 * scale)
        val points = if (exercise == ExerciseType.PUSH_UP) listOf(point(70f, 48f), point(135f, 68f), point(260f, 113f))
            else listOf(point(95f, 70f), point(160f, 112f), point(220f, 58f), point(275f, 114f))
        points.zipWithNext().forEach { (a, b) -> line(a, b) }
        if (exercise == ExerciseType.PUSH_UP) {
            line(point(70f, 48f), point(75f, 114f)); drawCircle(Accent, 13 * scale, point(55f, 32f))
        } else {
            line(point(95f, 70f), point(135f, 57f)); drawCircle(Accent, 13 * scale, point(76f, 58f))
        }
    }
}

@Composable
fun ReadingPage(content: @Composable () -> Unit) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.TopCenter) {
        Box(Modifier.widthIn(max = 900.dp).fillMaxSize()) { content() }
    }
}
