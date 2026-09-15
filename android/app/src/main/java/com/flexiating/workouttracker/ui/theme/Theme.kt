package com.flexiating.workouttracker.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

val AppBackground = Color(0xFF0B0F14)
val AppSurface = Color(0xFF151B23)
val AppCard = Color(0xFF1D2631)
val Accent = Color(0xFF3B82F6)
val Success = Color(0xFF22C55E)
val Warning = Color(0xFFF59E0B)
val Danger = Color(0xFFEF4444)

private val DarkColors = darkColorScheme(
    primary = Accent, secondary = Color(0xFF38BDF8), tertiary = Success,
    background = AppBackground, surface = AppSurface, surfaceVariant = AppCard,
    onPrimary = Color.White, onBackground = Color(0xFFF8FAFC), onSurface = Color(0xFFF8FAFC)
)

private val LightColors = lightColorScheme(
    primary = Color(0xFF2563EB), secondary = Color(0xFF0284C7), tertiary = Color(0xFF16A34A),
    background = Color(0xFFF1F5F9), surface = Color.White, surfaceVariant = Color(0xFFE2E8F0)
)

@Composable
fun WorkoutTrackerTheme(darkTheme: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (darkTheme) DarkColors else LightColors,
        typography = Typography(), shapes = Shapes(
            extraSmall = androidx.compose.foundation.shape.RoundedCornerShape(8.dp),
            small = androidx.compose.foundation.shape.RoundedCornerShape(12.dp),
            medium = androidx.compose.foundation.shape.RoundedCornerShape(16.dp),
            large = androidx.compose.foundation.shape.RoundedCornerShape(24.dp)
        ), content = content)
}
