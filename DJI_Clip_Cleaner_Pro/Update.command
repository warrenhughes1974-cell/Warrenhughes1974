#!/bin/bash
set -euo pipefail

TEMP_REPO="$(mktemp -d /tmp/dji-clip-cleaner-update.XXXXXX)"
trap 'rm -rf "$TEMP_REPO"' EXIT

REPO_URL="https://github.com/warrenhughes1974-cell/Warrenhughes1974.git"
INSTALLER="$TEMP_REPO/DJI_Clip_Cleaner_Pro/install-on-mac.sh"
PROJECT_DIR="$HOME/Desktop/DJI Clip Cleaner Pro"
BUILD_SCRIPT="$PROJECT_DIR/Install App on Desktop.command"

echo "=== DJI Clip Cleaner Pro — Update ==="
echo "Downloading latest version..."

git clone --depth 1 --filter=blob:none --sparse "$REPO_URL" "$TEMP_REPO"
cd "$TEMP_REPO"
git sparse-checkout set DJI_Clip_Cleaner_Pro

chmod +x "$INSTALLER"
SKIP_OPEN_XCODE=1 "$INSTALLER"

echo ""
echo "Building and installing the Desktop app..."
chmod +x "$BUILD_SCRIPT"
"$BUILD_SCRIPT"
