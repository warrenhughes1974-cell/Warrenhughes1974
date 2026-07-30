#!/bin/bash
set -euo pipefail

PROJECT_DIR="$HOME/Desktop/Hughes Clip Prep"
XCODEPROJ="$PROJECT_DIR/DJI Clip Cleaner Pro.xcodeproj"
SCHEME="Hughes Clip Prep"
BUILD_DIR="$HOME/Library/Application Support/HughesClipPrep/build"
LOG_FILE="$HOME/Library/Application Support/HughesClipPrep/last-build.log"
DESKTOP_APP="$HOME/Desktop/Hughes Clip Prep.app"
APP_VERSION="1.24"

echo "=== Building Hughes Clip Prep v${APP_VERSION} ==="
echo "This may take a minute..."
echo ""

if [[ ! -d "$XCODEPROJ" ]]; then
  osascript -e 'display dialog "Project not found at:\n~/Desktop/Hughes Clip Prep" buttons {"OK"} with title "Hughes Clip Prep"'
  exit 1
fi

echo "Closing any running copy of the app..."
osascript -e 'tell application "Hughes Clip Prep" to quit' 2>/dev/null || true
osascript -e 'tell application "Hughes Hot Lap" to quit' 2>/dev/null || true
osascript -e 'tell application "DJI Clip Cleaner Pro" to quit' 2>/dev/null || true
sleep 1

echo "Cleaning old build cache..."
mkdir -p "$(dirname "$BUILD_DIR")"
rm -rf "$BUILD_DIR"
rm -f "$LOG_FILE"

set +e
xcodebuild \
  -project "$XCODEPROJ" \
  -scheme "$SCHEME" \
  -configuration Release \
  -derivedDataPath "$BUILD_DIR" \
  clean build 2>&1 | tee "$LOG_FILE"
BUILD_STATUS=${PIPESTATUS[0]}
set -e

if [[ "$BUILD_STATUS" -ne 0 ]]; then
  echo ""
  echo "=== Build failed — Swift errors ==="
  # Surface the real compiler lines instead of module-cache noise.
  grep -E 'error:|fatal error:|❌' "$LOG_FILE" | head -40 || true
  echo ""
  echo "Full log saved to:"
  echo "  $LOG_FILE"
  osascript -e "display dialog \"Build failed.\n\nOpen Terminal and run Update again, or send the lines that start with error: from:\n~/Library/Application Support/HughesClipPrep/last-build.log\" buttons {\"OK\"} with title \"Hughes Clip Prep\""
  exit 1
fi

BUILT_APP="$BUILD_DIR/Build/Products/Release/Hughes Clip Prep.app"

if [[ ! -d "$BUILT_APP" ]]; then
  osascript -e 'display dialog "Build finished but app was not found." buttons {"OK"} with title "Hughes Clip Prep"'
  exit 1
fi

rm -rf "$DESKTOP_APP"
ditto "$BUILT_APP" "$DESKTOP_APP"

echo ""
echo "Installed:"
echo "  $DESKTOP_APP"
echo ""

open "$DESKTOP_APP"

osascript -e "display dialog \"Version ${APP_VERSION} is now on your Desktop.\n\nPick a series preset in Settings, then use Refresh Titles and Generate Thumbnails for a consistent brand.\" buttons {\"OK\"} with title \"Hughes Clip Prep\""

osascript -e "display notification \"Version ${APP_VERSION} installed on Desktop.\" with title \"Hughes Clip Prep\""
