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
recovery_separator="${COMPOSE_PATH_SEPARATOR:-:}"
recovery_file_list="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}"
if [[ ${#recovery_separator} -ne 1 || "$recovery_file_list" == *$'\n'* ||
      "$recovery_file_list" == "$recovery_separator"* ||
      "$recovery_file_list" == *"$recovery_separator" ||
      "$recovery_file_list" == *"$recovery_separator$recovery_separator"* ]]; then
  printf 'Compose file list has an invalid separator or empty entry.\n' >&2
  exit 2
fi
IFS="$recovery_separator" read -r -a recovery_files <<< "$recovery_file_list"
recovery_config_label=""
for recovery_file in "${recovery_files[@]}"; do
  if [[ ! -f "$recovery_file" || ! -r "$recovery_file" || "$recovery_file" == *,* ]]; then
    printf 'Compose file is missing, unreadable or has an ambiguous comma in its path.\n' >&2
    exit 2
  fi
  recovery_file="$(cd "$(dirname "$recovery_file")" && pwd -P)/$(basename "$recovery_file")"
  compose+=(-f "$recovery_file")
  recovery_config_label+="${recovery_config_label:+,}$recovery_file"
done

verify_recovery_target() {
  # Never print resolved configuration: it may contain credentials.
  "${compose[@]}" config --quiet
  local container installed_files
  container="$("${compose[@]}" ps -q "$POSTGRES_SERVICE")"
  if [[ ! "$container" =~ ^[a-f0-9]{64}$ ]]; then
    printf 'Select exactly one running database service before recovery.\n' >&2
    return 1
  fi
  installed_files="$("$DOCKER_BIN" inspect --format '{{ index .Config.Labels "com.docker.compose.project.config_files" }}' "$container")"
  if [[ "$installed_files" != "$recovery_config_label" ]]; then
    printf 'Recovery requires the same ordered Compose files as the installed database.\n' >&2
    return 1
  fi
}

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
