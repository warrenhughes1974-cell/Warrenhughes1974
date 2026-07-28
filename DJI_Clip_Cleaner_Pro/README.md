# DJI Clip Cleaner Pro

Ready-to-run macOS app. No manual file dragging in Xcode.

## On your Mac — two steps

### Option A: One-command install (easiest)

Open **Terminal** and run:

```bash
cd ~/Desktop
git clone https://github.com/warrenhughes1974-cell/Warrenhughes1974.git Warrenhughes1974-temp
cd Warrenhughes1974-temp/DJI_Clip_Cleaner_Pro
chmod +x install-on-mac.sh
./install-on-mac.sh
```

That script will:
- Back up your old Desktop project (if one exists)
- Copy the fresh project to **Desktop → DJI Clip Cleaner Pro**
- Open it in Xcode automatically

Then press **⌘R** in Xcode.

### Option B: Open the project directly

If you already have the repo:

1. In Finder, go to `Warrenhughes1974/DJI_Clip_Cleaner_Pro/`
2. Double-click **`DJI Clip Cleaner Pro.xcodeproj`**
3. Press **⌘R**

## Requirements

- macOS 14.0 or later
- Xcode 15+
- [Auto-Editor](https://github.com/WyattBlue/auto-editor) for the Clip Cleaner tab:

```bash
brew install auto-editor
```

## Tabs

| Tab | What it does |
|-----|----------------|
| **Clip Cleaner** | Batch silence-trim via Auto-Editor → `Processed/` folder |
| **Smart Analysis** | Scan clips, show metadata table |

## Old project on Desktop?

The install script automatically renames your existing folder to  
`DJI Clip Cleaner Pro.backup.YYYYMMDD-HHMMSS` before installing the new one.

You do **not** need to delete `ContentView.swift` manually — this is a fresh, complete project.
