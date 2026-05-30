# Current State & Known Issues

This is the source of truth for the current state of the application following the recent UI and Backend architectural pivot towards a unified intelligence cockpit, along with the prioritized backlog of known issues.

## 1. What Currently Works
- **Local Infrastructure:** Docker setup for PostgreSQL, FastAPI backend, Next.js frontend, and pgAdmin spins up successfully.
- **Database Models:** SQLAlchemy models and Alembic migrations exist for all MVP tables and recent intelligence tracking tables (e.g. `thesis_drift_score`, `event_corroborations`, `portfolio_priority_score`).
- **Core Entity Creation:** The backend correctly handles CRUD operations for Companies, Sources, Raw Documents, Events, Alerts, Thesis Notes, Portfolios, and Transactions.
- **Data Pipelines:**
  - RSS ingestion fetches feeds and stores XML items.
  - SEC ingestion fetches filing metadata and text (10-K, 10-Q, 8-K) via SEC EDGAR.
  - Event extraction parses raw documents into rule-based events.
  - Deterministic event scoring assigns `credibility_score`, `novelty_score`, and `impact_score`.
  - Alert generation runs when priority thresholds are met.

## 2. What is Mocked (or Hardcoded)
- **Frontend Views:** Many current frontend pages (`/events`, `/alerts`, `/thesis-notes`) simply render raw database tables rather than the new dashboard-driven layout.
- **Score Explanations:** While the backend calculates scores, the frontend does not yet have the `ScoreBreakdown` UI to explain them cleanly.
- **Data Freshness Indicators:** The frontend assumes all data is fresh because the backend does not yet return the standard `is_stale` wrapper.

## 3. What is Missing
- **API Response Envelope:** The critical `{"data", "meta", "errors"}` wrapper is not yet implemented across the FastAPI routes.
- **Processing Runs Tracking:** The backend does not yet log ingestion health to the `processing_runs` table robustly.
- **SEC User-Agent Validation:** The backend does not explicitly enforce or document the `SEC_USER_AGENT` environment variable requirement.
- **Advanced Intelligence Modules:**
  - Narrative Tracking (Models exist, but UI and logic do not).
  - Research Workspace (AI chat sessions linking to sources).
  - Valuation Tool (DCF builder).
- **New Frontend Architecture:** The new 8-tab layout (Dashboard, Portfolio, Companies, Research, Valuation, Alerts, Data, Settings) is not fully built out.

## 4. Existing Backend Endpoints
Currently, the backend has active routers for:
- `/api/companies`
- `/api/sources`
- `/api/raw-documents`
- `/api/events`
- `/api/alerts`
- `/api/thesis-notes`
- `/api/daily-briefs`
- `/api/portfolios`
- `/api/portfolio-holdings`
- `/api/portfolio-transactions`
- `/api/ingestion/rss`
- `/api/ingestion/sec`
- `/api/processing/extract-events`
*(Note: These will all be refactored to use the new API Response Envelope in Phase 2).*

## 5. Existing Frontend Pages
- `/companies`
- `/sources`
- `/documents`
- `/events`
- `/alerts`
- `/thesis-notes`
- `/daily-brief`
- `/portfolio`
- `/settings`
*(Note: These will be reorganized during the Phase 5-8 UI overhaul).*

## 6. Current Blockers to Progress
- **The API Response Envelope (Phase 2) must be implemented first.** Building any new frontend UI before the backend data structure is standardized will result in duplicate work and broken pages. This is the immediate next step.

## 7. Explicit Non-Goals (Do Not Build)
- Trading recommendations.
- Twitter, Reddit, or social scraping.
- Auth, billing, production cloud deployment, or team accounts.
- Vector databases, LangChain, Kafka, Kubernetes, or other heavy infrastructure.
- Broker integrations or broker credential storage.

---

## 8. Prioritized Backlog of Known Issues

### Priority 1: Missing Stale Data and Mock Data States
- **Issue:** The frontend currently lacks robust states for handling missing, partial, or stale data. There is a risk of "Mock Data" being presented as real if an API fails silently.
- **Fix:** The backend must be updated to return standard API response envelopes containing `is_stale` flags. The frontend must globally handle this state to clearly indicate when intelligence is outdated or mocked.
- **Risk:** High. If the user trusts stale data, the core product promise fails.

### Priority 2: Missing API Error Handling Gaps
- **Issue:** Frontend fetching utility does not gracefully handle `500 Internal Server Errors` from missing database columns (as seen recently with `portfolio_priority_score`) without causing a cascading white screen.
- **Fix:** Refactor `fetchApi` to parse the new `errors` array in the standard envelope and render explicit `<ErrorState />` components.

### Priority 3: Missing Score Explainability
- **Issue:** The backend calculates event-level scores, but does not provide API endpoints that explain the math (inputs, weighting, direction) for the new Company/Narrative level scores.
- **Fix:** Implement Score breakdown API endpoints that expose the exact factors.

### Priority 4: Missing Source Evidence Trails
- **Issue:** While raw documents are stored, the UI does not seamlessly expose the "Evidence" trail in a way that allows a user to trace an Alert directly to the highlighted text in an SEC filing.
- **Fix:** The Intelligence UI components must strictly adhere to the 4-layer hierarchy, requiring an Evidence layer.

### Priority 5: SEC Ingestion Not Fully Configured
- **Issue:** The backend needs a dedicated, enforced `SEC_USER_AGENT` environment variable to prevent IP blocking by the SEC.
- **Fix:** Add this variable and document it in the local setup guide. SEC ingestion will fail gracefully if it is missing.

### Priority 6: Alembic Missing Revision Risk
- **Issue:** Users have previously encountered: `Can't locate revision identified by 'a2afaa43a162'`. This breaks local database setup.
- **Fix:** Do not tell users to run destructive commands. Explain how to inspect migration history and either stamp head or restore the missing file safely. (This issue was mostly mitigated in recent commits, but remains a risk as the schema expands for Phase 2).

### Priority 7: Docker Socket Permission
- **Issue:** Users may see `permission denied while trying to connect to the docker API at unix:///var/run/docker.sock`.
- **Fix:** Explain that Docker Desktop must be running. On macOS, restarting Docker Desktop usually helps. Do not recommend `sudo chmod 666 /var/run/docker.sock`.

### Priority 8: Frontend/Backend Connectivity
- **Issue:** The frontend may show "backend not reachable" even when containers are running.
- **Fix Checklist:**
  - Are both containers running?
  - Is `NEXT_PUBLIC_API_BASE_URL` properly passed into the frontend container?
  - Is CORS configured on the backend?

---

## Later, Not Now
- AI summaries or extraction
- Narrative clustering
- Extra data sources beyond SEC/RSS
- Auth, billing, production deployment, or team accounts
- Trading recommendations
- Social scraping
- Live market data, macro APIs, options flow, broker sync, or real-time alerts
