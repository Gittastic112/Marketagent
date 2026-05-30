# Execution Runbook & Implementation Checklist

This checklist supersedes older development plans and outlines the strict order of implementation required to align the application with the new frontend and backend design brief. It also serves as a runbook with validation steps.

## Operating Rules & Avoiding Giant Diffs
- **Keep tasks narrow:** Do not rewrite the entire frontend or backend in one go.
- **Incremental PRs/Commits:** Commit after *every* phase. 
- **Explain files touched:** After each phase, output a brief summary of the exact files changed and the manual tests performed.
- **Rollback:** If a phase breaks the app, use `git checkout .` to revert to the previous phase checkpoint rather than adding more complexity.

---

## Phase 0: Audit & Documentation (Completed)
- [x] Audit the current codebase against the design brief.
- [x] Create an execution plan.
- [x] Consolidate and amend all existing markdown documents.

## Phase 1: Stabilize local dev
- [x] Ensure Docker startup works flawlessly.
- [x] Confirm Alembic migration chain is unbroken and local DB spins up.
- [x] Add `GET /api/health` endpoint and verify backend health.
- **Validation:** Run `docker compose up --build -d`. Visit `http://localhost:8000/api/health`.
- **Checkpoint Command:** `git add . && git commit -m "chore: stabilize local dev and add healthcheck"`

## Phase 2: API Response Envelope
- [x] Add the standard `{"data", "meta", "errors"}` response envelope schema to the backend.
- [x] Refactor all existing FastAPI routes to use this envelope.
- [x] Update frontend `fetchApi` client to parse this envelope.
- **Validation:** Write unit tests to confirm the `{"data", "meta", "errors"}` wrapper correctly wraps success and error responses. Verify frontend `fetchApi` parses it correctly without white-screening.
- **Checkpoint Command:** `git add . && git commit -m "feat: standard api response envelope"`

## Phase 3: Processing Runs and Ingestion Status
- [x] Create `processing_runs` table and models.
- [x] Update SEC and RSS services to track ingestion health to `processing_runs`.
- [x] Create `GET /api/ingestion/status` endpoint.
- **Validation:** Trigger an SEC or RSS fetch. Query the DB or check the `GET /api/ingestion/status` endpoint to ensure the run was logged successfully.
- **Checkpoint Command:** `git add . && git commit -m "feat: processing runs tracking"`

## Phase 4: SEC User-Agent and CIK Lookup
- [x] Add `SEC_USER_AGENT` environment variable validation.
- [x] Create `GET /api/sec/company/{ticker}/cik` endpoint.
- **Validation:** Remove the `SEC_USER_AGENT` from `.env` and verify the ingestion fails gracefully with a standard error. Put it back and verify success.
- **Checkpoint Command:** `git add . && git commit -m "feat: sec user agent and cik lookup"`

## Phase 5: Frontend App Shell
- [x] Build the new global `Sidebar` and `TopBar`.
- [x] Implement global page layout components.
- [x] Add basic Next.js routing for the new folder structure.

## Phase 6: Dashboard
- [x] Build the Daily Intelligence Brief UI.
- [x] Connect dashboard to backend events/alerts.
- [x] Add ingestion health summary.
- [x] Add portfolio concentration warnings.

## Phase 7: Portfolio Page
- [x] Build Holdings table and Portfolio summary cards.
- [x] Connect to existing portfolio backend routes.

## Phase 8: Company Intelligence Page
- [x] Build the individual `companies/[ticker]` view.
- [x] Add Ticker Header, Metric Cards, and SEC filings timeline.
- [x] Add Market Data header and Financial Trends.

## Phase 9: Narrative Page
- [x] Create backend models and endpoints for Narratives.
- [x] Build Narrative tracking UI and evidence timelines.

## Phase 10: Scoring Breakdown
- [x] Create backend models and endpoints for expanded Score types.
- [x] Build the `ScoreBreakdown` UI component to explain score formulas.
- [x] Integrate visual weighted bar chart into Events page.

## Phase 11: Valuation Tool
- [x] Create backend models and endpoints for Valuation Cases.
- [x] Build the frontend DCF UI (Assumptions, Scenarios, Sensitivity tables).

## Phase 12: Research Workspace
- [x] Create backend models for Research Sessions and Messages.
- [x] Build the source-backed AI workspace UI.

## Phase 13: Data Health Page
- [x] Build the Data Health page UI showing API connections and ingestion statuses.
- [x] Show recent processing runs with success/failure counts.
- [x] Show ingestion freshness per source type.

## Phase 14: Polish & Finalize
- [x] Add Error, Empty, Stale, and Loading states globally.
- [x] Perform final security checks (prevent secret leakage).
- [x] Clean up any remaining known issues.
- **Validation:** Run automated security checks (SSRF prevention, CSV escaping, no secrets logged). Ensure all known issues in `docs/known-issues.md` have been addressed.
- **Checkpoint Command:** `git add . && git commit -m "chore: final polish and security hardening"`

---

## Testing Checklist (Pre-Commit)
Before any commit, ensure:
1. `docker compose logs backend` shows no Python stack traces.
2. Migrations are up to date (`alembic upgrade head`).
3. No environment variables or API keys have been hardcoded.
4. The frontend compiles without fatal Next.js errors.
