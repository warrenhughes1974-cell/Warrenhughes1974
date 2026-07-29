# Hughes Hot Lap

Grid-ready DJI clip prep for YouTube creators. Sort junk, trim dead air, polish audio, then hand off to Filmora.

## On your Mac

1. Double-click **Update.command** inside `Desktop/Hughes Hot Lap/`
2. Wait for the build to finish
3. Open **Hughes Hot Lap.app** on your Desktop
4. Read the **Race Manual** tab for the full workflow

## Tabs

| Tab | What it does |
|-----|----------------|
| **Pit Lane** | Batch trim and Production Pass polish |
| **Scouting** | Smart Analysis — KEEP / REVIEW / DISCARD |
| **Garage Setup** | Tune analysis thresholds |
| **Race Manual** | Step-by-step editing guide + changelog |

## Requirements

- macOS 14.0 or later
- Xcode 15+ (for building from source)
- Auto-Editor: `brew install auto-editor`
- FFmpeg: `brew install ffmpeg`

## Updating the manual

When new features ship, update `Models/AppManual.swift` and bump `Utilities/AppIdentity.swift` version.
