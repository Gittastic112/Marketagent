#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.e2e.yml"
PROJECT_NAME="market-intel-e2e"
E2E_FRONTEND_PORT="${E2E_FRONTEND_PORT:-13000}"
E2E_BACKEND_PORT="${E2E_BACKEND_PORT:-18000}"
COMPOSE=(docker compose --env-file /dev/null -p "$PROJECT_NAME" -f "$COMPOSE_FILE")

# The isolated project must never require or load normal application credentials.
export NEXTAUTH_SECRET="${NEXTAUTH_SECRET:-browser-check-secret-not-for-production}"
export LOCAL_AUTH_USERNAME="${LOCAL_AUTH_USERNAME:-browser-check-user}"
export LOCAL_AUTH_PASSWORD="${LOCAL_AUTH_PASSWORD:-browser-check-password}"

cleanup() {
  "${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
}
for port in "$E2E_FRONTEND_PORT" "$E2E_BACKEND_PORT"; do
  if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    printf 'Port %s is already allocated. Stop the owning service or override E2E_FRONTEND_PORT/E2E_BACKEND_PORT.\n' "$port" >&2
    exit 1
  fi
done

trap cleanup EXIT INT TERM
cleanup

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

# Real row/advisory locking cannot be proven by the default SQLite suite.
# The test allocates its own random schema inside this disposable database.
"${COMPOSE[@]}" exec -T \
  -e INGESTION_TEST_DATABASE_URL=postgresql+psycopg://marketintel:marketintel_password@postgres-e2e:5432/marketintel_e2e \
  backend-e2e pytest -q -p no:cacheprovider backend/tests/integration/test_ingestion_postgres.py

cd "$ROOT_DIR/frontend"
E2E_BASE_URL="http://127.0.0.1:${E2E_FRONTEND_PORT}" npx --no-install playwright test "$@"
