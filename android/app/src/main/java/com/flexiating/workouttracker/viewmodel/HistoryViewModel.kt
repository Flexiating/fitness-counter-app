package com.flexiating.workouttracker.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.flexiating.workouttracker.data.local.WorkoutRepository
import com.flexiating.workouttracker.data.local.WorkoutSessionEntity
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HistoryViewModel @Inject constructor(private val repository: WorkoutRepository) : ViewModel() {
    val sessions: StateFlow<List<WorkoutSessionEntity>> = repository.sessions.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    fun session(id: Long): Flow<WorkoutSessionEntity?> = repository.session(id)
    fun delete(id: Long) { viewModelScope.launch { repository.delete(id) } }
    fun clear() { viewModelScope.launch { repository.clear() } }
}
