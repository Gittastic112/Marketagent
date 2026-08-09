# Next 10 Execution Checkpoint

Date: 2026-08-01

This checkpoint records the ten reliability and product-integrity tasks started
after the 2026-07-31 batch. Statuses describe verified foundations, not full
world-class completion.

## Status Summary

| # | Work item | Status | Evidence | Remaining limit |
|---:|---|---|---|---|
| 1 | Reconcile the capability register | Complete | Stale browser, reliability, transfer, evidence, and performance claims now match code and tests | The dated 58%/47% product score was not recalculated |
| 2 | Repository secret scan | Complete baseline | Credential-shaped tokens and quoted credential assignments are scanned without echoing values; placeholders and deterministic test credentials are explicitly handled | This is pattern detection, not full history scanning or entropy analysis |
| 3 | Static local/CI quality gates | Complete baseline | Scanner tests, repository scan, project-skill validation, TypeScript, frontend integrity checks, and release checks run locally/CI | A framework ESLint migration is not included |
| 4 | Dashboard performance budget | Complete first route | `/dashboard/overview` uses explicit relationship loading and is tested at no more than 20 SQL statements and 1,000 ms backend generation time | Search, browser render, large-table, and concurrent-load budgets remain |
| 5 | Evidence-integrity API | Complete bounded foundation | Authenticated report checks timestamps, links, asset size/hash, company consistency, text spans/quotes, PDF pages/regions, and low confidence; results cap at 200 | No external dead-link requests, repair actions, scheduler, or full ownership audit |
| 6 | Evidence-integrity UI | Complete foundation | `/data-health` shows status/counts, limitations, corrective actions, and document links | No trend history, alerting, or bulk repair |
| 7 | Company setup workflow | Complete browser baseline | Taxonomy contains real options, selected Damodaran mapping persists, creation redirects to the company workspace, and backend state is verified | India identity/filings remain provider dependent |
| 8 | SEC readiness and failed ingestion | Complete deterministic baseline | CIK-less SEC controls remain disabled; an SSRF-blocked RSS run surfaces as failed in Data Health | Mutable live SEC/RSS provider behavior is intentionally not asserted |
| 9 | Valid CSV transfer | Complete market-price baseline | Browser verifies preview, atomic apply, backend row, download name, and exported content; invalid-row recovery remains covered | Other CSV domains do not all have equivalent browser proof |
| 10 | Valuation and partial-dashboard failures | Complete baseline | Edits invalidate review, stale updates surface reload guidance, and missing holding prices produce a partial warning plus `Add Prices` action | Concurrent multi-tab behavior and every portfolio mutation remain uncovered |

## Validation

```bash
python3 -m unittest scripts.test_check_secrets
python3 scripts/check_secrets.py
python3 scripts/validate_project_skills.py
docker compose exec backend pytest -q
# 355 passed; 4 third-party openpyxl warnings

npm --prefix frontend test
# 68 passed

npm --prefix frontend run typecheck
npm --prefix frontend run build
bash scripts/run_browser_workflows.sh
# 13 passed in one disposable-stack run
```

Focused backend tests cover the dashboard query/latency contract and healthy and
corrupt evidence-integrity reports. The full backend/frontend regression counts
above include those tests.

## New Interfaces

- `GET /data-health/evidence-integrity`
- Evidence Integrity section on `/data-health`
- `scripts/check_secrets.py`
- `scripts/test_check_secrets.py`
- `scripts/seed_e2e_reference_data.py` for isolated `Mock Data` E2E taxonomy only
- `frontend/e2e/reliability-workflows.spec.ts`

## Honest Next Gate

The product still has zero certified real-source US/India financial histories.
The next trust milestone is not another dashboard feature: load, review,
reconcile, and certify one representative history in each market with exact
core-metric evidence. In parallel, expand performance measurement beyond the
dashboard and add scheduled evidence-health history only after a background-run
control model exists.
