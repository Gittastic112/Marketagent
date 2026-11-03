#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
guard="$root/scripts/check_workstream_ownership.sh"
manifest="$root/docs/workstreams/ownership.tsv"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
passed=0
expect_pass() {
  if ! bash "$guard" "$@" >"$scratch/result" 2>&1; then cat "$scratch/result"; exit 1; fi
  passed=$((passed + 1))
}
expect_failure() {
  if bash "$guard" "$@" >"$scratch/result" 2>&1; then
    printf 'Expected ownership rejection.\n' >&2; exit 1
  fi
  passed=$((passed + 1))
}
expect_pass
printf '%s\n' backend/app/services/morning_briefing_engine.py backend/tests/workstreams/w1/test_context.py >"$scratch/paths"
expect_pass --owner W1 --paths "$scratch/paths"
expect_failure --owner W2 --paths "$scratch/paths"
printf '%s\n' backend/app/models/dcf.py >"$scratch/paths"
expect_failure --owner W4 --paths "$scratch/paths"
printf '%s\n' backend/tests/workstreams/w10/test_context.py >"$scratch/paths"
expect_failure --owner W1 --paths "$scratch/paths"
printf '%s\n' ../outside.txt >"$scratch/paths"
expect_failure --owner W1 --paths "$scratch/paths"
cp "$manifest" "$scratch/manifest"
printf 'W2\tfile\tbackend/app/services/morning_briefing_engine.py\n' >>"$scratch/manifest"
expect_failure --manifest "$scratch/manifest"
cp "$manifest" "$scratch/manifest"
printf 'W2\ttree\tbackend/tests/workstreams/\n' >>"$scratch/manifest"
expect_failure --manifest "$scratch/manifest"
sed '/^W5/d' "$manifest" >"$scratch/manifest"
expect_failure --manifest "$scratch/manifest"
expect_failure --owner W1
printf 'Workstream ownership tests passed: %s cases.\n' "$passed"
