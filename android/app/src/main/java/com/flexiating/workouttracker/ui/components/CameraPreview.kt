package com.flexiating.workouttracker.ui.components

import androidx.camera.view.PreviewView
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView

@Composable
fun CameraPreview(previewView: PreviewView, modifier: Modifier = Modifier) {
    AndroidView(factory = {
        previewView.apply {
            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
            scaleType = PreviewView.ScaleType.FIT_CENTER
        }
    }, modifier = modifier)
}

