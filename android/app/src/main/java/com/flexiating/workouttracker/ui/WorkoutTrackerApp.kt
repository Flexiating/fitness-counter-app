package com.flexiating.workouttracker.ui

import android.content.Context
import android.content.ContextWrapper
import android.content.res.Configuration
import androidx.annotation.StringRes
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.FitnessCenter
import androidx.compose.material.icons.rounded.History
import androidx.compose.material.icons.automirrored.rounded.MenuBook
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material3.*
import androidx.compose.foundation.layout.padding
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.flexiating.workouttracker.R
import com.flexiating.workouttracker.ui.screens.*
import com.flexiating.workouttracker.ui.theme.WorkoutTrackerTheme
import com.flexiating.workouttracker.viewmodel.SettingsViewModel
import java.util.Locale

private data class Destination(val route: String, @param:StringRes val title: Int, val icon: androidx.compose.ui.graphics.vector.ImageVector)

/**
 * Keeps the Activity in the context chain so Hilt can resolve ViewModels, while
 * exposing resources configured for the selected app language.
 */
private class LocalizedResourcesContext(
    base: Context,
    private val localizedContext: Context,
) : ContextWrapper(base) {
    override fun getResources() = localizedContext.resources
    override fun getTheme() = localizedContext.theme
}

@Composable
fun WorkoutTrackerApp(settingsViewModel: SettingsViewModel = hiltViewModel()) {
    val settings by settingsViewModel.settings.collectAsState()
    val baseContext = LocalContext.current
    val baseConfiguration = LocalConfiguration.current
    val localizedConfiguration = remember(settings.language, baseConfiguration) {
        Configuration(baseConfiguration).apply { setLocale(Locale.forLanguageTag(settings.language)) }
    }
    val localizedContext = remember(settings.language, baseContext, localizedConfiguration) {
        baseContext.createConfigurationContext(localizedConfiguration)
    }
    val localizedResourcesContext = remember(baseContext, localizedContext) {
        LocalizedResourcesContext(baseContext, localizedContext)
    }
    CompositionLocalProvider(
        LocalContext provides localizedResourcesContext,
        LocalConfiguration provides localizedConfiguration,
    ) {
        WorkoutTrackerTheme(settings.darkMode) {
            val nav = rememberNavController()
            val items = listOf(
                Destination("workout", R.string.workout, Icons.Rounded.FitnessCenter),
                Destination("history", R.string.history, Icons.Rounded.History),
                Destination("guide", R.string.guide, Icons.AutoMirrored.Rounded.MenuBook),
                Destination("settings", R.string.settings, Icons.Rounded.Settings),
            )
            Scaffold(bottomBar = {
                NavigationBar {
                    val entry by nav.currentBackStackEntryAsState()
                    items.forEach { destination ->
                        NavigationBarItem(
                            selected = entry?.destination?.route == destination.route,
                            onClick = { nav.navigate(destination.route) { launchSingleTop = true; popUpTo("workout") { saveState = true }; restoreState = true } },
                            icon = { Icon(destination.icon, contentDescription = stringResource(destination.title)) },
                            label = { Text(stringResource(destination.title)) },
                        )
                    }
                }
            }) { padding ->
                NavHost(navController = nav, startDestination = "workout", modifier = Modifier.padding(padding)) {
                    composable("workout") { WorkoutScreen() }
                    composable("history") { HistoryScreen(onSessionClick = { nav.navigate("history/$it") }) }
                    composable("history/{sessionId}") { entry ->
                        SessionDetailScreen(
                            sessionId = entry.arguments?.getString("sessionId")?.toLongOrNull() ?: 0L,
                            onBack = { nav.popBackStack() },
                        )
                    }
                    composable("guide") { GuideScreen() }
                    composable("settings") { SettingsScreen(settingsViewModel) }
                }
            }
        }
    }
}
