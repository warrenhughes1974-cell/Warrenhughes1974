#!/bin/bash
set -euo pipefail

REPO="$HOME/Desktop/Warrenhughes1974-temp"
INSTALLER="$REPO/DJI_Clip_Cleaner_Pro/install-on-mac.sh"

echo "=== DJI Clip Cleaner Pro — Full Update ==="

if [[ ! -d "$REPO/.git" ]]; then
  echo "Cloning repo..."
  git clone https://github.com/warrenhughes1974-cell/Warrenhughes1974.git "$REPO"
fi

cd "$REPO"
git pull

chmod +x "$INSTALLER"
"$INSTALLER"

osascript -e 'display notification "Full update done. Press ⌘R in Xcode." with title "DJI Clip Cleaner Pro"'
