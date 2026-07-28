#!/bin/bash
set -euo pipefail

DESKTOP="$HOME/Desktop"

trash_item() {
  local path="$1"
  if [[ -e "$path" ]]; then
    echo "Trash: $(basename "$path")"
    osascript -e "tell application \"Finder\" to delete POSIX file \"$path\"" >/dev/null
  fi
}

echo "=== DJI Clip Cleaner Pro — Desktop Cleanup ==="
echo ""
echo "KEEPING:"
echo "  Desktop/DJI Clip Cleaner Pro/"
echo ""
echo "REMOVING (moving to Trash):"
echo ""

# Huge full repo clone — not needed anymore (updates use /tmp)
trash_item "$DESKTOP/Warrenhughes1974-temp"
trash_item "$DESKTOP/Warrenhughes1974"

# Duplicate / old project copies
trash_item "$DESKTOP/DJI Clip Cleaner Pro 2"
for item in "$DESKTOP"/DJI\ Clip\ Cleaner\ Pro.backup.*; do
  [[ -e "$item" ]] && trash_item "$item"
done

# Old standalone scripts on Desktop (now live inside the project folder)
trash_item "$DESKTOP/Fix Build.command"
trash_item "$DESKTOP/Update Everything.command"
trash_item "$DESKTOP/Cleanup Desktop.command"
trash_item "$DESKTOP/DJI_Old_Stuff_Archive"

# Old script names inside project if duplicated at desktop root
trash_item "$DESKTOP/Update.command"

echo ""
echo "Done."
echo ""
echo "Your Desktop should now have only:"
echo "  DJI Clip Cleaner Pro/"
echo ""
echo "Inside that folder:"
echo "  • DJI Clip Cleaner Pro.xcodeproj  (double-click to open)"
echo "  • Update.command                  (double-click for updates)"
echo ""

osascript -e 'display notification "Desktop cleaned. Only DJI Clip Cleaner Pro folder kept." with title "Desktop Cleanup"'
