# Workout Tracker release build guide

The release scripts create native packages from the current source tree. Build
on the target operating system: PyInstaller does not reliably cross-compile a
Windows executable from macOS or a macOS app from Windows.

## Prerequisites

- Python 3.10 or 3.11
- A current `pip`
- macOS: Xcode Command Line Tools (`xcode-select --install`) for `iconutil`
- Windows: the Microsoft Visual C++ runtime is recommended for OpenCV

The scripts install the dependencies in `requirements.txt`, including
PyInstaller and Pillow, before every standard build. Use a virtual environment
for predictable releases.

## Build for Windows

On Windows, from the project root:

```powershell
python scripts\build_windows.py
```

The finished single-file application is:

```text
release\windows\WorkoutTracker.exe
```

It is a windowed executable and does not open a console. Test it on a computer
without the source checkout before sharing it. Windows SmartScreen may show a
warning until the executable is code-signed and has built reputation.

## Build for macOS

On macOS, from the project root:

```bash
python3 scripts/build_macos.py
```

The finished Finder and Dock application is:

```text
release/macos/WorkoutTracker.app
```

The `.app` is built without a terminal window. It has a standard unsigned,
signing-ready bundle structure. Build on Apple Silicon for an `arm64` release,
or on an Intel Mac for an `x86_64` release. A `universal2` build requires a
matching universal2 Python/PyInstaller environment:

```bash
python3 scripts/build_macos.py --target-arch universal2
```

After building, sign and notarize the app for distribution outside your own Mac:

```bash
codesign --deep --force --options runtime --sign "Developer ID Application: Your Name" release/macos/WorkoutTracker.app
```

## Automatic platform build

To build for whichever supported operating system is currently running:

```bash
python scripts/build.py
```

The named platform scripts intentionally stop with a clear message if run on
the wrong operating system.

## Build options

For a faster repeat build when dependencies and tests are already verified:

```bash
python scripts/build_macos.py --skip-install --skip-tests
```

The scripts always run PyInstaller with a clean `build/` and `dist/` directory,
then copy the artifact to `release/`.

## Cleaning generated output

```bash
python scripts/clean.py
```

This removes `build/`, `dist/`, Python cache folders, test cache files, and
temporary bytecode. To also remove release artifacts:

```bash
python scripts/clean.py --release
```

## Icons

The first Windows build generates `icons/app.ico`; the first macOS build
generates `icons/app.icns`. The icon source design is documented in
`icons/app.svg`. To use a custom icon, replace either generated file before
running the relevant build command, using the same filename.

## New models, assets, fonts, and configuration

Place new model files in `models/`, visual assets and fonts in `assets/`, and
configuration under `app/config/`. `WorkoutTracker.spec` bundles all of these
locations automatically. Read them at runtime through
`app.utils.paths.resource_path()` so they work in development, the Windows
executable, and the macOS bundle.

Use `app.utils.paths.app_data_path()` for logs, history, settings, or any other
files the application writes. It keeps writable data outside the signed app
bundle.

## Common build errors

### `No matching distribution found for mediapipe`

Use Python 3.10 or 3.11. MediaPipe 0.10.14 used by this project does not
support every Python version.

### `iconutil` is missing

Run the macOS build on a Mac and install Xcode Command Line Tools:

```bash
xcode-select --install
```

### Camera permission is denied

Grant camera access to `WorkoutTracker.app` in macOS Privacy & Security, or to
`WorkoutTracker.exe` in Windows camera privacy settings. Camera permission is
granted to the packaged app, not to the Python interpreter used during build.

### MediaPipe/OpenCV module or library error after packaging

Build using the provided scripts rather than a manual PyInstaller command. The
spec collects MediaPipe, OpenCV, NumPy data, dynamic libraries, and hidden
imports used by the application.
