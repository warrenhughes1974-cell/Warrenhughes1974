#!/bin/bash
set -euo pipefail

PROJECT_DIR="$HOME/Desktop/DJI Clip Cleaner Pro"
XCODEPROJ="$PROJECT_DIR/DJI Clip Cleaner Pro.xcodeproj"
SCHEME="DJI Clip Cleaner Pro"
BUILD_DIR="$HOME/Library/Application Support/DJIClipCleanerPro/build"
DESKTOP_APP="$HOME/Desktop/DJI Clip Cleaner Pro.app"
APP_VERSION="1.2"

echo "=== Building DJI Clip Cleaner Pro v${APP_VERSION} ==="
echo "This may take a minute..."
echo ""

if [[ ! -d "$XCODEPROJ" ]]; then
  osascript -e 'display dialog "Project not found at:\n~/Desktop/DJI Clip Cleaner Pro" buttons {"OK"} with title "Install App"'
  exit 1
fi

echo "Closing any running copy of the app..."
osascript -e 'tell application "DJI Clip Cleaner Pro" to quit' 2>/dev/null || true
sleep 1

echo "Cleaning old build cache..."
rm -rf "$BUILD_DIR"

xcodebuild \
  -project "$XCODEPROJ" \
  -scheme "$SCHEME" \
  -configuration Release \
  -derivedDataPath "$BUILD_DIR" \
  clean build

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

open "$DESKTOP_APP"

osascript -e "display dialog \"Version ${APP_VERSION} is now on your Desktop.\n\nOn Smart Analysis, look for the big blue Scan Folder button and the v${APP_VERSION} badge.\" buttons {\"OK\"} with title \"DJI Clip Cleaner Pro\""

osascript -e "display notification \"Version ${APP_VERSION} installed on Desktop.\" with title \"DJI Clip Cleaner Pro\""
