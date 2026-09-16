package com.flexiating.workouttracker.ui.screens

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.model.ExerciseType
import com.flexiating.workouttracker.ui.exerciseName

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
    LazyColumn(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { Text(stringResource(R.string.exercise_guide), style = MaterialTheme.typography.headlineMedium) }
        item {
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                ExerciseType.entries.forEachIndexed { index, type ->
                    SegmentedButton(selected = selected == type, onClick = { selected = type }, shape = SegmentedButtonDefaults.itemShape(index, ExerciseType.entries.size)) {
                        Text(exerciseName(type))
                    }
                }
            }
        }
        item { GuideCard(guide.firstTitle, guide.firstBody) }
        item { GuideCard(guide.secondTitle, guide.secondBody) }
        item { GuideCard(R.string.common_mistakes, guide.mistakes) }
        item { GuideCard(R.string.tips, guide.tips) }
    }
}

@Composable private fun GuideCard(@StringRes title: Int, @StringRes body: Int) {
    ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(18.dp)) {
        Text(stringResource(title), fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(8.dp)); Text(stringResource(body))
    } }
}
