package com.flexiating.workouttracker.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.flexiating.workouttracker.viewmodel.SettingsViewModel

@Composable
fun SettingsScreen(viewModel: SettingsViewModel) {
    val settings by viewModel.settings.collectAsState()
    LazyColumn(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item { Text("Settings", style = MaterialTheme.typography.headlineMedium); Spacer(Modifier.height(10.dp)) }
        item { SettingSwitch("Dark mode", "Use the dark fitness theme", settings.darkMode) { viewModel.update { s -> s.copy(darkMode = it) } } }
        item { SettingSwitch("Front camera", "Mirror your movement like a workout studio", settings.useFrontCamera) { viewModel.update { s -> s.copy(useFrontCamera = it) } } }
        item { FpsSetting(settings.targetFps) { value -> viewModel.update { it.copy(targetFps = value) } } }
        item { SettingSwitch("Show FPS", "Display live camera processing speed", settings.showFps) { viewModel.update { s -> s.copy(showFps = it) } } }
        item { SettingSwitch("Debug overlay", "Show detector, angles and rejection details", settings.debugMode) { viewModel.update { s -> s.copy(debugMode = it) } } }
        item { SettingSwitch("Rep sound", "Play a short sound for accepted repetitions", settings.soundEnabled) { viewModel.update { s -> s.copy(soundEnabled = it) } } }
        item { SettingSwitch("Vibration", "Vibrate briefly for accepted repetitions", settings.vibrationEnabled) { viewModel.update { s -> s.copy(vibrationEnabled = it) } } }
        item { LanguageSetting(settings.language) { value -> viewModel.update { it.copy(language = value) } } }
        item { Spacer(Modifier.height(20.dp)); Text("Workout Tracker for Android\nCamera frames are processed on your device.", color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall) }
    }
}

@Composable private fun SettingSwitch(title: String, description: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    ElevatedCard(Modifier.fillMaxWidth()) { Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) { Text(title); Text(description, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        Switch(checked, onChange)
    } }
}

@Composable private fun FpsSetting(value: Int, onChange: (Int) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    ElevatedCard(Modifier.fillMaxWidth()) { Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) { Text("Target FPS"); Text("Camera analysis preference", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        Box { OutlinedButton(onClick = { expanded = true }) { Text("$value FPS") }; DropdownMenu(expanded, { expanded = false }) {
            listOf(24, 30, 60).forEach { fps -> DropdownMenuItem({ Text("$fps FPS") }, onClick = { onChange(fps); expanded = false }) }
        } }
    } }
}

@Composable private fun LanguageSetting(value: String, onChange: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    ElevatedCard(Modifier.fillMaxWidth()) { Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) { Text("Language"); Text("App display language", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        Box { OutlinedButton(onClick = { expanded = true }) { Text(value) }; DropdownMenu(expanded, { expanded = false }) {
            listOf("English", "Tiếng Việt").forEach { language -> DropdownMenuItem({ Text(language) }, onClick = { onChange(language); expanded = false }) }
        } }
    } }
}
