# Architecture

## 1. System Overview
The Market Intelligence Engine is a source-backed event system and portfolio tracker. It is not designed to be an open-ended chatbot.

**Correct Architecture Flow:**
```text
Raw source
↓
Stored with provenance
↓
Normalized event & Processing Run Tracking
↓
Classified by speed/type
↓
Scored for credibility/novelty/impact (Explainable Scoring)
↓
Linked to company/thesis/narrative
↓
Linked to portfolio exposure when owned
↓
Brief or alert
```

---

## 2. Frontend Architecture

**Technology:** Next.js
**Purpose:** Display dashboards, companies, narratives, DCF valuations, and orchestrate the research workspace.

**Structure Rules:**
1. Pages should orchestrate data and layout.
2. Components should render reusable UI (organized into Layout, Finance, Intelligence, Charts, Data).
3. API functions live under `lib/api`.
4. Do not scatter fetch logic across components.
5. All UI must properly handle API states: Loading, Empty, Error, Stale, Partial, Not Configured.

---

## 3. Backend Architecture

**Technology:** Python FastAPI, PostgreSQL (via Docker), Alembic

**Structure Rules:**
1. **Routes (`app/api/routes`):** Must be thin and only handle HTTP requests/responses.
2. **Services (`app/services`):** All business logic, scoring, and data manipulation lives here.
3. **Database Models (`app/models`):** SQLAlchemy ORM models. Never leak directly to the frontend.
4. **Schemas (`app/schemas`):** Pydantic schemas for strict request validation and response serialization.

### 3.1 API Response Envelope (Standard)
Every backend API response must follow a predictable shape to enable the frontend to display honest data states.

**Success Example:**
```json
{
  "data": {},
  "meta": {
    "status": "success",
    "last_updated": "2026-05-30T10:00:00Z",
    "source": "internal",
    "is_stale": false,
    "warnings": []
  },
  "errors": []
}
```

**Error Example:**
```json
{
  "data": null,
  "meta": {
    "status": "error",
    "last_updated": null,
    "source": "SEC",
    "is_stale": true,
    "warnings": []
  },
  "errors": [
    {
      "code": "SEC_USER_AGENT_MISSING",
      "message": "SEC ingestion requires a valid SEC User-Agent."
    }
  ]
}
```

---

## 4. Ingestion & Data Freshness Strategy
Trust is paramount. The system must explicitly expose what data is broken, stale, or missing.

- **Processing Runs:** Every ingestion job (SEC, News, Prices) must create a `processing_run` record tracking started_at, completed_at, status, records_processed, and error messages.
- **Data Freshness:** The backend must return a `last_updated` and `is_stale` boolean in the `meta` envelope. The frontend will use this to display stale banners.
- **Sources:** Initially SEC EDGAR, RSS/News, and manual prices.

---

## 5. Scoring Architecture
All scoring must be explainable. The score is not useful unless users can inspect why it exists.

**Required Scores:** Fundamental, Valuation, Narrative, Sentiment, Risk, Momentum, Confidence, Overall Signal.

**API Transparency Requirement:**
Score endpoints must return the inputs, weightings, direction, and text explanation. Do not hide the formula.

---

## 6. Narrative Tracking Architecture (Planned)
The system will group events and sentiment into cohesive "Narratives" (e.g., "AI Capex Cycle", "Margin Compression").

- Narratives track source velocity over time.
- They link to multiple companies.
- They include confidence scores and price reaction correlations.

---

## 7. Valuation & Research Layers (Planned)
- **Valuation:** A DCF builder with assumptions, scenarios (Bear/Base/Bull), and sensitivity tables.
- **Research Workspace:** A structured chat interface for source-backed AI interactions, linking back to exact `research_sources`.

---

## 8. Current Implementation Status
The MVP backend currently supports basic event extraction, manual RSS/SEC pasting, deterministic rule-based event scoring, and manual portfolio/holdings CRUD. The next massive shift is implementing the **API Response Envelope** and **Processing Runs** to stabilize data trust before expanding AI features.
