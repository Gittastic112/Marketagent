# Next 10 Execution Checkpoint

Date: 2026-07-31

This records the implementation result for the ten-item sequence in
`world-class-product-ideation-register.md`. It distinguishes a shipped
foundation from full product certification.

## Status Summary

| # | Work item | Status | Evidence | Remaining limit |
|---:|---|---|---|---|
| 1 | Database and document backup/restore | Complete | Versioned custom PostgreSQL archive, manifest, table counts, SHA-256 checksums, retention option, destructive isolated restore drill, and exact document-byte verification | Encryption depends on the storage destination; remote/off-device scheduling is not configured |
| 2 | Exact event/alert locators | Complete foundation | `event_evidence_references`, exact text-span validation, PDF page validation, deterministic extraction references, safe highlighting, and evidence-trail propagation | Historical events need backfill; bounding-box overlays remain limited |
| 3 | AI citation/evaluation/review | Complete foundation | Declared-source citation validation, exact stored-text spans, deterministic evaluation fixtures, prohibited recommendation checks, owner-scoped approve/reject/revision API, and review UI | Generated providers do not yet emit automatic citations; the evaluation corpus is intentionally small |
| 4 | Real-source US/India certification | Blocked on data | Fail-closed manifest/database harness tests source documents, three annual periods, trust-ready normalization, reconciliation, reviewed exact core evidence, mock markers, and both markets | Zero real histories are certified. Synthetic fixtures remain `Mock Data` and cannot pass as product evidence |
| 5 | Accessibility and responsive gates | Complete baseline | CI browser job; six core routes at 1440x900 and 390x844; semantic names/labels, duplicate IDs, image alternatives, keyboard focus, overflow, 12 screenshots, mobile drawer Escape/focus restoration | This is not a full WCAG audit and does not cover every dynamic workflow |
| 6 | Blocking browser dialogs | Complete for known production calls | Production `alert()`/`confirm()` calls replaced with inline status/confirmation; static regression scan added; valuation narrative apply now changes actual form fields | More complex destructive actions could later use a reusable focus-trapped dialog component |
| 7 | Dashboard fanout | Complete HTTP consolidation | `/dashboard/overview` returns owner-scoped alerts, thesis notes, default portfolio and analytics with companies, events, brief, and run health in one request | Representative route/query latency budgets are not yet measured |
| 8 | Point-in-time facts | Partial foundation | Reviewed financial promotions create immutable source-fact revisions with effective, observed, superseded, revision, source-document, and candidate references; `as_of` reads work | Only reviewed financial facts are covered. Market, valuation, thesis, event, and decision histories remain |
| 9 | PostgreSQL full-text search | Partial foundation | GIN indexes for documents/events; `/search/evidence`; typed results, source/timestamp, exact stored-text span when found, company filter, and `/search` UI | Sections, alerts, thesis notes, decisions, valuation notes, ranking explanation, and measured relevance remain |
| 10 | Contradiction/language-change review | Partial foundation | Explicit contradiction links and calculated filing-section changes appear in `/intelligence/review` with separate claim types, severity, and source links | Thesis-assumption mapping, user disposition, ambiguity/support states, exact two-period diff focus, and certified-corpus proof remain |

## Validation

```bash
docker compose exec -w /workspace/backend backend pytest tests -q
# 352 passed, 4 third-party openpyxl warnings

npm --prefix frontend test
# 67 passed

npm --prefix frontend run typecheck
# passed

npm --prefix frontend run build
# optimized production build passed

./scripts/run_browser_workflows.sh
# 8 passed; 12 responsive route screenshots captured

docker compose exec -T backend alembic current
# g3g3g3g3g3g3 (head)
```

The backup/restore drill also completed against an isolated project and restored
the original document bytes after destructive mutation.

The full browser run covers responsive accessibility, mobile focus restoration,
complete and missing alert evidence, PDF upload/review/promotion/reconciliation,
AI provider failure disclosure, invalid CSV recovery, mobile navigation, and the
valuation draft archive-to-promotion lifecycle. It also exposed and fixed a
review-queue contract defect: promoted financial candidates remain stored for
audit history but no longer appear as active extraction-review work.

## New Interfaces

- `GET /dashboard/overview`
- `POST /events/{event_id}/evidence-references`
- `GET /events/{event_id}/evidence-references`
- `GET /evidence-references/{reference_id}`
- `GET /ai-outputs/{output_id}` and citation/evaluation/review actions
- `GET /companies/{company_id}/source-facts?as_of=...`
- `GET /search/evidence?q=...`
- `GET /intelligence/review`
- `/search`
- `/intelligence/review`

## Honest Next Gate

Load and review one real US history and one real India history, create a
non-mock certification manifest, and run:

```bash
docker compose exec -T backend python scripts/certify_financial_histories.py /workspace/path/to/manifest.json
```

Do not remove legacy financial fallback or call the corpus certified until that
report returns `passed` for both `US` and `IN`.
