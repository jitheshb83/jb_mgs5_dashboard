#!/usr/bin/env bash
# Starts the backend (FastAPI/uvicorn, port 8000) and frontend (Vite dev server, port 5173)
# for local testing, matching the manual steps in README.md. Both run in the background;
# logs go to .run/*.log, PIDs to .run/*.pid (gitignored). Re-running this is safe -- an
# already-running service is left alone rather than double-started.
#
# Usage: scripts/start.sh [--backend-only|--frontend-only]

set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib.sh"

MODE="${1:-}"

start_backend() {
  if is_running "$BACKEND_PID_FILE"; then
    echo "Backend already running (pid $(cat "$BACKEND_PID_FILE")) at http://localhost:$BACKEND_PORT"
    return
  fi
  echo "Starting backend..."
  (
    cd "$REPO_ROOT/backend"
    # Export every var from backend/.env (SAIC_USERNAME, SAIC_PASSWORD, SAIC_REGION,
    # DATABASE_PATH -- see backend/.env.example) into this subshell so the uvicorn process
    # launched below inherits them directly, rather than relying solely on app/config.py's
    # own load_dotenv() call. Never printed -- load_env_file only sources the file.
    if load_env_file "$REPO_ROOT/backend/.env"; then
      : # loaded
    else
      echo "Warning: backend/.env not found (copy backend/.env.example and fill in SAIC credentials)." >&2
    fi
    nohup uv run uvicorn app.main:app --app-dir src --port "$BACKEND_PORT" \
      > "$BACKEND_LOG" 2>&1 &
    echo $! > "$BACKEND_PID_FILE"
  )
  echo "Backend starting (pid $(cat "$BACKEND_PID_FILE")), log: $BACKEND_LOG"
}

start_frontend() {
  if is_running "$FRONTEND_PID_FILE"; then
    echo "Frontend already running (pid $(cat "$FRONTEND_PID_FILE")) at http://localhost:$FRONTEND_PORT"
    return
  fi
  echo "Starting frontend..."
  (
    cd "$REPO_ROOT/frontend"
    nohup npm run dev -- --port "$FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
  )
  echo "Frontend starting (pid $(cat "$FRONTEND_PID_FILE")), log: $FRONTEND_LOG"
}

case "$MODE" in
  --backend-only)
    start_backend
    ;;
  --frontend-only)
    start_frontend
    ;;
  "")
    start_backend
    start_frontend
    ;;
  *)
    echo "Unknown option: $MODE (expected --backend-only or --frontend-only)" >&2
    exit 1
    ;;
esac

sleep 1
echo
echo "Backend:  http://localhost:$BACKEND_PORT  (docs at /docs)"
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Logs:     $RUN_DIR"
echo "Stop with: scripts/stop.sh"
