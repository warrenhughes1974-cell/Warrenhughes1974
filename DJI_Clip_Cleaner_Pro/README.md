# DJI Clip Cleaner Pro

Personal macOS SwiftUI app for DJI footage workflows.

**Separate from the CSO / insurance conversion work in the repo root.**

## Tabs

| Tab | What it does |
|-----|----------------|
| **Clip Cleaner** | Batch silence-trim via Auto-Editor → `Processed/` folder |
| **Smart Analysis** | Scan clips, show metadata table (speech/motion coming next) |

## Project layout

```
DJI_Clip_Cleaner_Pro/
├── DJI_Clip_Cleaner_ProApp.swift
├── Models/
│   ├── VideoFile.swift
│   ├── CleaningPreset.swift
│   └── AnalysisResult.swift
├── ViewModels/
│   ├── CleanerViewModel.swift
│   └── AnalysisViewModel.swift
├── Views/
│   ├── MainTabView.swift
│   ├── Cleaner/CleanerView.swift
│   └── Analysis/AnalysisView.swift
├── Services/
│   ├── FolderScanner.swift
│   └── VideoMetadataService.swift
└── Utilities/
    └── DateFormatter+LogTimestamp.swift
```

## Update your Mac Xcode project

Your old single `ContentView.swift` is now split across these files. To upgrade:

1. **Back up** your project folder first (Time Machine or duplicate the folder).
2. In Xcode, **delete** the old monolithic `ContentView.swift` from the project (Move to Trash).
3. Drag the entire inner `DJI_Clip_Cleaner_Pro` source folder into Xcode.
   - Check **Copy items if needed**
   - Check your app target
4. Open `DJI_Clip_Cleaner_ProApp.swift` — it should launch `MainTabView()` (already set).
5. **Build & Run** — you should see both tabs.

If Xcode complains about duplicate symbols, you still have the old `ContentView.swift` in the target. Remove it.

## What Clip Cleaner does

Uses **Auto-Editor** (`/opt/homebrew/bin/auto-editor`) to remove dead air from clips:

- Originals are **never** modified
- Output goes to a `Processed/` subfolder as `*_CLEANED.mp4`
- Presets: Conservative (1.0s margin), Balanced (0.5s), Aggressive (0.25s)
- Skips files that already have a `_CLEANED` output

Install Auto-Editor if needed:

```bash
brew install auto-editor
```

## Smart Analysis tab

- Choose a folder → scans MP4/MOV/M4V
- Shows clip name, duration, size
- Speech / Motion columns are placeholders for the next features
