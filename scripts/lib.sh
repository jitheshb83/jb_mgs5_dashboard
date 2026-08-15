#!/usr/bin/env bash
# Shared helpers for start.sh/stop.sh/restart.sh -- not meant to be run directly.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$REPO_ROOT/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"
# Overridable: BACKEND_PORT=9000 FRONTEND_PORT=3000 scripts/start.sh
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

mkdir -p "$RUN_DIR"

# is_running <pid_file> -- true (0) if the file names a live process.
is_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file")"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

# load_env_file <path> -- exports every KEY=VALUE line in a dotenv file into the current
# shell's environment (so a background process launched afterwards inherits them), without
# ever printing the file's contents. Silently does nothing if the file doesn't exist -- callers
# decide whether that's fatal.
load_env_file() {
  local env_file="$1"
  [[ -f "$env_file" ]] || return 1
  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
}

# stop_service <name> <pid_file>
stop_service() {
  local name="$1" pid_file="$2"
  if is_running "$pid_file"; then
    local pid
    pid="$(cat "$pid_file")"
    echo "Stopping $name (pid $pid)..."
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.2
    done
    kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  else
    echo "$name is not running (no live pid in $pid_file)."
  fi
  rm -f "$pid_file"
}
