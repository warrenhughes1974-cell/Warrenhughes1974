#!/bin/bash
set -euo pipefail

# Installs or updates DJI Clip Cleaner Pro on your Desktop.

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/Desktop/DJI Clip Cleaner Pro"

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
echo "Opening in Xcode..."
open "$XCODEPROJ"

echo ""
echo "Done. Press Cmd+R in Xcode to run."
echo ""
echo "To update later, double-click:"
echo "  Desktop/DJI Clip Cleaner Pro/Update.command"
