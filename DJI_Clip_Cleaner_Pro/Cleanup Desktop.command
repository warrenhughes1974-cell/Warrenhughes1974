#!/bin/bash
set -euo pipefail

DESKTOP="$HOME/Desktop"
ARCHIVE="$DESKTOP/DJI_Old_Stuff_Archive"
KEEP_PROJECT="$DESKTOP/DJI Clip Cleaner Pro"
KEEP_REPO="$DESKTOP/Warrenhughes1974-temp"

mkdir -p "$ARCHIVE"

move_if_exists() {
  local path="$1"
  local label="$2"

  if [[ -e "$path" ]]; then
    local name
    name="$(basename "$path")"
    echo "Archiving: $label → $ARCHIVE/$name"
    mv "$path" "$ARCHIVE/"
  fi
}

echo "=== DJI Clip Cleaner Pro — Desktop Cleanup ==="
echo ""
echo "Keeping:"
echo "  • DJI Clip Cleaner Pro          (your app)"
echo "  • Warrenhughes1974-temp           (for updates)"
echo "  • Fix Build.command               (quick fixes)"
echo "  • Update Everything.command       (full updates)"
echo ""
echo "Archiving old copies into:"
echo "  $ARCHIVE"
echo ""

# Old duplicate project folders from install script backups
for item in "$DESKTOP"/DJI\ Clip\ Cleaner\ Pro.backup.*; do
  [[ -e "$item" ]] && move_if_exists "$item" "backup folder"
done

move_if_exists "$DESKTOP/DJI Clip Cleaner Pro 2" "old duplicate project"

# Old temp clone names if any
move_if_exists "$DESKTOP/Warrenhughes1974" "old repo clone (no -temp suffix)"

echo ""
echo "Done."
echo ""
echo "Archived items are in:"
echo "  $ARCHIVE"
echo ""
echo "To permanently delete them later:"
echo "  1. Open Finder → Desktop → DJI_Old_Stuff_Archive"
echo "  2. Select all → Move to Trash"
echo ""

open "$ARCHIVE" 2>/dev/null || true

osascript -e 'display notification "Old DJI copies moved to DJI_Old_Stuff_Archive on Desktop." with title "Desktop Cleanup"'
