#!/bin/bash
set -euo pipefail

# Legacy alias — runs the new Update.command flow.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/Update.command"
