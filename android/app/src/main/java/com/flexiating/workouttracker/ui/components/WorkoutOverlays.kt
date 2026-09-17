package com.flexiating.workouttracker.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.res.stringResource
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.model.WorkoutUiState
import com.flexiating.workouttracker.ui.exerciseName
import com.flexiating.workouttracker.ui.feedbackText
import com.flexiating.workouttracker.ui.phaseName
import java.util.Locale

@Composable
fun WorkoutMetricsOverlay(state: WorkoutUiState, modifier: Modifier = Modifier) {
    BoxWithConstraints(modifier) {
        val compact = maxHeight < 280.dp
        Column(Modifier.align(Alignment.TopStart).padding(if (compact) 8.dp else 12.dp).background(Color.Black.copy(alpha = .55f), RoundedCornerShape(12.dp)).padding(if (compact) 8.dp else 12.dp)) {
            if (!compact) {
                Text(exerciseName(state.exercise), fontWeight = FontWeight.Bold)
                Text(stringResource(R.string.state_value, phaseName(state.result.phase)), fontSize = 13.sp)
                RepCounter(state.result.count)
            } else Text(stringResource(R.string.reps_value, state.result.count), fontSize = 24.sp, fontWeight = FontWeight.Bold)
        }
        Column(Modifier.align(Alignment.TopEnd).padding(if (compact) 8.dp else 12.dp).background(Color.Black.copy(alpha = .55f), RoundedCornerShape(12.dp)).padding(if (compact) 8.dp else 12.dp), horizontalAlignment = Alignment.End) {
            if (state.settings.showFps) Text(String.format(Locale.US, "%.1f FPS", state.fps), fontSize = 13.sp)
            Text(stringResource(R.string.tracking_value, (state.result.trackingConfidence * 100).toInt()), fontSize = 13.sp)
            Text(stringResource(R.string.form_value, state.result.formScore), fontSize = 13.sp)
        }
        val seconds = state.elapsedMs / 1000
        Row(Modifier.align(if (compact) Alignment.BottomStart else Alignment.BottomCenter).padding(start = if (compact) 8.dp else 0.dp, bottom = if (compact) 20.dp else 78.dp).background(Color.Black.copy(alpha = .75f), RoundedCornerShape(16.dp)).padding(12.dp),
            verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            if (!compact) GoalRing(state.result.count.toFloat() / state.settings.targetReps.coerceAtLeast(1))
            Text(String.format(Locale.US, "%02d:%02d", seconds / 60, seconds % 60), fontSize = if (compact) 16.sp else 24.sp, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
fun DebugOverlay(state: WorkoutUiState, modifier: Modifier = Modifier) {
    Column(modifier.background(Color(0xDD0B0F14), RoundedCornerShape(12.dp)).padding(12.dp)) {
        Text(stringResource(R.string.debug_detector, state.result.detectorName), color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
        Text(stringResource(R.string.state_machine, phaseName(state.result.phase)), fontSize = 12.sp)
        Text(stringResource(R.string.visibility_value, (state.result.trackingConfidence * 100).toInt()), fontSize = 12.sp)
        state.result.angles.forEach { (name, angle) -> Text("${angleName(name)}: ${angle.toInt()}°", fontSize = 12.sp) }
        if (state.result.rejectionReason.isNotBlank()) Text(stringResource(R.string.rejected_value, feedbackText(state.result.rejectionReason)), color = Color(0xFFF59E0B), fontSize = 12.sp)
    }
}

@Composable
private fun angleName(name: String): String = stringResource(when (name) {
    "Left elbow" -> R.string.angle_left_elbow
    "Right elbow" -> R.string.angle_right_elbow
    "Hip" -> R.string.angle_hip
    "Knee" -> R.string.angle_knee
    "Torso flexion" -> R.string.angle_torso
    "Neck" -> R.string.angle_neck
    else -> R.string.angle_shoulder_knee
})
