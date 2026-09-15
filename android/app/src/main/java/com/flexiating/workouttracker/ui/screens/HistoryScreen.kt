package com.flexiating.workouttracker.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.DeleteSweep
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.flexiating.workouttracker.viewmodel.HistoryViewModel
import java.text.DateFormat
import java.util.*

@Composable
fun HistoryScreen(viewModel: HistoryViewModel = hiltViewModel()) {
    val sessions by viewModel.sessions.collectAsState()
    Column(Modifier.fillMaxSize().padding(20.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Workout history", style = MaterialTheme.typography.headlineMedium)
            IconButton(onClick = viewModel::clear, enabled = sessions.isNotEmpty()) { Icon(Icons.Rounded.DeleteSweep, "Clear history") }
        }
        Spacer(Modifier.height(16.dp))
        if (sessions.isEmpty()) Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("Your completed workouts will appear here", color = MaterialTheme.colorScheme.onSurfaceVariant) }
        else LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            items(sessions, key = { it.id }) { session ->
                ElevatedCard(Modifier.fillMaxWidth()) {
                    Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                        Column { Text(session.exercise.replace('_', ' '), fontWeight = FontWeight.Bold); Text(DateFormat.getDateTimeInstance().format(Date(session.dateEpochMs)), style = MaterialTheme.typography.bodySmall) }
                        Column(horizontalAlignment = Alignment.End) { Text("${session.reps} reps", fontWeight = FontWeight.Bold); Text("${session.durationMs / 1000}s • ${session.averageFormScore.toInt()}% form", style = MaterialTheme.typography.bodySmall) }
                    }
                }
            }
        }
    }
}

