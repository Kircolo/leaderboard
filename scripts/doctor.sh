#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

require_command python3
require_command brew
require_command redis-server
require_command redis-cli
require_command alembic
require_command uvicorn
require_command jq

brew list --versions "$POSTGRES_FORMULA" >/dev/null 2>&1 || fail "Install $POSTGRES_FORMULA with Homebrew."
brew list --versions redis >/dev/null 2>&1 || fail "Install redis with Homebrew."

info "python3: $(python3 --version 2>&1)"
info "brew: $(brew --version | head -n 1)"
info "postgresql@16: $(brew list --versions "$POSTGRES_FORMULA")"
info "redis: $(brew list --versions redis)"
info "alembic: $(alembic --version 2>&1)"
info "uvicorn: $(uvicorn --version 2>&1)"
info "jq: $(jq --version)"
info "Postgres bin dir: $(postgres_bin_dir)"
info "Doctor checks passed."

