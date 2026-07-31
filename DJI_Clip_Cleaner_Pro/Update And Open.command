#!/bin/bash
set -euo pipefail

# Legacy name — same flow as Update.command (Desktop rebuild).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/Update.command"
