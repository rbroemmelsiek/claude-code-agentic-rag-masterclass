#!/usr/bin/env bash
# Start backend and/or frontend (background by default — for cloud agents and CI).
# Usage (from repo root):
#   ./scripts/start-services.sh              # both
#   ./scripts/start-services.sh backend
#   ./scripts/start-services.sh frontend
#   ./scripts/start-services.sh all --foreground   # blocking (one service only per shell)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/services-common.sh
source "$SCRIPT_DIR/lib/services-common.sh"

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUN_DIR="$PROJECT_ROOT/.run"
LOG_DIR="$PROJECT_ROOT/.logs"
TARGET="${1:-all}"
FOREGROUND=false

if [[ "${2:-}" == "--foreground" || "${1:-}" == "--foreground" ]]; then
  FOREGROUND=true
  if [[ "${1:-}" == "--foreground" ]]; then
    TARGET="all"
  fi
fi

services_ensure_dirs "$PROJECT_ROOT"

start_backend_bg() {
  local backend_dir="$PROJECT_ROOT/backend"
  local pid_file
  pid_file="$(services_pid_file "$PROJECT_ROOT" backend)"
  services_check_backend_venv "$backend_dir"

  if services_is_running "$pid_file"; then
    echo "Backend already running (PID $(cat "$pid_file"))"
    return 0
  fi

  cd "$backend_dir"
  # shellcheck source=/dev/null
  source venv/bin/activate
  nohup python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
    >"$(services_log_file "$PROJECT_ROOT" backend)" 2>&1 &
  echo $! >"$pid_file"
  echo "Backend started (PID $(cat "$pid_file")) — http://localhost:8000"
  echo "  log: $(services_log_file "$PROJECT_ROOT" backend)"
}

start_backend_fg() {
  local backend_dir="$PROJECT_ROOT/backend"
  services_check_backend_venv "$backend_dir"
  cd "$backend_dir"
  # shellcheck source=/dev/null
  source venv/bin/activate
  exec python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

start_frontend_bg() {
  local frontend_dir="$PROJECT_ROOT/frontend"
  local pid_file
  pid_file="$(services_pid_file "$PROJECT_ROOT" frontend)"
  services_check_frontend_deps "$frontend_dir"

  if services_is_running "$pid_file"; then
    echo "Frontend already running (PID $(cat "$pid_file"))"
    return 0
  fi

  cd "$frontend_dir"
  nohup npm run dev >"$(services_log_file "$PROJECT_ROOT" frontend)" 2>&1 &
  echo $! >"$pid_file"
  echo "Frontend started (PID $(cat "$pid_file")) — http://localhost:5173"
  echo "  log: $(services_log_file "$PROJECT_ROOT" frontend)"
}

start_frontend_fg() {
  local frontend_dir="$PROJECT_ROOT/frontend"
  services_check_frontend_deps "$frontend_dir"
  cd "$frontend_dir"
  exec npm run dev
}

case "$TARGET" in
  backend)
    if $FOREGROUND; then start_backend_fg; else start_backend_bg; fi
    ;;
  frontend)
    if $FOREGROUND; then start_frontend_fg; else start_frontend_fg; fi
    ;;
  all)
    if $FOREGROUND; then
      echo "ERROR: --foreground with 'all' is not supported. Start backend and frontend in separate terminals."
      exit 1
    fi
    start_backend_bg
    start_frontend_bg
    services_wait_for_url "http://localhost:8000/health" "Backend" 45 || true
    services_wait_for_url "http://localhost:5173/" "Frontend" 45 || true
    ;;
  *)
    echo "Usage: $0 [backend|frontend|all] [--foreground]"
    exit 1
    ;;
esac
