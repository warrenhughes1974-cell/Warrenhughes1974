#!/bin/bash
set -euo pipefail

UPDATE_SCRIPT="$HOME/Desktop/Hughes Hot Lap/Update.command"
LEGACY_UPDATE_SCRIPT="$HOME/Desktop/DJI Clip Cleaner Pro/Update.command"

if [[ -x "$UPDATE_SCRIPT" ]]; then
  exec "$UPDATE_SCRIPT"
fi

if [[ -x "$LEGACY_UPDATE_SCRIPT" ]]; then
  exec "$LEGACY_UPDATE_SCRIPT"
fi

osascript -e 'display dialog "Update.command was not found.\n\nPlease download the latest project to:\n~/Desktop/Hughes Hot Lap" buttons {"OK"} with title "Hughes Hot Lap"'
