# Hughes Clip Prep

Prepare DJI footage before editing — sort junk, trim dead air, polish audio, and smooth shaky camera movement.

## On your Mac

1. Double-click **Update.command** inside `Desktop/Hughes Clip Prep/`
2. Wait for the build to finish
3. Open **Hughes Clip Prep.app** on your Desktop
4. Read the **Guide** tab for the full workflow

## Tabs

| Tab | What it does |
|-----|----------------|
| **Clip Cleaner** | Batch trim, Production Pass, and optional stabilization |
| **Smart Analysis** | KEEP / REVIEW / DISCARD scoring and sudden movement detection |
| **Settings** | Tune analysis thresholds |
| **Guide** | Step-by-step workflow manual and changelog |

## Requirements

- macOS 14.0 or later
- Auto-Editor: `brew install auto-editor`
- FFmpeg: `brew install ffmpeg`

## Updating the manual

When new features ship, update `Models/AppManual.swift` and bump `Utilities/AppIdentity.swift`.
