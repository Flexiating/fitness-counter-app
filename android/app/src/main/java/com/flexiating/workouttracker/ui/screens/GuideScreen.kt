package com.flexiating.workouttracker.ui.screens

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.tween
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.ExpandMore
import androidx.compose.material.icons.rounded.ExpandLess
import androidx.compose.ui.Alignment
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.model.ExerciseType
import com.flexiating.workouttracker.ui.exerciseName
import com.flexiating.workouttracker.ui.components.ExerciseIllustration

private data class GuideResources(
    @param:StringRes val firstTitle: Int, @param:StringRes val firstBody: Int,
    @param:StringRes val secondTitle: Int, @param:StringRes val secondBody: Int,
    @param:StringRes val mistakes: Int, @param:StringRes val tips: Int,
)

private val guides = mapOf(
    ExerciseType.PUSH_UP to GuideResources(R.string.starting_position, R.string.pushup_start, R.string.ending_position, R.string.pushup_end, R.string.pushup_mistakes, R.string.pushup_tips),
    ExerciseType.CRUNCH to GuideResources(R.string.correct_posture, R.string.crunch_posture, R.string.range_of_motion, R.string.crunch_range, R.string.crunch_mistakes, R.string.crunch_tips),
)

@Composable
fun GuideScreen() {
    var selected by remember { mutableStateOf(ExerciseType.PUSH_UP) }
    val guide = guides.getValue(selected)
    val selector: @Composable () -> Unit = {
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
            ExerciseType.entries.forEachIndexed { index, type ->
                SegmentedButton(selected = selected == type, onClick = { selected = type }, modifier = Modifier.heightIn(min = 48.dp), shape = SegmentedButtonDefaults.itemShape(index, ExerciseType.entries.size)) {
                    Text(exerciseName(type))
                }
            }
        }
    }
    val cards = listOf(guide.firstTitle to guide.firstBody, guide.secondTitle to guide.secondBody, R.string.common_mistakes to guide.mistakes, R.string.tips to guide.tips)
    BoxWithConstraints(Modifier.fillMaxSize().padding(20.dp)) {
        if (maxWidth >= 580.dp) Row(Modifier.fillMaxSize(), horizontalArrangement = Arrangement.spacedBy(20.dp)) {
            Column(Modifier.width(240.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text(stringResource(R.string.exercise_guide), style = MaterialTheme.typography.headlineSmall)
                selector()
                ExerciseIllustration(selected)
            }
            LazyColumn(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                cards.forEach { (title, body) -> item(key = title) { GuideCard(title, body) } }
            }
        } else LazyColumn(Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            item { Text(stringResource(R.string.exercise_guide), style = MaterialTheme.typography.headlineMedium) }
            item { selector() }
            item { ExerciseIllustration(selected) }
            cards.forEach { (title, body) -> item(key = title) { GuideCard(title, body) } }
        }
    }
}

@Composable private fun GuideCard(@StringRes title: Int, @StringRes body: Int) {
    var expanded by rememberSaveable(title) { mutableStateOf(true) }
    ElevatedCard(onClick = { expanded = !expanded }, modifier = Modifier.fillMaxWidth().animateContentSize(tween(200))) {
        Column(Modifier.padding(20.dp)) {
            Row(Modifier.fillMaxWidth().heightIn(min = 48.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(stringResource(title), fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f))
                Icon(if (expanded) Icons.Rounded.ExpandLess else Icons.Rounded.ExpandMore, contentDescription = null)
            }
            AnimatedVisibility(expanded) { Text(stringResource(body), color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 8.dp)) }
        }
    }
}
