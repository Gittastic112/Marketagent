#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.e2e.yml"
PROJECT_NAME="market-intel-e2e"
E2E_FRONTEND_PORT="${E2E_FRONTEND_PORT:-13000}"
E2E_BACKEND_PORT="${E2E_BACKEND_PORT:-18000}"
COMPOSE=(docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE")

cleanup() {
  "${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

if [[ ! -f "$ROOT_DIR/.env" ]] && {
  [[ -z "${NEXTAUTH_SECRET:-}" ]] \
    || [[ -z "${LOCAL_AUTH_USERNAME:-}" ]] \
    || [[ -z "${LOCAL_AUTH_PASSWORD:-}" ]];
}; then
  printf 'Configure local auth in %s/.env or export NEXTAUTH_SECRET, LOCAL_AUTH_USERNAME, and LOCAL_AUTH_PASSWORD.\n' "$ROOT_DIR" >&2
  exit 1
fi

cleanup

for port in "$E2E_FRONTEND_PORT" "$E2E_BACKEND_PORT"; do
  if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    printf 'Port %s is already allocated. Stop the owning service or override E2E_FRONTEND_PORT/E2E_BACKEND_PORT.\n' "$port" >&2
    exit 1
  fi
done

E2E_FRONTEND_PORT="$E2E_FRONTEND_PORT" E2E_BACKEND_PORT="$E2E_BACKEND_PORT" \
  "${COMPOSE[@]}" up --build --detach

for _ in $(seq 1 90); do
  if curl --fail --silent "http://127.0.0.1:${E2E_BACKEND_PORT}/api/readiness" >/dev/null \
    && curl --fail --silent "http://127.0.0.1:${E2E_FRONTEND_PORT}/api/auth/readiness" >/dev/null; then
    break
  fi
  sleep 2
done

if ! curl --fail --silent "http://127.0.0.1:${E2E_BACKEND_PORT}/api/readiness" >/dev/null; then
  "${COMPOSE[@]}" logs --tail=120 backend-e2e >&2
  exit 1
fi
if ! curl --fail --silent "http://127.0.0.1:${E2E_FRONTEND_PORT}/api/auth/readiness" >/dev/null; then
  "${COMPOSE[@]}" logs --tail=120 frontend-e2e >&2
  exit 1
fi

"${COMPOSE[@]}" exec -T backend-e2e python scripts/seed_e2e_reference_data.py

cd "$ROOT_DIR/frontend"
E2E_BASE_URL="http://127.0.0.1:${E2E_FRONTEND_PORT}" npx playwright test "$@"
