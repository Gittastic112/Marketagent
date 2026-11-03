# Backend Suite Recovery Checkpoint

**Date:** 2026-08-24

## Scope

This checkpoint records test-harness and assertion repairs exposed by the first
broad backend runs after the 2026-08-23 feature increment. It does not claim a
new fully green release baseline.

## Repairs

- Removed the `backend/test_models.py` scratch collision that shadowed
  `backend/tests/test_models.py` during collection.
- Added `backend/tests/test_pytest_layout.py` to reject future root/suite
  basename collisions and pytest-style functions inside manual backend scripts.
- Converted `backend/scripts/test_ledger.py` into the non-pytest
  `run_ledger_smoke` utility, updated it to the current
  `generate_change_logs(db, assumption_set)` contract, and isolated it on an
  in-memory database so it cannot mutate the configured local database.
- Added `backend/tests/test_assumption_diff_service.py` as the durable ledger
  behavior test.
- Raised the Daily Brief API fixture from priority 70 to 90 so it genuinely
  exercises the engine's `>= 80` high-materiality boundary.
- Corrected the fixture's valuation-analysis assertion to `not_run`. A material
  event has work to analyze, but deterministic GET does not invoke AI.
  `not_required` remains covered separately by a below-threshold event.

## Recorded Runtime Evidence

- The user rebuilt the backend image successfully.
- PostgreSQL reported healthy and the backend container started.
- The first repaired broad run reached 581 passes and two failures.
- After the collection and threshold fixes, the focused run reached 6 passes
  and one failure, and the broad run reached 583 passes and the same one failure.
- That final failure was the `not_run` versus `not_required` assertion described
  above. It is corrected in source but has not yet been rerun in Docker.
- Four non-failing `openpyxl` deprecation warnings remain under Python 3.14.

## Source-Level Validation

- Changed Python files compile.
- Pytest layout guards pass when executed directly.
- Project skill validation passes for all 11 skills.
- Documentation validation passes.
- Changed-file whitespace validation passes.

## Final Runtime Result

Run from the repository root because the production backend image does not
bind-mount source code:

```bash
docker compose up -d --build backend
docker compose exec -w /workspace/backend backend pytest -q tests/test_api_daily_brief.py tests/test_pytest_layout.py tests/test_assumption_diff_service.py
docker compose exec -w /workspace/backend backend pytest -q
```

The rebuilt backend run completed on 2026-08-24:

- Focused recovery command: 7 passed.
- Full backend suite: 584 passed in 57.58 seconds.
- Warnings: four upstream `openpyxl` deprecation warnings under Python 3.14.
- Migration upgrade completed before the test run.

The backend-suite recovery gate is closed.
