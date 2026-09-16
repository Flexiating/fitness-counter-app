package com.flexiating.workouttracker.ui.screens

import androidx.annotation.StringRes
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.unit.dp
import com.flexiating.workouttracker.BuildConfig
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.viewmodel.SettingsViewModel

@Composable
fun SettingsScreen(viewModel: SettingsViewModel) {
    val settings by viewModel.settings.collectAsState()
    LazyColumn(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        item { Text(stringResource(R.string.settings), style = MaterialTheme.typography.headlineMedium); Spacer(Modifier.height(10.dp)) }
        item { SectionTitle(R.string.appearance) }
        item { SettingSwitch(R.string.dark_mode, R.string.dark_mode_description, settings.darkMode) { viewModel.update { s -> s.copy(darkMode = it) } } }
        item { LanguageSetting(settings.language) { value -> viewModel.update { it.copy(language = value) } } }
        item { SectionTitle(R.string.camera) }
        item { SettingSwitch(R.string.front_camera, R.string.front_camera_description, settings.useFrontCamera) { viewModel.update { s -> s.copy(useFrontCamera = it) } } }
        item { FpsSetting(settings.targetFps) { value -> viewModel.update { it.copy(targetFps = value) } } }
        item { SettingSwitch(R.string.show_fps, R.string.show_fps_description, settings.showFps) { viewModel.update { s -> s.copy(showFps = it) } } }
        item { SectionTitle(R.string.ai) }
        item { TargetSetting(settings.targetReps) { value -> viewModel.update { it.copy(targetReps = value) } } }
        item { SettingSwitch(R.string.debug_overlay, R.string.debug_overlay_description, settings.debugMode) { viewModel.update { s -> s.copy(debugMode = it) } } }
        item { SettingSwitch(R.string.rep_sound, R.string.rep_sound_description, settings.soundEnabled) { viewModel.update { s -> s.copy(soundEnabled = it) } } }
        item { SettingSwitch(R.string.vibration, R.string.vibration_description, settings.vibrationEnabled) { viewModel.update { s -> s.copy(vibrationEnabled = it) } } }
        item { SectionTitle(R.string.about) }
        item {
            ElevatedCard(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(stringResource(R.string.about_description), color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodySmall)
                    Text("${stringResource(R.string.version)}: ${BuildConfig.VERSION_NAME}")
                    Text("${stringResource(R.string.build_number)}: ${BuildConfig.VERSION_CODE}")
                }
            }
        }
    }
}

@Composable private fun SectionTitle(@StringRes title: Int) {
    Text(stringResource(title), style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary, modifier = Modifier.padding(top = 10.dp))
}

@Composable private fun SettingSwitch(@StringRes title: Int, @StringRes description: Int, checked: Boolean, onChange: (Boolean) -> Unit) {
    ElevatedCard(Modifier.fillMaxWidth()) { Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) { Text(stringResource(title)); Text(stringResource(description), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        Switch(checked, onChange)
    } }
}

@Composable private fun FpsSetting(value: Int, onChange: (Int) -> Unit) {
    ChoiceSetting(R.string.target_fps, R.string.target_fps_description, stringResource(R.string.fps_value, value), listOf(24, 30, 60), onChange) {
        stringResource(R.string.fps_value, it)
    }
}

@Composable private fun TargetSetting(value: Int, onChange: (Int) -> Unit) {
    ChoiceSetting(R.string.target_reps, R.string.target_reps_description, pluralStringResource(R.plurals.target_reps_value, value, value), listOf(5, 10, 15, 20, 30, 50), onChange) {
        pluralStringResource(R.plurals.target_reps_value, it, it)
    }
}

@Composable
private fun ChoiceSetting(@StringRes title: Int, @StringRes description: Int, valueLabel: String, choices: List<Int>, onChange: (Int) -> Unit, label: @Composable (Int) -> String) {
    var expanded by remember { mutableStateOf(false) }
    ElevatedCard(Modifier.fillMaxWidth()) { Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) { Text(stringResource(title)); Text(stringResource(description), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        Box { OutlinedButton(onClick = { expanded = true }) { Text(valueLabel) }; DropdownMenu(expanded, { expanded = false }) {
            choices.forEach { choice -> DropdownMenuItem({ Text(label(choice)) }, onClick = { onChange(choice); expanded = false }) }
        } }
    } }
}

@Composable private fun LanguageSetting(value: String, onChange: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    val current = stringResource(if (value == "vi") R.string.vietnamese else R.string.english)
    ElevatedCard(Modifier.fillMaxWidth()) { Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) { Text(stringResource(R.string.language)); Text(stringResource(R.string.language_description), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        Box { OutlinedButton(onClick = { expanded = true }) { Text(current) }; DropdownMenu(expanded, { expanded = false }) {
            DropdownMenuItem({ Text(stringResource(R.string.english)) }, onClick = { onChange("en"); expanded = false })
            DropdownMenuItem({ Text(stringResource(R.string.vietnamese)) }, onClick = { onChange("vi"); expanded = false })
        } }
    } }
}
