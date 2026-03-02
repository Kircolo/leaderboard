#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

if postgres_running; then
  ensure_expected_postgres_cluster
  info "Stopping Postgres."
  "$(postgres_bin pg_ctl)" -D "$POSTGRES_DATA_DIR" stop -m fast
else
  info "Postgres is not running."
fi

if redis_running; then
  info "Stopping Redis."
  redis-cli shutdown
else
  info "Redis is not running."
fi

info "Infrastructure stopped."
