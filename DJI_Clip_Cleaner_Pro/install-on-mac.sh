#!/bin/bash
set -euo pipefail

# Installs or updates Hughes Clip Prep on your Desktop.

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/Desktop/Hughes Clip Prep"
OLD_DEST_HOT_LAP="$HOME/Desktop/Hughes Hot Lap"
OLD_DEST_DJI="$HOME/Desktop/DJI Clip Cleaner Pro"

echo "Installing to:"
echo "  $DEST"

mkdir -p "$DEST"
ditto "$REPO_ROOT" "$DEST"

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
echo "  ~/Desktop/Hughes Clip Prep.app"
echo ""
echo "To update later, double-click:"
echo "  Desktop/Hughes Clip Prep/Update.command"
echo ""
if [[ -d "$OLD_DEST_HOT_LAP" || -d "$OLD_DEST_DJI" ]]; then
  echo "Note: older app folders may still be on your Desktop."
  echo "You can delete them after confirming Hughes Clip Prep works."
fi
