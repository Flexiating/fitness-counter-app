package com.flexiating.workouttracker.ui.theme

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.platform.LocalView
import android.app.Activity
import androidx.core.view.WindowCompat
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

val AppBackground = Color(0xFF0F1115)
val AppSurface = Color(0xFF171A21)
val AppCard = Color(0xFF232832)
val Accent = Color(0xFF2D8CFF)
val Success = Color(0xFF32D583)
val Warning = Color(0xFFF59E0B)
val Danger = Color(0xFFF04438)

private val DarkColors = darkColorScheme(
    primary = Accent, secondary = Accent, tertiary = Success, error = Danger,
    background = AppBackground, surface = AppSurface, surfaceVariant = AppCard,
    onPrimary = Color(0xFF081A30), onBackground = Color(0xFFF5F7FA), onSurface = Color(0xFFF5F7FA),
    onSurfaceVariant = Color(0xFFA9B4C4), outline = Color(0xFF526074),
    surfaceContainer = AppSurface, surfaceContainerLow = AppSurface,
    surfaceContainerHigh = AppCard, secondaryContainer = Color(0xFF183657),
    onSecondaryContainer = Color(0xFFB4D6FF)
)

@Composable
fun WorkoutTrackerTheme(content: @Composable () -> Unit) {
    val view = LocalView.current
    if (!view.isInEditMode) SideEffect {
        (view.context as? Activity)?.window?.let { window ->
            WindowCompat.getInsetsController(window, view).apply {
                isAppearanceLightStatusBars = false
                isAppearanceLightNavigationBars = false
            }
        }
    }
    MaterialTheme(colorScheme = DarkColors,
        typography = Typography(), shapes = Shapes(
            extraSmall = androidx.compose.foundation.shape.RoundedCornerShape(8.dp),
            small = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
            medium = androidx.compose.foundation.shape.RoundedCornerShape(16.dp),
            large = androidx.compose.foundation.shape.RoundedCornerShape(18.dp)
        ), content = content)
}
