#!/bin/bash
set -euo pipefail

TEMP_REPO="$(mktemp -d /tmp/dji-clip-cleaner-update.XXXXXX)"
trap 'rm -rf "$TEMP_REPO"' EXIT

REPO_URL="https://github.com/warrenhughes1974-cell/Warrenhughes1974.git"
INSTALLER="$TEMP_REPO/DJI_Clip_Cleaner_Pro/install-on-mac.sh"

echo "=== DJI Clip Cleaner Pro — Update ==="
echo "Downloading latest version (only the DJI app, not the whole repo)..."

git clone --depth 1 --filter=blob:none --sparse "$REPO_URL" "$TEMP_REPO"
cd "$TEMP_REPO"
git sparse-checkout set DJI_Clip_Cleaner_Pro

chmod +x "$INSTALLER"
"$INSTALLER"

osascript -e 'display notification "Update complete. Press ⌘R in Xcode." with title "DJI Clip Cleaner Pro"'
