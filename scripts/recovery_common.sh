#!/usr/bin/env bash
# Shared command boundaries for local backup and explicit restore operations.
DOCKER_BIN="${DOCKER_BIN:-docker}"
compose=("$DOCKER_BIN" compose)
# Operators retain Compose's existing environment behavior. Automated drills
# explicitly select /dev/null and never inspect the normal environment file.
if [[ -n "${COMPOSE_ENV_FILE:-}" ]]; then
  compose+=(--env-file "$COMPOSE_ENV_FILE")
fi
if [[ -n "${COMPOSE_PROJECT_NAME:-}" ]]; then
  compose+=( -p "$COMPOSE_PROJECT_NAME" )
fi
compose+=( -f "${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}" )

recovery_python() {
  local directory="$1"
  shift
  if [[ -z "${RECOVERY_PYTHON_IMAGE:-}" ]] && python3 --version >/dev/null 2>&1; then
    (cd "$directory" && python3 "$ROOT_DIR/scripts/recovery_metadata.py" "$@")
  else
    "$DOCKER_BIN" run --rm --pull never --network none --memory 256m --pids-limit 64 \
      --user "$(id -u):$(id -g)" --read-only --cap-drop ALL \
      --security-opt no-new-privileges:true \
      -v "$ROOT_DIR/scripts:/recovery-scripts:ro" -v "$directory:/recovery-data:rw" \
      -w /recovery-data --entrypoint python "${RECOVERY_PYTHON_IMAGE:-market-intelligence-tools:local}" \
      /recovery-scripts/recovery_metadata.py "$@"
  fi
}

collect_recovery_inventory() {
  "${compose[@]}" exec -T "$POSTGRES_SERVICE" psql -X -qAt \
    -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f - \
    < "$ROOT_DIR/scripts/recovery_inventory.sql"
}
