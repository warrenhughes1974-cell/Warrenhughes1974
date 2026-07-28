#!/bin/bash
set -euo pipefail

# Installs DJI Clip Cleaner Pro to your Desktop and opens it in Xcode.
# Run from Terminal on your Mac after cloning the repo.

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/Desktop/DJI Clip Cleaner Pro"
BACKUP=""

if [[ -d "$DEST" ]]; then
  BACKUP="$HOME/Desktop/DJI Clip Cleaner Pro.backup.$(date +%Y%m%d-%H%M%S)"
  echo "Backing up existing project to:"
  echo "  $BACKUP"
  mv "$DEST" "$BACKUP"
fi

echo "Installing fresh project to:"
echo "  $DEST"

mkdir -p "$DEST"
ditto "$REPO_ROOT" "$DEST"

XCODEPROJ="$DEST/DJI Clip Cleaner Pro.xcodeproj"

if [[ ! -d "$XCODEPROJ" ]]; then
  echo "ERROR: Xcode project not found at $XCODEPROJ"
  exit 1
fi

echo ""
echo "Checking for Auto-Editor..."
if command -v auto-editor >/dev/null 2>&1; then
  echo "  Auto-Editor found: $(command -v auto-editor)"
  auto-editor --version || true
else
  echo "  Auto-Editor not installed."
  echo "  Install with: brew install auto-editor"
fi

echo ""
echo "Opening in Xcode..."
open "$XCODEPROJ"

echo ""
echo "Done."
echo "  1. In Xcode, select the 'DJI Clip Cleaner Pro' scheme."
echo "  2. Press Cmd+R to build and run."
if [[ -n "$BACKUP" ]]; then
  echo ""
  echo "Your old project was backed up to:"
  echo "  $BACKUP"
fi
