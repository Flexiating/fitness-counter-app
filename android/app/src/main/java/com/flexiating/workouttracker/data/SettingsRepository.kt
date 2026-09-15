package com.flexiating.workouttracker.data

import android.content.Context
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import com.flexiating.workouttracker.model.WorkoutSettings
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.settingsStore by preferencesDataStore("workout_settings")

@Singleton
class SettingsRepository @Inject constructor(@param:ApplicationContext private val context: Context) {
    private object Keys {
        val dark = booleanPreferencesKey("dark")
        val front = booleanPreferencesKey("front")
        val fps = intPreferencesKey("fps")
        val showFps = booleanPreferencesKey("show_fps")
        val debug = booleanPreferencesKey("debug")
        val sound = booleanPreferencesKey("sound")
        val vibration = booleanPreferencesKey("vibration")
        val language = stringPreferencesKey("language")
    }

    val settings: Flow<WorkoutSettings> = context.settingsStore.data.map { p ->
        WorkoutSettings(
            darkMode = p[Keys.dark] ?: true,
            useFrontCamera = p[Keys.front] ?: true,
            targetFps = p[Keys.fps] ?: 30,
            showFps = p[Keys.showFps] ?: true,
            debugMode = p[Keys.debug] ?: false,
            soundEnabled = p[Keys.sound] ?: true,
            vibrationEnabled = p[Keys.vibration] ?: true,
            language = p[Keys.language] ?: "English"
        )
    }

    suspend fun update(value: WorkoutSettings) = context.settingsStore.edit {
        it[Keys.dark] = value.darkMode; it[Keys.front] = value.useFrontCamera; it[Keys.fps] = value.targetFps
        it[Keys.showFps] = value.showFps
        it[Keys.debug] = value.debugMode; it[Keys.sound] = value.soundEnabled
        it[Keys.vibration] = value.vibrationEnabled; it[Keys.language] = value.language
    }
}
