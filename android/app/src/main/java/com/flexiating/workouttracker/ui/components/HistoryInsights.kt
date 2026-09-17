package com.flexiating.workouttracker.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.unit.dp
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.data.local.WorkoutSessionEntity
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/** Read-only summaries of existing sessions; no database or workout changes. */
@Composable
fun HistoryInsights(sessions: List<WorkoutSessionEntity>) {
    val today = LocalDate.now()
    val totals = remember(sessions, today) {
        sessions.groupBy { Instant.ofEpochMilli(it.dateEpochMs).atZone(ZoneId.systemDefault()).toLocalDate() }
            .mapValues { (_, values) -> values.sumOf { it.reps } }
    }
    val days = (6L downTo 0L).map { today.minusDays(it) }
    val peak = days.maxOf { totals[it] ?: 0 }.coerceAtLeast(1)
    var streak = 0
    var day = if (totals.containsKey(today)) today else today.minusDays(1)
    while (totals.containsKey(day)) { streak++; day = day.minusDays(1) }
    val best = sessions.maxOfOrNull { it.reps } ?: 0
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        ElevatedCard(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(20.dp)) {
                Text(stringResource(R.string.weekly_activity), style = MaterialTheme.typography.titleSmall)
                Row(Modifier.fillMaxWidth().height(120.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    days.forEach { date ->
                        val reps = totals[date] ?: 0
                        val fraction by animateFloatAsState(reps.toFloat() / peak, tween(200), label = "daily activity")
                        Column(Modifier.weight(1f).fillMaxHeight(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Bottom) {
                            Text(reps.toString(), style = MaterialTheme.typography.labelSmall)
                            Spacer(Modifier.height(4.dp))
                            Box(Modifier.width(16.dp).height((60 * fraction).coerceAtLeast(3f).dp).background(MaterialTheme.colorScheme.primary, RoundedCornerShape(4.dp)))
                            Spacer(Modifier.height(8.dp))
                            Text(date.format(DateTimeFormatter.ofPattern("dd/MM")), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Insight(stringResource(R.string.personal_best), pluralStringResource(R.plurals.reps_short, best, best), Modifier.weight(1f))
            Insight(stringResource(R.string.current_streak), pluralStringResource(R.plurals.streak_days, streak, streak), Modifier.weight(1f))
        }
    }
}

@Composable
private fun Insight(title: String, value: String, modifier: Modifier) {
    ElevatedCard(modifier) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(title, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value, style = MaterialTheme.typography.titleLarge)
        }
    }
}
