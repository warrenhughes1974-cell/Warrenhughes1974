# DJI Clip Cleaner Pro — Agent Context

Personal macOS SwiftUI project. **Not** related to CSO, QLA, QuikPlan, or `app.py`.

## Rules

- Work only inside `DJI_Clip_Cleaner_Pro/`
- One session = one runnable feature
- Keep Clip Cleaner and Smart Analysis on separate tabs
- Surgical edits; no monolithic files

## Current state

- **Clip Cleaner** — fully migrated from user's `ContentView.swift`
- **Smart Analysis** — folder scan + table; detectors not implemented yet
- Uses Auto-Editor CLI for silence trimming

## File map

| File | Role |
|------|------|
| `CleanerView.swift` | Clip Cleaner UI (was ContentView) |
| `CleanerViewModel.swift` | Scan, process, cancel, logging |
| `AnalysisView.swift` | Smart Analysis UI |
| `AnalysisViewModel.swift` | Analysis folder scan |
| `VideoFile.swift` | Shared video model |

## Next features

1. Speech detection column
2. Motion / scene detection column
3. KEEP / REVIEW / DISCARD recommendation engine
