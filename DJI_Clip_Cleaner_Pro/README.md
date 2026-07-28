# DJI Clip Cleaner Pro

Personal macOS SwiftUI app for DJI footage workflows.

**This folder is separate from the CSO / insurance conversion work in the repo root.**

## What this project is

| Tab | Purpose |
|-----|---------|
| **Clip Cleaner** | Your existing proxy/transcode workflow (migrate from `ContentView.swift`) |
| **Smart Analysis** | Scan folders, show clip table, future speech/motion/recommendation engine |

## Project layout

```
DJI_Clip_Cleaner_Pro/
├── DJI_Clip_Cleaner_ProApp.swift    # App entry → MainTabView
├── Views/
│   ├── MainTabView.swift            # Two tabs
│   ├── Cleaner/CleanerView.swift    # ← paste your existing cleaner UI here
│   └── Analysis/AnalysisView.swift  # Working scan + table foundation
├── Models/
│   ├── VideoFile.swift
│   └── AnalysisResult.swift
├── ViewModels/
│   └── AnalysisViewModel.swift
└── Services/
    ├── FolderScanner.swift
    └── VideoMetadataService.swift
```

## Get this into Xcode (5 minutes)

### If you already have the Xcode project on your Mac

1. **Pull or copy** this `DJI_Clip_Cleaner_Pro` folder onto your Mac.
2. In Xcode, right-click your project → **Add Files to "DJI Clip Cleaner Pro"…**
3. Select the entire `DJI_Clip_Cleaner_Pro` source folder (the inner one with `.swift` files).
4. Check **Copy items if needed** and your app target.
5. Open `DJI_Clip_Cleaner_ProApp.swift` and confirm it launches `MainTabView()` (already set).
6. **Migrate your cleaner:**
   - Open your old `ContentView.swift`.
   - Copy its `body` and supporting state into `CleanerView.swift` (or move the whole file and rename).
   - Delete or stop using the old `ContentView` as the root view.
7. **Build & Run** — you should see **Clip Cleaner** and **Smart Analysis** tabs.

### Drag files into Cursor (for AI help)

In Finder: **Product → Show Build Folder in Finder** won't help. Instead:

- In Xcode sidebar, right-click `ContentView.swift` → **Show in Finder**
- Drag the `.swift` file into this Cursor chat

Or open **only** the DJI project folder in Cursor (File → Open Folder).

## Smart Analysis tab (working now)

- Choose a folder of `.mp4` / `.mov` clips
- Scans and lists: clip name, duration, file size
- Speech / Motion columns show **Not Yet Implemented** (hooks ready)
- Recommendation column shows **Pending** until we add the engine

## Roadmap (one feature per session)

1. ✅ Tab shell + Smart Analysis table
2. Migrate your Clip Cleaner into `CleanerView`
3. Silence / speech detection column
4. Motion / scene detection column
5. Recommendation engine (KEEP / REVIEW / DISCARD)

## Filmora proxy note

If Filmora made your files smaller, that is **proxy media** — lower-resolution copies for faster editing. Your originals are still on disk. This app’s cleaner can do something similar for your DJI workflow once your existing logic is migrated.
