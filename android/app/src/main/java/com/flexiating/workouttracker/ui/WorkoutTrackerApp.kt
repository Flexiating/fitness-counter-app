package com.flexiating.workouttracker.ui

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.FitnessCenter
import androidx.compose.material.icons.rounded.History
import androidx.compose.material.icons.rounded.MenuBook
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material3.*
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.flexiating.workouttracker.ui.screens.*
import com.flexiating.workouttracker.ui.theme.WorkoutTrackerTheme
import com.flexiating.workouttracker.viewmodel.SettingsViewModel

private data class Destination(val route: String, val title: String, val icon: androidx.compose.ui.graphics.vector.ImageVector)

@Composable
fun WorkoutTrackerApp(settingsViewModel: SettingsViewModel = hiltViewModel()) {
    val settings by settingsViewModel.settings.collectAsState()
    WorkoutTrackerTheme(settings.darkMode) {
        val nav = rememberNavController()
        val items = listOf(
            Destination("workout", "Workout", Icons.Rounded.FitnessCenter),
            Destination("history", "History", Icons.Rounded.History),
            Destination("guide", "Guide", Icons.Rounded.MenuBook),
            Destination("settings", "Settings", Icons.Rounded.Settings)
        )
        Scaffold(bottomBar = {
            NavigationBar {
                val entry by nav.currentBackStackEntryAsState()
                items.forEach { destination ->
                    NavigationBarItem(selected = entry?.destination?.route == destination.route,
                        onClick = { nav.navigate(destination.route) { launchSingleTop = true; popUpTo("workout") { saveState = true }; restoreState = true } },
                        icon = { Icon(destination.icon, null) }, label = { Text(destination.title) })
                }
            }
        }) { padding ->
            NavHost(navController = nav, startDestination = "workout", modifier = Modifier.padding(padding)) {
                composable("workout") { WorkoutScreen() }
                composable("history") { HistoryScreen() }
                composable("guide") { GuideScreen() }
                composable("settings") { SettingsScreen(settingsViewModel) }
            }
        }
    }
}
