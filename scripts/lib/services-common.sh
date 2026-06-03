#!/usr/bin/env bash
# Shared helpers for start/stop service scripts (Linux, macOS, WSL, cloud agents).

services_ensure_dirs() {
  local root="$1"
  mkdir -p "$root/.run" "$root/.logs"
}

services_pid_file() {
  local root="$1"
  local name="$2"
  echo "$root/.run/${name}.pid"
}

services_log_file() {
  local root="$1"
  local name="$2"
  echo "$root/.logs/${name}.log"
}

services_is_running() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

services_stop_pid_file() {
  local pid_file="$1"
  local label="$2"
  if services_is_running "$pid_file"; then
    local pid
    pid="$(cat "$pid_file")"
    echo "Stopping $label (PID $pid)..."
    kill "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  fi
  rm -f "$pid_file"
}

services_stop_port() {
  local port="$1"
  local label="$2"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti ":$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      echo "Stopping $label on port $port..."
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
      sleep 1
      # shellcheck disable=SC2086
      kill -9 $pids 2>/dev/null || true
    fi
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" 2>/dev/null || true
  fi
}

services_wait_for_url() {
  local url="$1"
  local label="$2"
  local attempts="${3:-30}"
  local i
  for ((i = 1; i <= attempts; i++)); do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "$label is up: $url"
      return 0
    fi
    sleep 1
  done
  echo "WARNING: $label did not respond at $url within ${attempts}s (check logs in .logs/)"
  return 1
}

services_check_backend_venv() {
  local backend_dir="$1"
  if [[ ! -f "$backend_dir/venv/bin/activate" ]]; then
    echo "ERROR: $backend_dir/venv not found."
    echo "Create it:"
    echo "  cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
  fi
}

services_check_frontend_deps() {
  local frontend_dir="$1"
  if [[ ! -d "$frontend_dir/node_modules" ]]; then
    echo "ERROR: frontend/node_modules not found."
    echo "Run: cd frontend && npm install"
    exit 1
  fi
}
