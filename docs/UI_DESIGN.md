# Workout Tracker UI

The desktop and Android interfaces share this visual contract. Desktop uses Qt's
Fusion widget style and Arial on both Windows and macOS; native window decorations
remain platform-specific. Android uses Material 3 and the platform typeface.

| Token | Value |
| --- | --- |
| Background | `#0F1115` |
| Card | `#171A21` |
| Blue accent | `#2D8CFF` |
| Success | `#32D583` |
| Error | `#F04438` |
| Main text | `#F5F7FA` |
| Secondary text | `#A9B4C4` |
| Corner radius | 12–18 logical pixels / dp |
| Motion | 150–200 ms |
| Primary touch / button targets | At least 48 logical pixels / dp |

## Components

Desktop reusable components live in `app/ui/design.py`: painted button lift and
press effects, switch animation, numeric presentation, progress bars and rings,
hover borders, tab indicators, page fades, disclosures, illustrations, and toasts.
Animations never feed intermediate numbers back into workout state. Page fades
use snapshots so they do not apply compositing effects to the live camera.

Android reusable components live in `ui/components/DesignComponents.kt`. The
Material color scheme is in `ui/theme/Theme.kt`. Phone workout content scrolls
below the camera; wide windows place information beside the camera. Guide and
settings reading widths are capped on tablets. Guides use a split layout in wide
windows, and history uses an adaptive card grid.

Both interfaces are dark-only. The existing saved appearance field is retained;
the appearance screen presents dark mode as a fixed choice. Existing localization
mechanisms are unchanged, and new presentation labels use their resource catalogs.

## Shortcuts and accessibility

- Space pauses/resumes using the existing pause action.
- R resets using the existing reset action.
- C toggles the camera using existing camera actions.
- F toggles fullscreen.

Single-key shortcuts are disabled while editing a text field, spin box, or combo
box. They do not auto-repeat. History cards support keyboard activation, controls
retain native semantics, and all camera actions have descriptive labels.

## History insights

Insights read existing sessions without new columns or writes. The activity chart
shows total reps for each of the last seven local calendar dates. Best session is
the largest saved session rep count. A streak counts consecutive active dates
ending today, or yesterday if there is no session today. Searching or filtering
the list does not change these all-history summary values.

## Scope

Detector implementations, MediaPipe configuration, pose processing, rep counting,
timers, history schemas/repositories, localization infrastructure, and packaging
are untouched. Desktop camera pixel rendering no longer burns debugging text
over the video; the skeleton is preserved and readable telemetry uses UI overlays.

Verification includes desktop regression tests, English/Vietnamese page renders
at 1100×700, 1440×900, 1080p, 1440p, and 4K, and Android unit tests, lint, debug
builds, and emulator navigation/layout checks. Native Windows execution still
requires a Windows host. Emulator UI checks use disabled host cameras and are not
a replacement for exercising detection with a real camera.
