# Hughes Clip Prep

Prepare DJI footage before editing — sort junk, trim dead air, polish audio, and package YouTube uploads.

## On your Mac

1. Double-click **Update.command** inside `Desktop/Hughes Clip Prep/`
2. Wait for the build to finish
3. Open **Hughes Clip Prep.app** on your Desktop
4. Read the **Guide** tab for the full workflow

## Tabs

| Tab | What it does |
|-----|----------------|
| **Clip Cleaner** | Batch trim, Production Pass, and optional stabilization |
| **Smart Analysis** | KEEP / B-ROLL / REVIEW / DISCARD scoring, optional AI Assist + cut hints, Run Pipeline |
| **Shorts** | Ranked vertical Shorts from a finished Filmora export |
| **YouTube Prep** | Story Review, titles, Rank Thumbnails, description/tags, upload package |
| **Settings** | Analysis thresholds, brand/thumbnails, OpenAI |
| **Guide** | Step-by-step workflow manual and changelog |

## Workflow (short)

1. **Smart Analysis** — sort the shoot folder  
2. **Clip Cleaner** — trim/polish KEEP clips  
3. **Filmora** — creative edit  
4. **YouTube Prep** — upload package for the finished video  
5. **Shorts** — optional vertical clips from that same export  

## Requirements

- macOS 14.0 or later
- Auto-Editor: `brew install auto-editor`
- FFmpeg: `brew install ffmpeg`

## Updating the manual

When new features ship, update `Models/AppManual.swift` and bump `Utilities/AppIdentity.swift`.
