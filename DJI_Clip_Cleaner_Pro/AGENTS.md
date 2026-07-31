# Hughes Clip Prep — Agent Context

Personal macOS SwiftUI project under `DJI_Clip_Cleaner_Pro/`.  
**Not** related to CSO, QLA, QuikPlan, or `app.py`.

## Rules

- Work only inside `DJI_Clip_Cleaner_Pro/` for this app
- Surgical edits; minimize blast radius
- Bump `AppIdentity.version` + `MARKETING_VERSION` when shipping
- Prefer merge to `main` so Desktop `Update.command` installs the build
- Do not redesign architecture or rewrite workflows wholesale

## Tabs (current)

| Tab | Role |
|-----|------|
| Clip Cleaner | auto-editor trim, Production Pass, optional stabilize |
| Smart Analysis | speech/motion/jerk → KEEP/B-ROLL/REVIEW/DISCARD; optional AI Assist + cut hints; Run Pipeline |
| Shorts | vertical moments from a finished export |
| YouTube Prep | Story Review → titles/thumbs/description/tags/SRT upload pack |
| Settings | analysis thresholds, brand/thumbnails, OpenAI |
| Guide | `AppManual.swift` workflow + changelog |

## OpenAI (optional)

Key in Application Support (not Keychain). Toggles: Whisper, cloud story, cloud copy, Vision thumbs, AI Assist, cut hints.

## Install / update

- `Update.command` — pull latest and rebuild Desktop app
- `Update Everything.command` / `Update And Open.command` — aliases that run `Update.command`
