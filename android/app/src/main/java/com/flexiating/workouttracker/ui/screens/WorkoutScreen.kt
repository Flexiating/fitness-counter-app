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
import androidx.compose.material.icons.rounded.VideocamOff
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.ui.platform.LocalDensity
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
    val wide = with(LocalDensity.current) { LocalWindowInfo.current.containerSize.width.toDp() >= 600.dp }
    var permission by remember { mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) }
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { permission = it }

    LaunchedEffect(Unit) { if (!permission) permissionLauncher.launch(Manifest.permission.CAMERA) }
    LaunchedEffect(permission) { if (permission) viewModel.startCamera(owner, preview.surfaceProvider) }
    DisposableEffect(Unit) { onDispose { viewModel.stopCamera() } }

    val progress by animateFloatAsState((state.result.count.toFloat() / state.settings.targetReps.coerceAtLeast(1)).coerceIn(0f, 1f), tween(200), label = "workout progress")
    val cameraContent: @Composable (Modifier) -> Unit = { modifier ->
        BoxWithConstraints(modifier.clip(RoundedCornerShape(18.dp)).background(Color.Black)) {
            val compact = maxHeight < 280.dp
            if (permission) CameraPreview(preview, Modifier.fillMaxSize())
            if (state.cameraRunning) {
                PoseOverlay(state.poseFrame, Modifier.fillMaxSize())
                WorkoutMetricsOverlay(state, Modifier.fillMaxSize())
            } else Column(Modifier.fillMaxSize().background(Color.Black).padding(horizontal = 24.dp).padding(top = if (compact) 32.dp else 24.dp, bottom = if (compact) 8.dp else 24.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                if (!compact) {
                    Icon(Icons.Rounded.VideocamOff, null, modifier = Modifier.size(56.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    Spacer(Modifier.height(16.dp))
                }
                Text(stringResource(if (permission) R.string.camera_off else R.string.camera_permission_required), style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.height(if (compact) 4.dp else 20.dp))
                if (permission) Button(onClick = { viewModel.startCamera(owner, preview.surfaceProvider) }, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.start)) }
                else Button(onClick = { permissionLauncher.launch(Manifest.permission.CAMERA) }, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.allow_camera)) }
            }
            if (state.cameraRunning) Row(Modifier.align(Alignment.BottomEnd).padding(14.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MotionIconButton(onClick = { viewModel.toggleCamera(owner, preview.surfaceProvider) }, enabled = permission) { Icon(Icons.Rounded.Cameraswitch, stringResource(R.string.switch_camera)) }
                MotionIconButton(onClick = { if (state.cameraRunning) viewModel.stopCamera() else viewModel.startCamera(owner, preview.surfaceProvider) }, enabled = permission) {
                    Icon(if (state.cameraRunning) Icons.Rounded.Stop else Icons.Rounded.PlayArrow, stringResource(if (state.cameraRunning) R.string.stop else R.string.start))
                }
                MotionIconButton(onClick = viewModel::resetWorkout) { Icon(Icons.Rounded.Refresh, stringResource(R.string.reset)) }
            }
            state.cameraError?.let { Text(stringResource(R.string.camera_error), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error, modifier = Modifier.align(Alignment.TopCenter).background(Color.Black).padding(12.dp)) }
        }
    }
    val informationContent: @Composable (Modifier) -> Unit = { modifier ->
        Column(modifier, verticalArrangement = Arrangement.spacedBy(12.dp)) {
            ElevatedCard(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(stringResource(R.string.live_coaching), style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                    Text(feedbackText(state.result.feedback), style = MaterialTheme.typography.titleMedium)
                }
            }
            ElevatedCard(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(stringResource(R.string.target_progress, state.result.count.coerceAtMost(state.settings.targetReps), state.settings.targetReps))
                    LinearProgressIndicator(progress = { progress }, modifier = Modifier.fillMaxWidth(), color = Success)
                    Text(stringResource(R.string.form_value, state.result.formScore), color = if (state.result.postureValid) Success else MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            if (state.settings.debugMode) DebugOverlay(state, Modifier.fillMaxWidth())
        }
    }

    val exercisePicker: @Composable (Modifier) -> Unit = { modifier ->
        LazyRow(modifier, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(ExerciseType.entries) { exercise ->
                FilterChip(selected = state.exercise == exercise, onClick = { viewModel.selectExercise(exercise) }, label = { Text(exerciseName(exercise)) }, modifier = Modifier.heightIn(min = 48.dp))
            }
        }
    }
    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
            Text(stringResource(R.string.workout), style = MaterialTheme.typography.headlineMedium)
            if (wide) exercisePicker(Modifier.widthIn(max = 280.dp))
            else Text(stringResource(if (state.cameraRunning) R.string.camera_active else R.string.camera_stopped), color = if (state.cameraRunning) Success else MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp)
        }
        if (!wide) exercisePicker(Modifier.fillMaxWidth())
        BoxWithConstraints(Modifier.weight(1f).fillMaxWidth()) {
            if (maxWidth >= 600.dp) {
                Row(Modifier.fillMaxSize(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    cameraContent(Modifier.weight(1f).fillMaxHeight())
                    informationContent(Modifier.width(248.dp).verticalScroll(rememberScrollState()))
                }
            } else {
                val cameraHeight = (maxHeight * .68f).coerceAtLeast(280.dp)
                Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    cameraContent(Modifier.fillMaxWidth().height(cameraHeight))
                    informationContent(Modifier.fillMaxWidth())
                }
            }
        }
    }
}
