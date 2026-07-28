#!/bin/bash
set -euo pipefail

DESKTOP_APP="$HOME/Desktop/DJI Clip Cleaner Pro"
REPO="$HOME/Desktop/Warrenhughes1974-temp/DJI_Clip_Cleaner_Pro"
GITHUB_RAW="https://raw.githubusercontent.com/warrenhughes1974-cell/Warrenhughes1974/main/DJI_Clip_Cleaner_Pro"

if [[ ! -d "$DESKTOP_APP" ]]; then
  osascript -e 'display dialog "Desktop project not found at:\n~/Desktop/DJI Clip Cleaner Pro" buttons {"OK"} with title "Fix Build"'
  exit 1
fi

copy_file() {
  local relative_path="$1"
  local dest="$DESKTOP_APP/DJI_Clip_Cleaner_Pro/$relative_path"
  local source=""

  if [[ -f "$REPO/DJI_Clip_Cleaner_Pro/$relative_path" ]]; then
    source="$REPO/DJI_Clip_Cleaner_Pro/$relative_path"
  else
    mkdir -p "$(dirname "$dest")"
    curl -fsSL "$GITHUB_RAW/DJI_Clip_Cleaner_Pro/$relative_path" -o "$dest"
    echo "Downloaded: $relative_path"
    return
  fi

  mkdir -p "$(dirname "$dest")"
  cp "$source" "$dest"
  echo "Copied: $relative_path"
}

if [[ -d "$REPO" ]]; then
  echo "Updating repo..."
  (cd "$HOME/Desktop/Warrenhughes1974-temp" && git pull) || true
fi

copy_file "Views/Analysis/AnalysisView.swift"
copy_file "Views/MainTabView.swift"
copy_file "Views/Settings/SettingsView.swift"
copy_file "ViewModels/CleanerViewModel.swift"
copy_file "ViewModels/AnalysisViewModel.swift"
copy_file "Models/AnalysisResult.swift"
copy_file "Models/AnalysisSettings.swift"
copy_file "Services/SpeechAnalyzer.swift"
copy_file "Services/MotionAnalyzer.swift"
copy_file "Services/RecommendationEngine.swift"

open "$DESKTOP_APP/DJI Clip Cleaner Pro.xcodeproj"

osascript -e 'display notification "Build fixes applied. Press ⌘R in Xcode." with title "DJI Clip Cleaner Pro"'
