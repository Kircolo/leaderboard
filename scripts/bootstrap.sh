#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

bash "$SCRIPT_DIR/doctor.sh"
bash "$SCRIPT_DIR/infra_up.sh"
ensure_env_file

info "Running database migrations."
(
  cd "$ROOT_DIR"
  alembic upgrade head
)

info "Bootstrap complete."

