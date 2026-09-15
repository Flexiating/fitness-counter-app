# Fitness Counter

A desktop Python app for macOS and Windows that uses a webcam and pose estimation to count complete push-ups and crunches. It renders detected landmarks, waits for an adequately visible body, and counts a repetition only after a stable full movement cycle.

## Features

- PySide6 desktop interface with exercise picker, live camera view, state, and repetitions.
- MediaPipe pose adapter behind a replaceable `PoseModel` interface.
- Debounced, noise-tolerant `extended → contracted → extended` repetition state machine.
- Push-up elbow-angle and crunch hip-angle detection.
- JSON workout history saved when a counted session is closed.
- Unit tests for geometry, smoothing, readiness, state transitions, and incomplete movement.

## Requirements

- Python 3.9–3.12 (Python 3.12 recommended). Python 3.13 and 3.14 are not
  compatible with the classic MediaPipe Pose API used by this version.
- A webcam
- macOS or Windows

## Run on macOS

If Python 3.12 is not installed, first use
[`set_up_mac/install_python_312.command`](set_up_mac/install_python_312.command).

In Terminal from this folder:

```bash
chmod +x run_mac.sh
./run_mac.sh
```

The script automatically selects Python 3.12, 3.11, 3.10, or 3.9, creates a matching private environment, installs dependencies, and starts the app. If none is installed, download Python 3.12 from [python.org](https://www.python.org/downloads/), then run the script again. If the camera is unavailable, allow your terminal/Python app in **System Settings → Privacy & Security → Camera**, then restart it.

## Run on Windows

If Python 3.12 is not installed, first double-click
[`set_up_win/install_python_312.bat`](set_up_win/install_python_312.bat).

Double-click `run_windows.bat`, or run it from Command Prompt. It automatically selects a compatible Python version, creates a private environment, installs the packages, and starts the app. Grant camera permission if Windows asks.

## Create a no-install app

For people who should not install Python or packages, build a native app once, then share the generated result.

On macOS, run `./build_mac.sh`. Share `dist/Workout Tracker.app`.

On Windows, run `build_windows.bat`. Share the complete `dist/Workout Tracker` folder, not only the `.exe` inside it.

Build each platform on that platform: macOS creates the `.app`; Windows creates the `.exe`. The recipient can open the built app without Python, a virtual environment, or an internet connection.

## Use

1. Choose **Push Up** or **Crunch**.
2. Press **Start** and position your whole relevant side in the frame.
3. Wait until the state says Ready. The counter requires stable start, end, and return positions, so partial movements are ignored.
4. Press Reset between sets. Closing a session with one or more counted repetitions records it in `data/workouts.json`.

## Architecture

```
webcam → Camera → PoseModel/MediaPipe adapter → standardized landmarks
       → MotionProcessor/smoother → selected exercise → RepetitionCounter → GUI/storage
```

- `app/camera`: opens, reads, and releases the webcam only.
- `app/models`: `PoseModel` abstraction; `MediaPipePoseModel` translates MediaPipe output into named `Landmark` values.
- `app/pose`: geometry, visibility validation, and moving-average smoothing.
- `app/exercises`: self-contained exercise algorithms registered with `ExerciseManager`.
- `app/processing`: reusable movement and repetition logic.
- `app/ui`: GUI and a camera/pose worker thread so the interface stays responsive.
- `app/data`: small, replaceable JSON storage layer.

## Detection logic

For a push-up, the app measures both elbow angles from shoulder–elbow–wrist landmarks and uses the clearer (more extended) side. A stable elbow angle above the configured UP threshold arms the movement; a stable angle below the DOWN threshold confirms depth; returning to UP counts one rep.

For a crunch, it measures shoulder–hip–knee angle on each side and averages them. A stable extended torso, then contracted torso, then extended torso counts one rep. Both algorithms reject low-visibility poses and intermediate movements.

Thresholds, confidence levels, resolution, and smoothing live in `app/config/settings.py` for simple calibration.

## Tests

After dependencies are installed:

```bash
python -m pytest
```

## Add an exercise

1. Create `app/exercises/squat.py` inheriting `BaseExercise`.
2. Declare required named landmarks and compute angles with `calculate_angle`.
3. Feed stable `MovementState` values into a `RepetitionCounter`.
4. Register it in `ExerciseManager` and add its thresholds to `settings.py`.

## Replace the pose model

Create another class implementing `PoseModel.load`, `predict`, and `close`. Its `predict` method returns the same `PoseLandmarks` dictionary (`LandmarkName` to `Landmark`). Supply it to `ModelManager`; no exercise or UI code needs to change.

## Troubleshooting

- **No camera**: close other camera apps, check OS permission, then reconnect or select a different camera index in `Camera`.
- **Not counting**: use a side-on view with shoulder, elbow/hip, and knee/wrist visible; make complete movements and adjust thresholds for your setup.
- **Package install fails**: confirm a supported Python version and update `pip` (the launchers do this automatically).
