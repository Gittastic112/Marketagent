# Unified Stored-Research Search Checkpoint

**Date:** 2026-08-23

## Delivered Boundary

- Expanded `GET /search/evidence` from six to ten primary record types:
  documents, events, alerts, thesis notes, decisions, valuations, narratives,
  research sessions, user research messages, and reviewed AI output.
- Added explicit result `scope`, `review_status`, `is_mock`, and
  `AI Interpretation` contracts.
- Preserved the existing shared scope for documents, events, and narratives.
- Enforced authenticated ownership for alerts, theses, decisions, valuations,
  research sessions/messages, and AI output.
- Indexed only user-authored research messages. Assistant text becomes
  searchable only through its owned AI output after successful execution,
  human approval, a non-blocked state, and a stored review timestamp.
- Excluded pending, blocked, failed, unreviewed, and cross-user AI output.
- Bounded all excerpts to 280 characters and kept a global result limit.
- Deduplicated direct narrative and narrative-claim matches by cluster.
- Preserved PostgreSQL full-text search and SQLite test fallback behavior.
- Added responsive result cards, visible Shared/Private, claim-type, review, and
  Mock Data badges, unavailable and short-query states, and stable record
  anchors.
- Extended the authenticated browser workflow for narrative and private-session
  results.

## Additional Regression Repair

The user accidentally ran the full backend suite while attempting the focused
AI citation command. It reached 567 passes and exposed four stale tests. The
worktree now:

- expects `not_required` when Daily Brief valuation analysis has no applicable
  work;
- checks the current deterministic dashboard summary;
- removes a monkeypatch for the deleted per-event price helper; and
- stores ORM IDs before closing the SQLAlchemy session.

Those four corrections were exercised in later Docker runs; subsequent
collection and Daily Brief contract repairs are recorded below.

The subsequent full-suite collection collision was traced to an untracked
`backend/test_models.py` scratch stub shadowing the real
`backend/tests/test_models.py`. The scratch stub was removed and
`backend/tests/test_pytest_layout.py` now rejects future basename collisions.

A later rebuilt-container run reached 581 passes and two failures. The ledger
failure was not an application regression: `backend/scripts/test_ledger.py` was
a manual utility exposed as a pytest test, used an obsolete service signature,
and wrote into the configured database. It now uses an isolated in-memory
database and a `run_ledger_smoke` entry point; the real behavior is covered by
`backend/tests/test_assumption_diff_service.py`. The remaining Daily Brief test
fixture scored its event at 70 while the engine correctly requires 80 for the
high-materiality list. The fixture now scores 90. The collection guard also
rejects future `test_*` functions in manual backend scripts.

The next rebuilt run passed 583 tests and isolated one assertion mismatch. Once
the fixture became high materiality, deterministic GET correctly changed its
valuation-analysis state from `not_required` to `not_run`: work exists, but the
read path deliberately does not invoke AI. The API assertion now reflects that
contract. `test_persisted_daily_brief.py` still covers `not_required` with a
below-threshold event, so the two states cannot silently collapse together.

## Validation

- Backend changed-file compile: passed.
- Frontend TypeScript: passed.
- Frontend tests: 122 passed.
- Project skill validation: 11 passed.
- Documentation validation: 62 active Markdown files and 279 local links passed;
  all four documentation-checker unit tests passed.
- The explicit security skill frontmatter and `agents/openai.yaml` parsed with
  implicit invocation enabled. The bundled quick validator could not import
  PyYAML, so equivalent YAML and policy checks ran with the system YAML parser.
- Damodaran knowledge-base audit: status `ok`, 61 canonical raw files, 61 source
  catalog rows, 38 processing-ledger rows, and no pending inbox files.
- `git diff --check` for changed application/test files: passed.
- Backend coverage: all search and AI citation tests passed inside the latest
  broad run, which reached 583 passes and one unrelated Daily Brief assertion.
  That assertion is corrected; the final full-suite rerun remains pending.
- Authenticated search browser workflow: passed, 1 test in 11.3 seconds as
  reported by the user.
- Production build: not rerun; the host build remains blocked by protected
  environment metadata and Docker-owned Next build artifacts.

## User-Run Gate

Rebuild first because the production container does not bind-mount source code.
Then run from the repository root. The explicit working directory makes test
paths unambiguous.

```bash
docker compose up -d --build backend
docker compose exec -w /workspace/backend backend pytest -q tests/test_pytest_layout.py tests/test_assumption_diff_service.py tests/test_api_evidence_search.py tests/test_ai_citation_suggestions.py tests/test_ai_citations.py tests/test_api_daily_brief.py tests/test_api_dashboard_overview.py tests/test_daily_brief.py
cd frontend
npm run test:e2e -- search-workflows.spec.ts
```

Then run the full backend suite:

```bash
cd ..
docker compose exec -w /workspace/backend backend pytest -q
```

Passing search tests proves access boundaries, filters, bounded excerpts, and
navigation contracts. It does not make narrative or AI interpretations factual
or prove semantic entailment.
