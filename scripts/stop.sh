#!/usr/bin/env bash
# Stops whatever scripts/start.sh started (backend and/or frontend), by PID file.
#
# Usage: scripts/stop.sh [--backend-only|--frontend-only]

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"

MODE="${1:-}"

case "$MODE" in
  --backend-only)
    stop_service "Backend" "$BACKEND_PID_FILE"
    ;;
  --frontend-only)
    stop_service "Frontend" "$FRONTEND_PID_FILE"
    ;;
  "")
    stop_service "Backend" "$BACKEND_PID_FILE"
    stop_service "Frontend" "$FRONTEND_PID_FILE"
    ;;
  *)
    echo "Unknown option: $MODE (expected --backend-only or --frontend-only)" >&2
    exit 1
    ;;
esac
