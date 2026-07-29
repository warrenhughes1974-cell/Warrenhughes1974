#!/bin/bash
set -euo pipefail

# Installs or updates Hughes Hot Lap on your Desktop.

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/Desktop/Hughes Hot Lap"
OLD_DEST="$HOME/Desktop/DJI Clip Cleaner Pro"

echo "Installing to:"
echo "  $DEST"

mkdir -p "$DEST"
ditto "$REPO_ROOT" "$DEST"

# Remove stale user-specific Xcode state from copied project.
rm -rf "$DEST/DJI Clip Cleaner Pro.xcodeproj/xcuserdata"
rm -rf "$DEST/DJI Clip Cleaner Pro.xcodeproj/project.xcworkspace/xcuserdata"

XCODEPROJ="$DEST/DJI Clip Cleaner Pro.xcodeproj"

if [[ ! -d "$XCODEPROJ" ]]; then
  echo "ERROR: Xcode project not found at $XCODEPROJ"
  exit 1
fi

echo ""
echo "Checking for Auto-Editor..."
if command -v auto-editor >/dev/null 2>&1; then
  echo "  Auto-Editor found: $(command -v auto-editor)"
else
  echo "  Auto-Editor not installed. Run: brew install auto-editor"
fi

echo ""
echo "Checking for FFmpeg..."
if command -v ffmpeg >/dev/null 2>&1; then
  echo "  FFmpeg found: $(command -v ffmpeg)"
else
  echo "  FFmpeg not installed. Run: brew install ffmpeg"
fi

echo ""
if [[ "${SKIP_OPEN_XCODE:-}" == "1" ]]; then
  echo "Source files updated."
else
  echo "Opening in Xcode..."
  open "$XCODEPROJ"
  echo ""
  echo "Done. Press Cmd+R in Xcode to run."
fi

echo ""
echo "Desktop app after install:"
echo "  ~/Desktop/Hughes Hot Lap.app"
echo ""
echo "To update later, double-click:"
echo "  Desktop/Hughes Hot Lap/Update.command"
echo ""
if [[ -d "$OLD_DEST" ]]; then
  echo "Note: your old DJI Clip Cleaner Pro folder is still on the Desktop."
  echo "You can delete it after confirming Hughes Hot Lap works."
fi
