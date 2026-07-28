# DJI Clip Cleaner Pro — Agent Context

This is a **personal macOS SwiftUI project**. It is **not** related to CSO, QLA, QuikPlan, or `app.py` in the repo root.

## Rules for AI agents

- Work only inside `DJI_Clip_Cleaner_Pro/`
- Do not modify insurance conversion code unless explicitly asked
- One session = one working feature the user can Run in Xcode
- Prefer small, surgical edits over architecture lectures
- Keep **Clip Cleaner** and **Smart Analysis** on separate tabs
- Never stuff new features into a monolithic single file

## Current state

- `MainTabView` — two tabs wired
- `CleanerView` — placeholder; user’s real cleaner lives in their Mac `ContentView.swift` pending migration
- `AnalysisView` — folder scan + table works; detectors are stubs

## User workflow

YouTube creator: Halloween hunts, product reviews, travel/work vlogs. DJI camera footage. Wants fast editing prep (proxies, analysis, keep/discard recommendations).

## Next likely tasks

1. User pastes or drags existing `ContentView.swift` → migrate to `CleanerView` / `CleanerViewModel`
2. Implement speech column (AVSpeechRecognizer or similar)
3. Implement motion column (AVAssetReader frame sampling)
4. Recommendation engine
