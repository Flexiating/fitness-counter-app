# Workout Tracker — Android

This is the independent Android version of the AI Workout Tracker. It does not import or modify the desktop application.

## Requirements

- Android Studio with JDK 17 or newer
- Android SDK Platform 37 and Build Tools 37
- Either a physical Android device or an Android Studio emulator running Android 8.0 (API 26) or newer

## Open and run

1. Open Android Studio.
2. Choose **Open** and select this `android` folder (not the repository root).
3. Allow Gradle Sync to finish.
4. Connect an Android phone with USB debugging enabled.
5. Select the phone and press **Run**.
6. Grant camera permission when asked.

The first Gradle sync downloads dependencies. The MediaPipe pose model is bundled in `app/src/main/assets`, so the installed app performs inference fully on-device.

## Run without an Android phone (Android Studio Emulator)

You can run the complete app in an Android Virtual Device and use your computer's webcam as its camera.

### 1. Create a virtual phone

1. Open this `android` folder in Android Studio and wait for Gradle Sync to finish.
2. Open **View → Tool Windows → Device Manager**.
3. Click **+ → Create Virtual Device**.
4. Select a recent Pixel phone, such as **Pixel 8**, and click **Next**.
5. Select and download a stable Android system image with API 37 or newer.
   - On an Apple Silicon Mac, use an **ARM 64** image.
   - On an Intel/AMD Windows computer, use an **x86_64** image when offered.
6. On **Verify Configuration**, click **Show Advanced Settings**.
7. Under **Camera**, set **Front** to **Webcam0**. Set **Back** to **VirtualScene** or another available webcam.
8. Click **Finish**.

### 2. Start the emulator and app

1. In Device Manager, click the **Launch** button beside the virtual phone.
2. Wait until the Android home screen is fully loaded.
3. In the Android Studio device selector, choose the running virtual phone.
4. Click **Run ▶** or press **Control+R** on macOS / **Shift+F10** on Windows.
5. When Workout Tracker opens, select **Allow while using the app** for camera permission.
6. If the virtual scene appears, press the camera-switch button in Workout Tracker to select the webcam-facing camera.

### Camera permission on the computer

- **macOS:** Open **System Settings → Privacy & Security → Camera** and enable access for Android Studio and Android Emulator. Restart the emulator afterward.
- **Windows:** Open **Settings → Privacy & security → Camera** and enable camera access plus **Let desktop apps access your camera**.

### Emulator troubleshooting

- **Black camera:** Stop the emulator, open its menu in Device Manager, choose **Edit**, and confirm that Front Camera is `Webcam0`. Then choose **Cold Boot Now**.
- **Webcam is busy:** Close Zoom, Teams, Photo Booth, browser camera tabs, and other camera applications.
- **Camera option is missing:** Create a phone AVD rather than a TV, Wear OS, or Automotive AVD.
- **App is slow:** Enable hardware acceleration, reduce the AVD resolution, close other virtual devices, and select 24 FPS in Workout Tracker settings.
- **Permission was denied:** Open the emulator's **Settings → Apps → Workout Tracker → Permissions → Camera** and select **Allow only while using the app**.

Pose detection and CameraX run in the emulator, but camera FPS can be lower than on a physical phone because the webcam frame is processed through both the emulator and MediaPipe.

## Command-line build

macOS/Linux:

```bash
./gradlew test assembleDebug
```

Windows:

```bat
gradlew.bat test assembleDebug
```

The debug APK is created at `app/build/outputs/apk/debug/app-debug.apk`.

## Architecture

`CameraX → MediaPipe Pose → PoseFrame → selected detector → detector state machine → ViewModel → Compose UI`

- `camera/`: capture only
- `mediapipe/`: model execution and normalized landmark extraction only
- `detectors/`: independent exercise detectors implementing `BaseExerciseDetector`
- `data/`: Room history and DataStore settings
- `viewmodel/`: lifecycle-aware orchestration
- `ui/`: Compose screens, camera preview, skeleton, metrics and debug overlay

Selecting an exercise resets every detector before activating the requested one. MediaPipe landmark extraction is shared, but exercise state, thresholds, scoring, feedback and repetition logic are not.

## Performance notes

- CameraX uses `KEEP_ONLY_LATEST`, so inference never queues stale frames.
- Camera analysis runs on a dedicated single-thread executor.
- MediaPipe live-stream mode performs inference away from Compose.
- UI state is delivered through `StateFlow`; there is no busy loop.
- Use good lighting and keep the required joints visible for stable 30 FPS tracking.

## Release build

Create a signing configuration in Android Studio, then use **Build → Generate Signed App Bundle or APK**. The existing release build enables code and resource shrinking.
