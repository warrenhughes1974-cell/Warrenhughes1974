#!/bin/bash
set -euo pipefail

REPO="$HOME/Desktop/Warrenhughes1974-temp"
PROJECT_INSTALLER="$REPO/DJI_Clip_Cleaner_Pro/install-on-mac.sh"

osascript -e 'display notification "Pulling latest code..." with title "DJI Clip Cleaner Pro"'

if [[ ! -d "$REPO/.git" ]]; then
  osascript -e 'display dialog "Repo not found at ~/Desktop/Warrenhughes1974-temp\n\nRun the git clone steps first." buttons {"OK"} default button "OK" with title "DJI Clip Cleaner Pro"'
  exit 1
fi

cd "$REPO"
git pull

if [[ ! -x "$PROJECT_INSTALLER" ]]; then
  osascript -e 'display dialog "install-on-mac.sh not found." buttons {"OK"} default button "OK" with title "DJI Clip Cleaner Pro"'
  exit 1
fi

"$PROJECT_INSTALLER"

osascript -e 'display notification "Ready — press ⌘R in Xcode to build." with title "DJI Clip Cleaner Pro"'
