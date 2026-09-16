package com.flexiating.workouttracker.ui.screens

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Cameraswitch
import androidx.compose.material.icons.rounded.PlayArrow
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.flexiating.workouttracker.model.ExerciseType
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.ui.exerciseName
import com.flexiating.workouttracker.ui.feedbackText
import com.flexiating.workouttracker.ui.components.*
import com.flexiating.workouttracker.ui.theme.Success
import com.flexiating.workouttracker.viewmodel.WorkoutViewModel

@Composable
fun WorkoutScreen(viewModel: WorkoutViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsState()
    val context = LocalContext.current
    val owner = LocalLifecycleOwner.current
    val preview = remember { PreviewView(context) }
    var permission by remember { mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) }
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { permission = it }

    LaunchedEffect(Unit) { if (!permission) permissionLauncher.launch(Manifest.permission.CAMERA) }
    LaunchedEffect(permission) { if (permission) viewModel.startCamera(owner, preview.surfaceProvider) }
    DisposableEffect(Unit) { onDispose { viewModel.stopCamera() } }

    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            Column {
                Text(stringResource(R.string.app_name), style = MaterialTheme.typography.headlineSmall)
                Text(stringResource(if (state.cameraRunning) R.string.camera_active else R.string.camera_stopped), color = if (state.cameraRunning) Success else MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 13.sp)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalIconButton(onClick = { viewModel.toggleCamera(owner, preview.surfaceProvider) }, enabled = permission) { Icon(Icons.Rounded.Cameraswitch, stringResource(R.string.switch_camera)) }
                FilledTonalIconButton(onClick = { if (state.cameraRunning) viewModel.stopCamera() else viewModel.startCamera(owner, preview.surfaceProvider) }, enabled = permission) {
                    Icon(if (state.cameraRunning) Icons.Rounded.Stop else Icons.Rounded.PlayArrow, stringResource(if (state.cameraRunning) R.string.stop else R.string.start))
                }
                FilledTonalIconButton(onClick = viewModel::resetWorkout) { Icon(Icons.Rounded.Refresh, stringResource(R.string.reset)) }
            }
        }

        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(ExerciseType.entries) { exercise ->
                FilterChip(selected = state.exercise == exercise, onClick = { viewModel.selectExercise(exercise) }, label = { Text(exerciseName(exercise)) })
            }
        }

        Box(Modifier.weight(1f).fillMaxWidth().clip(RoundedCornerShape(20.dp)).background(Color.Black)) {
            if (permission) CameraPreview(preview, Modifier.fillMaxSize())
            else PermissionMessage { permissionLauncher.launch(Manifest.permission.CAMERA) }
            PoseOverlay(state.poseFrame, Modifier.fillMaxSize())
            WorkoutMetricsOverlay(state, Modifier.fillMaxSize())
            if (state.settings.debugMode) DebugOverlay(state, Modifier.align(Alignment.BottomStart).padding(12.dp).widthIn(max = 300.dp))
            state.cameraError?.let { Text(stringResource(R.string.camera_error), color = MaterialTheme.colorScheme.error, modifier = Modifier.align(Alignment.Center).background(Color.Black.copy(alpha = .8f), RoundedCornerShape(12.dp)).padding(16.dp)) }
        }
        ElevatedCard(Modifier.fillMaxWidth()) {
            Row(Modifier.fillMaxWidth().padding(14.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
                Column(Modifier.weight(1f)) {
                    Text(stringResource(R.string.live_coaching), fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(feedbackText(state.result.feedback))
                    Text(stringResource(R.string.target_progress, state.result.count.coerceAtMost(state.settings.targetReps), state.settings.targetReps), fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Text("${state.result.formScore}%", style = MaterialTheme.typography.headlineSmall, color = if (state.result.postureValid) Success else MaterialTheme.colorScheme.error)
            }
        }
    }
}

@Composable
private fun PermissionMessage(onRequest: () -> Unit) {
    Column(Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
        Text(stringResource(R.string.camera_permission_required))
        Spacer(Modifier.height(8.dp))
        Button(onClick = onRequest) { Text(stringResource(R.string.allow_camera)) }
    }
}
