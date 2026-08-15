#!/usr/bin/env bash
# Restarts whatever scripts/start.sh manages (backend and/or frontend).
#
# Usage: scripts/restart.sh [--backend-only|--frontend-only]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/stop.sh" "$@"
"$SCRIPT_DIR/start.sh" "$@"
