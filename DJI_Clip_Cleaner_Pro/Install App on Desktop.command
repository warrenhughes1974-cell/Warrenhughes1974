#!/bin/bash
set -euo pipefail

PROJECT_DIR="$HOME/Desktop/DJI Clip Cleaner Pro"
XCODEPROJ="$PROJECT_DIR/DJI Clip Cleaner Pro.xcodeproj"
SCHEME="DJI Clip Cleaner Pro"
BUILD_DIR="$HOME/Library/Application Support/DJIClipCleanerPro/build"
DESKTOP_APP="$HOME/Desktop/DJI Clip Cleaner Pro.app"

echo "=== Building DJI Clip Cleaner Pro ==="
echo "This may take a minute the first time..."
echo ""

if [[ ! -d "$XCODEPROJ" ]]; then
  osascript -e 'display dialog "Project not found at:\n~/Desktop/DJI Clip Cleaner Pro" buttons {"OK"} with title "Install App"'
  exit 1
fi

xcodebuild \
  -project "$XCODEPROJ" \
  -scheme "$SCHEME" \
  -configuration Release \
  -derivedDataPath "$BUILD_DIR" \
  build

BUILT_APP="$BUILD_DIR/Build/Products/Release/DJI Clip Cleaner Pro.app"

if [[ ! -d "$BUILT_APP" ]]; then
  osascript -e 'display dialog "Build finished but app was not found." buttons {"OK"} with title "Install App"'
  exit 1
fi

rm -rf "$DESKTOP_APP"
ditto "$BUILT_APP" "$DESKTOP_APP"

echo ""
echo "Installed:"
echo "  $DESKTOP_APP"
echo ""
echo "You can now double-click the app on your Desktop anytime."
echo ""

open "$DESKTOP_APP"

osascript -e 'display notification "DJI Clip Cleaner Pro is on your Desktop." with title "Install App"'
