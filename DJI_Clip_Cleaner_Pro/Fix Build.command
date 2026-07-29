#!/bin/bash
set -euo pipefail

UPDATE_SCRIPT="$HOME/Desktop/DJI Clip Cleaner Pro/Update.command"

if [[ -x "$UPDATE_SCRIPT" ]]; then
  exec "$UPDATE_SCRIPT"
fi

osascript -e 'display dialog "Update.command was not found.\n\nPlease download the latest project to:\n~/Desktop/DJI Clip Cleaner Pro" buttons {"OK"} with title "Fix Build"'
