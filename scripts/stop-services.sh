#!/usr/bin/env bash
# Stop backend and/or frontend started by start-services.sh
# Usage (from repo root):
#   ./scripts/stop-services.sh           # both
#   ./scripts/stop-services.sh backend
#   ./scripts/stop-services.sh frontend
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/services-common.sh
source "$SCRIPT_DIR/lib/services-common.sh"

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET="${1:-all}"

stop_backend() {
  services_stop_pid_file "$(services_pid_file "$PROJECT_ROOT" backend)" "backend"
  services_stop_port 8000 "backend"
}

stop_frontend() {
  services_stop_pid_file "$(services_pid_file "$PROJECT_ROOT" frontend)" "frontend"
  services_stop_port 5173 "frontend"
}

case "$TARGET" in
  backend) stop_backend ;;
  frontend) stop_frontend ;;
  all)
    stop_backend
    stop_frontend
    echo "All services stopped."
    ;;
  *)
    echo "Usage: $0 [backend|frontend|all]"
    exit 1
    ;;
esac
