package com.flexiating.workouttracker.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowBack
import androidx.compose.material.icons.rounded.Delete
import androidx.compose.material.icons.rounded.DeleteSweep
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.data.local.WorkoutSessionEntity
import com.flexiating.workouttracker.model.ExerciseType
import com.flexiating.workouttracker.ui.exerciseName
import com.flexiating.workouttracker.viewmodel.HistoryViewModel
import java.text.DateFormat
import java.text.SimpleDateFormat
import java.util.*

@Composable
fun HistoryScreen(onSessionClick: (Long) -> Unit, viewModel: HistoryViewModel = hiltViewModel()) {
    val sessions by viewModel.sessions.collectAsState()
    var query by remember { mutableStateOf("") }
    var exercise by remember { mutableStateOf<ExerciseType?>(null) }
    var filterOpen by remember { mutableStateOf(false) }
    var confirmClear by remember { mutableStateOf(false) }
    val dateFormat = remember { SimpleDateFormat("yyyy-MM-dd", Locale.US) }
    val filtered = sessions.filter { session ->
        (query.isBlank() || dateFormat.format(Date(session.dateEpochMs)).contains(query.trim(), ignoreCase = true)) &&
            (exercise == null || session.exercise == exercise!!.name)
    }

    if (confirmClear) ConfirmDeleteDialog(
        message = stringResource(R.string.delete_all_question),
        onConfirm = { viewModel.clear(); confirmClear = false },
        onDismiss = { confirmClear = false },
    )

    Column(Modifier.fillMaxSize().padding(20.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text(stringResource(R.string.history_title), style = MaterialTheme.typography.headlineMedium)
            IconButton(onClick = { confirmClear = true }, enabled = sessions.isNotEmpty()) {
                Icon(Icons.Rounded.DeleteSweep, stringResource(R.string.clear_history))
            }
        }
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            value = query, onValueChange = { query = it }, modifier = Modifier.fillMaxWidth(),
            label = { Text(stringResource(R.string.search_date)) }, singleLine = true,
        )
        Spacer(Modifier.height(8.dp))
        Box {
            OutlinedButton(onClick = { filterOpen = true }) {
                Text(exercise?.let { exerciseName(it) } ?: stringResource(R.string.all_exercises))
            }
            DropdownMenu(expanded = filterOpen, onDismissRequest = { filterOpen = false }) {
                DropdownMenuItem(text = { Text(stringResource(R.string.all_exercises)) }, onClick = { exercise = null; filterOpen = false })
                ExerciseType.entries.forEach { type ->
                    DropdownMenuItem(text = { Text(exerciseName(type)) }, onClick = { exercise = type; filterOpen = false })
                }
            }
        }
        Spacer(Modifier.height(12.dp))
        if (filtered.isEmpty()) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text(stringResource(R.string.history_empty), color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        } else LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(filtered, key = { it.id }) { session ->
                ElevatedCard(Modifier.fillMaxWidth().clickable { onSessionClick(session.id) }) {
                    Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                        Column {
                            Text(exerciseName(ExerciseType.valueOf(session.exercise)), fontWeight = FontWeight.Bold)
                            Text(DateFormat.getDateTimeInstance().format(Date(session.dateEpochMs)), style = MaterialTheme.typography.bodySmall)
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            Text(pluralStringResource(R.plurals.reps_short, session.reps, session.reps), fontWeight = FontWeight.Bold)
                            Text(stringResource(R.string.duration_form, formatDuration(session.durationMs), session.averageFormScore.toInt()), style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun SessionDetailScreen(sessionId: Long, onBack: () -> Unit, viewModel: HistoryViewModel = hiltViewModel()) {
    val session by viewModel.session(sessionId).collectAsState(initial = null)
    var confirmDelete by remember { mutableStateOf(false) }
    if (confirmDelete) ConfirmDeleteDialog(
        message = stringResource(R.string.delete_session_question),
        onConfirm = { viewModel.delete(sessionId); confirmDelete = false; onBack() },
        onDismiss = { confirmDelete = false },
    )
    Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Rounded.ArrowBack, stringResource(R.string.back)) }
            Text(stringResource(R.string.session_details), style = MaterialTheme.typography.headlineMedium, modifier = Modifier.weight(1f))
            IconButton(onClick = { confirmDelete = true }, enabled = session != null) { Icon(Icons.Rounded.Delete, stringResource(R.string.delete_session)) }
        }
        session?.let { item -> SessionDetails(item) }
    }
}

@Composable
private fun SessionDetails(session: WorkoutSessionEntity) {
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            DetailRow(stringResource(R.string.date), DateFormat.getDateInstance().format(Date(session.dateEpochMs)))
            DetailRow(stringResource(R.string.start_time), DateFormat.getTimeInstance().format(Date(session.dateEpochMs)))
            DetailRow(stringResource(R.string.end_time), DateFormat.getTimeInstance().format(Date(session.endEpochMs)))
            DetailRow(stringResource(R.string.exercise), exerciseName(ExerciseType.valueOf(session.exercise)))
            DetailRow(stringResource(R.string.total_reps), session.reps.toString())
            DetailRow(stringResource(R.string.duration), formatDuration(session.durationMs))
            DetailRow(stringResource(R.string.average_posture), "${session.averageFormScore.toInt()}%")
            DetailRow(stringResource(R.string.average_tracking), "${(session.averageTrackingConfidence * 100).toInt()}%")
            DetailRow(stringResource(R.string.average_fps), String.format(Locale.US, "%.1f", session.averageFps))
            DetailRow(stringResource(R.string.target_reached), stringResource(if (session.targetReached) R.string.yes else R.string.no))
        }
    }
}

@Composable private fun DetailRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant); Text(value, fontWeight = FontWeight.SemiBold)
    }
}

@Composable private fun ConfirmDeleteDialog(message: String, onConfirm: () -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.confirm_delete)) }, text = { Text(message) },
        confirmButton = { TextButton(onClick = onConfirm) { Text(stringResource(R.string.delete)) } },
        dismissButton = { TextButton(onClick = onDismiss) { Text(stringResource(R.string.cancel)) } },
    )
}

private fun formatDuration(durationMs: Long): String {
    val seconds = durationMs.coerceAtLeast(0L) / 1000
    return String.format(Locale.US, "%02d:%02d", seconds / 60, seconds % 60)
}
