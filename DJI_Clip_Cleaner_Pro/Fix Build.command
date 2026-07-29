#!/bin/bash
set -euo pipefail

for UPDATE_SCRIPT in \
  "$HOME/Desktop/Hughes Clip Prep/Update.command" \
  "$HOME/Desktop/Hughes Hot Lap/Update.command" \
  "$HOME/Desktop/DJI Clip Cleaner Pro/Update.command"
do
  if [[ -x "$UPDATE_SCRIPT" ]]; then
    exec "$UPDATE_SCRIPT"
  fi
done

osascript -e 'display dialog "Update.command was not found.\n\nPlease download the latest project to:\n~/Desktop/Hughes Clip Prep" buttons {"OK"} with title "Hughes Clip Prep"'
