package com.flexiating.workouttracker.ui

import androidx.annotation.StringRes
import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.model.ExercisePhase
import com.flexiating.workouttracker.model.ExerciseType

@StringRes
fun exerciseNameResource(type: ExerciseType): Int = when (type) {
    ExerciseType.PUSH_UP -> R.string.push_up
    ExerciseType.CRUNCH -> R.string.crunch
}

@Composable
fun exerciseName(type: ExerciseType): String = stringResource(exerciseNameResource(type))

@Composable
fun phaseName(phase: ExercisePhase): String = stringResource(when (phase) {
    ExercisePhase.WAITING -> R.string.phase_waiting
    ExercisePhase.READY -> R.string.phase_ready
    ExercisePhase.UP -> R.string.phase_up
    ExercisePhase.DOWN -> R.string.phase_down
})

@Composable
fun feedbackText(key: String): String = stringResource(when (key) {
    "ready" -> R.string.feedback_ready
    "show_full_body_arms" -> R.string.feedback_show_full_body_arms
    "low_visibility" -> R.string.feedback_low_visibility
    "pushup_position" -> R.string.feedback_pushup_position
    "hips_aligned" -> R.string.feedback_hips_aligned
    "straighten_legs" -> R.string.feedback_straighten_legs
    "push_back_up" -> R.string.feedback_push_back_up
    "lower_chest" -> R.string.feedback_lower_chest
    "crunch_sideways" -> R.string.feedback_crunch_sideways
    "crunch_landmarks_missing" -> R.string.feedback_crunch_landmarks_missing
    "lie_down" -> R.string.feedback_lie_down
    "avoid_twisting" -> R.string.feedback_avoid_twisting
    "extend_torso" -> R.string.feedback_extend_torso
    "neutral_neck" -> R.string.feedback_neutral_neck
    "lower_shoulders" -> R.string.feedback_lower_shoulders
    "lift_shoulders" -> R.string.feedback_lift_shoulders
    "starting_position" -> R.string.feedback_starting_position
    else -> R.string.feedback_move_into_frame
})
