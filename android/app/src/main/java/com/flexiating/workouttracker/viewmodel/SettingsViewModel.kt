package com.flexiating.workouttracker.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.flexiating.workouttracker.data.SettingsRepository
import com.flexiating.workouttracker.model.WorkoutSettings
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(private val repository: SettingsRepository) : ViewModel() {
    val settings: StateFlow<WorkoutSettings> = repository.settings.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), WorkoutSettings())
    fun update(transform: (WorkoutSettings) -> WorkoutSettings) { viewModelScope.launch { repository.update(transform(settings.value)) } }
}

