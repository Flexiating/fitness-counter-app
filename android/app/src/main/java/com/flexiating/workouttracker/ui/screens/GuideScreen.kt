package com.flexiating.workouttracker.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.flexiating.workouttracker.model.ExerciseType

private data class Guide(val setup: String, val movement: String, val mistakes: List<String>, val tips: List<String>)

private val guides = mapOf(
    ExerciseType.PUSH_UP to Guide("Place hands slightly wider than shoulders and form a straight line from head to heels.", "Lower your chest until elbows reach about 70–90°, then press to full extension.", listOf("Hips sagging or raised", "Partial elbow range", "Looking too far forward"), listOf("Brace your core", "Keep elbows about 45° from your body", "Move under control")),
    ExerciseType.CRUNCH to Guide("Lie on your back with knees bent and feet planted. Keep your hands light beside your head.", "Curl your shoulders toward your knees, then lower until your upper back returns to the floor.", listOf("Pulling the neck", "Sitting all the way up", "Using momentum"), listOf("Exhale while lifting", "Keep the lower back grounded", "Lead with your ribs")),
    ExerciseType.SQUAT to Guide("Stand with feet around shoulder width and toes slightly outward.", "Sit hips down and back until thighs approach parallel, then stand tall.", listOf("Knees collapsing inward", "Heels lifting", "Chest dropping"), listOf("Spread the floor with your feet", "Brace before descending", "Keep knees tracking over toes")),
    ExerciseType.PLANK to Guide("Set elbows below shoulders and extend both legs.", "Hold a straight, stable line while breathing normally.", listOf("Hips sagging", "Hips too high", "Holding your breath"), listOf("Squeeze glutes", "Push the floor away", "Keep your neck neutral")),
    ExerciseType.LUNGE to Guide("Take a split stance with both feet facing forward.", "Lower both knees, then press through the front foot to return.", listOf("Front knee collapsing inward", "Stance too narrow", "Leaning sideways"), listOf("Keep hips square", "Use a comfortable stride", "Move vertically"))
)

@Composable
fun GuideScreen() {
    var selected by remember { mutableStateOf(ExerciseType.PUSH_UP) }
    val guide = guides.getValue(selected)
    LazyColumn(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item { Text("Exercise guide", style = MaterialTheme.typography.headlineMedium) }
        item {
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                ExerciseType.entries.forEachIndexed { index, type ->
                    SegmentedButton(selected = selected == type, onClick = { selected = type }, shape = SegmentedButtonDefaults.itemShape(index, ExerciseType.entries.size)) { Text(type.title) }
                }
            }
        }
        item { GuideCard("Starting position", guide.setup) }
        item { GuideCard("Movement", guide.movement) }
        item { GuideCard("Common mistakes", guide.mistakes.joinToString("\n") { "• $it" }) }
        item { GuideCard("Tips", guide.tips.joinToString("\n") { "• $it" }) }
        item {
            ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(18.dp)) {
                Text("Animated demonstration", fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(10.dp))
                Box(Modifier.fillMaxWidth().height(140.dp), contentAlignment = androidx.compose.ui.Alignment.Center) { Text("Illustration coming soon", color = MaterialTheme.colorScheme.onSurfaceVariant) }
            } }
        }
        item { GuideCard("FAQ", "For best tracking, place your phone sideways with your full body visible and use even lighting. Wear clothing that contrasts with the background.") }
    }
}

@Composable private fun GuideCard(title: String, body: String) {
    ElevatedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(18.dp)) {
        Text(title, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        Spacer(Modifier.height(8.dp)); Text(body)
    } }
}

