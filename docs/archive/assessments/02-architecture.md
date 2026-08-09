# Architecture

## 2026-08-02 Exact PDF Evidence Additions

- `pdf_page_rendering.py` converts one stored PDF page to PNG through the pinned
  `pypdfium2`/Pillow stack. It limits scale to `0.5`-`2.0` and output to 16
  million pixels before rendering.
- `GET /api/raw-documents/{id}/asset/pages/{page}.png` is authenticated and
  returns `private, no-store`, inline, `nosniff` image bytes. Invalid stored page
  numbers and unsafe render requests fail explicitly.
- `financialEvidenceGeometry` accepts only finite, in-bounds
  `pdfplumber_top_left_points` geometry. It supports a single reported row or
  multiple component rows and rejects unknown coordinate systems.
- `/documents/{id}/financial-evidence?candidate_id={candidate}` renders the
  source page and proportional overlays. Unsupported geometry retains the
  original authenticated PDF/page link; the UI never guesses a region.

## 2026-08-02 Financial Trust and Industry-Mix Additions

- `data/certification/aapl-apsez-reference-manifest.json` resolves companies and
  source documents by stable market identity plus source hashes instead of local
  database IDs. The certification command still fails unless exactly one match
  exists and both `US` and `IN` histories pass.
- Data Health audits promoted financial candidates for exact locators, unique
  stored fiscal periods, valid stored PDF pages, and matching source/stored
  period-end dates. It derives certified-history and market coverage from
  promoted records only; reviewed-but-unpromoted facts cannot earn the health
  badge. It does not persist or fabricate a certification badge.
- `FinancialStatementIdentityService` evaluates annual promoted source facts
  before certification and valuation use. It currently checks
  `net_income = pre_tax_income - tax_expense` and
  `net_income = net_income_parent + net_income_nci` under a declared absolute
  and relative tolerance. Missing facts produce `not_available`; duplicate
  required metrics and arithmetic mismatches fail closed.
- Certification blocks only failed applicable identities. Partial or unavailable
  coverage remains an explicit limitation. Valuation autofill marks actual
  provenance for review and sets identity trust to `blocked` after a failure.
- Company industry mixes are durable user assumptions with segment labels,
  revenue weights, an optional source document, and an as-of date. Serialization
  reports module and blended-field coverage. Missing component data never causes
  the remaining industries to be silently renormalized.
- Valuation draft source metadata includes deterministic industry-mix and
  financial-history signatures. Reopening a draft refreshes changed source
  values while preserving user-edited values and review state.

## 2026-08-01 Trust and Retrieval Additions

- `EventEvidenceReference` is the precise source locator boundary for events and
  downstream alert evidence. Validation occurs against stored text or PDF page
  count before persistence.
- `AiOutput` now stores validated citations, deterministic evaluation results,
  review notes, reviewer, and disposition. Approval fails closed when execution,
  citation, or recommendation-language checks fail.
- `SourceFactRevision` starts bitemporal-style history for reviewed financial
  promotions with economic effective time and application observation time.
- `/dashboard/overview` is the bounded server-render contract for the Today
  page and enforces owned alert, thesis, and portfolio reads.
- PostgreSQL GIN expression indexes support first-pass corpus search across raw
  documents, events, owned alerts, thesis notes, decisions, and valuation
  models. Search returns stored records, not generated answers.
- `/intelligence/review` combines manually classified event contradictions and
  deterministic filing-section diffs while preserving different claim types.

These are foundations, not a completed evidence graph. Broad real-source
coverage, historical backfill, section/research-message/AI-output search,
large-corpus relevance evaluation, and thesis disposition remain separate gates.

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
6. Browser reads/writes use the same-origin `/api/backend` proxy. Multipart helpers must not set `Content-Type`; the browser supplies the boundary.
7. Server-rendered pages and server actions use `lib/server-api`. Next.js validates the NextAuth JWT locally and sends FastAPI a 60-second HMAC-signed identity assertion; raw session cookies are not forwarded to the backend.
8. The browser `/api/backend` route strips caller-supplied internal-auth headers, validates the JWT, regenerates the signed assertion, and applies a 15-second backend timeout.
9. Authenticated Playwright workflows run against `docker-compose.e2e.yml`: a fresh tmpfs PostgreSQL database, migrated FastAPI service, and production-mode Next.js service on separate ports. The runner reads credentials from the root `.env`, never prints their values, and removes the isolated stack and volumes on exit.
10. Tailwind 4 utilities compile through `@tailwindcss/postcss`; `app/globals.css`
    owns the design-token contract and compatibility aliases. Do not add a
    second styling pipeline or remote font dependency.
11. Primary navigation is grouped and responsive; company routes share a
    nested workspace layout. Dense sidebar and company-tab links use
    `prefetch={false}` because production prefetch otherwise executes many
    dynamic route trees and backend queries before user intent.
12. Normal Docker development bind-mounts source at `/app` but masks
    `/app/node_modules` and `/app/.next` with container-only volumes. Startup
    runs `npm ci` inside Linux so Mac native Lightning CSS, SWC, or Sharp
    packages cannot enter the container runtime.

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
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "last_updated": null,
    "source": "SEC",
    "is_stale": true,
    "warnings": []
  },
  "errors": [
    {
      "code": "SEC_USER_AGENT_MISSING",
      "message": "SEC ingestion requires a valid SEC User-Agent.",
      "retryable": false,
      "provider": "SEC"
    }
  ]
}
```

`app/api/errors.py` owns HTTP, request-validation, response-validation,
rate-limit, and unhandled-error serialization. Server failures are sanitized.
The legacy top-level `detail` field is a temporary compatibility bridge and
must not be used by new clients. `app/core/request_context.py` validates or
generates `X-Request-ID`; `app/core/logging.py` writes request-aware JSON to
stdout. Logs must use explicit safe fields and must not include prompts,
provider bodies, raw documents, private holdings, or credentials.

`app/api/response_contracts.py` is the executable route-response inventory.
Every operation must classify as `api_envelope`, `binary`, `no_content`, or
temporary `legacy_json`. The contract test fails when any legacy JSON route is
present. PDF/CSV/memo downloads are intentionally binary and deletes may remain
no-content; those exceptions must not be wrapped in JSON.

### 3.1.1 Database connection boundary

SQLAlchemy uses `pool_pre_ping` plus an explicit local capacity contract:

```text
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT_SECONDS=10
```

This allows bounded Next.js server-render bursts without silently opening an
unlimited pool. The defaults permit at most 30 checked-out application
connections per backend process. Change them only with a measured render/query
profile and PostgreSQL connection budget.

The consolidated `GET /dashboard/overview` contract has a representative local
budget of at most 20 SQL statements and 1,000 ms of backend generation time.
Explicit `noload`/`selectinload` plans bound relationship loading, response
metadata reports generation time, and the backend emits a warning when the
latency budget is exceeded. This is a dashboard budget, not a system-wide
performance certification.

`GET /search/evidence` has a representative local budget of at most 14 SQL
statements and 750 ms of backend processing. It uses explicit relationship
loading, per-domain candidate limits, a final global result limit, PostgreSQL
full-text indexes, and owner filters for alerts, theses, decisions, and
valuations. Source documents/events rank ahead of mutable user records by a
documented deterministic base weight; PostgreSQL `ts_rank_cd` resolves
relevance within each class. This ranking still needs representative
large-corpus evaluation before it can be called calibrated.

### 3.2 AI Execution Boundary

All AI-capable services use `app/services/ai_contract.py`. The boundary selects
Gemini only when configured, permits `MockAIProvider` only in tests or explicit
`AI_DEMO_MODE`, records success and failure attempts in `ai_outputs`, and never
falls back from a provider failure to mock text. Every active UI call carries a
versioned privacy acknowledgement after displaying the transmitted data
classes.

AI output records are user-owned and include provider/model identity, SHA-256
input hash, source IDs/scope, explicit mock state, privacy version, external
data classes, transmission scope, limitations, confidence, review metadata,
and safe execution/failure state. AI output is untrusted display text.
Narrative extraction is no longer part of automatic ingestion because that
would send data without a separate disclosure. Event-to-thesis classification
returns proposals; reviewed writes use the existing thesis-impact workflow.

---

## 4. Ingestion & Data Freshness Strategy
Trust is paramount. The system must explicitly expose what data is broken, stale, or missing.

- **Processing Runs:** Every ingestion job must create a `processing_run` record tracking `started_at`, `finished_at`, status, fetched/created/skipped/error counts, safe error details, source/company links, and the active `request_id`. Lifecycle logs include both IDs so an HTTP failure can be correlated to durable run status. SEC/RSS, filing/PDF/XBRL extraction, Screener uploads, and normalized backfill follow this pattern.
- **Source Resolution:** SEC ingestion resolves an active `sec` or legacy `filing` source and creates the local `SEC EDGAR` source record when none exists. Browser forms may pass a preferred source id, but must not make users provision one just to enable SEC ingestion. RSS forms remain restricted to active RSS sources.
- **Document Payload Boundary:** Collection and picker views use `RawDocumentSummaryRead` through `/raw-documents/summaries` or `/raw-documents/{id}/summary`. Full `raw_text` is fetched only by a detail workflow that needs it. Metadata-only updates must never overwrite stored source text.
- **Data Freshness:** The backend must return a `last_updated` and `is_stale` boolean in the `meta` envelope. The frontend will use this to display stale banners.
- **Sources:** Initially SEC EDGAR, RSS/News, and manual prices.

---

## 5. Scoring Architecture
All scoring must be explainable. The score is not useful unless users can inspect why it exists.

**Required Scores:** Fundamental, Valuation, Narrative, Sentiment, Risk, Momentum, Confidence, Overall Signal.

**API Transparency Requirement:**
Score endpoints must return the inputs, weightings, direction, and text explanation. Do not hide the formula.

---

## 6. Narrative Tracking Architecture (Partially Implemented)
The system will group events and sentiment into cohesive "Narratives" (e.g., "AI Capex Cycle", "Margin Compression").

- Narratives track source velocity over time.
- They link to multiple companies.
- They include confidence scores and price reaction correlations.

---

## 7. Valuation & Research Layers
- **Valuation Agent:** A Damodaran-style DCF builder with assumptions, scenarios (Bear/Base/Bull), sensitivity tables, reverse DCF, real options, macro sensitivity, WACC, and relative pricing. The mature valuation plan lives in `docs/valuation-agent/master-build-plan.md`; newer automation gaps live in `docs/roadmaps/valuation-auto-pipeline-master-plan.md`.
- **Synthetic-rating WACC:** `synthetic_rating_catalog.py` is an immutable,
  hash-versioned transcription of all 45 approved `ratings.xls` rows. The WACC
  router accepts large non-financial, small/risky, or financial-service firm
  types, keeps the legacy two-state boolean compatible, and returns the exact
  source band plus provenance. Unknown source date and user-assumed recency are
  explicit. Operating-lease conversion remains outside this lookup service.
- **Quick Valuation boundary:** baseline generation and FCFF calculation use typed authenticated endpoints but instantiate only transient calculation objects. Inputs are strictly validated, results are labeled `Calculation` and `is_persisted=false`, and the UI does not fabricate fallback assumptions after an API failure. Durable scenario, sensitivity, reverse-DCF, and review state remain in the full valuation workflow.
- **Financial extraction and autofill:** Filing-text, PDF-table, SEC XBRL, and Screener candidates share a structured evidence-locator contract. Text uses line/page/section, PDF uses page/table/row/column plus table/cell point bounding boxes, Screener uses sheet/row/column/cell, and XBRL uses concept/unit/period/accession metadata. `DocumentAsset` stores one original binary per `RawDocument`; metadata responses stay small and an authenticated route streams the source PDF. Candidate review deep-links to the owning document or PDF page. Normalized snapshots expose coverage, backfill, source-versus-normalized reconciliation, and annual statement identities; broader share-count and equity-bridge metrics feed source-labeled autofill drafts. The portable AAPL/APSEZ corpus proves one structured US and one targeted India profile. Synthetic `Mock Data` histories remain test-only. PDF OCR, arbitrary complex layouts, broad statement totals/subtotals, and broader accounting-policy coverage remain unimplemented.

### PDF filing data flow

```text
Authenticated multipart upload
  -> extension/MIME/magic/size/page validation
  -> RawDocument metadata + extracted page text
  -> one-to-one DocumentAsset original bytes
  -> deterministic pdfplumber tables/cell coordinates
  -> review-gated FinancialExtractionCandidate rows
  -> user review/override
  -> normalized financials
  -> source-fact statement identity checks
  -> valuation draft
```

Binary content must not be serialized through `RawDocumentRead` or
`DocumentAssetRead`. The source stream is authenticated, inline-only,
`Cache-Control: private, no-store`, and `X-Content-Type-Options: nosniff`.

Alert and event evidence reads use a separate bounded projection:

```text
Owned Alert or Authenticated Event
  -> linked Event
  -> safe RawDocument metadata
  -> Source + Company metadata
  -> current-user Thesis impacts
  -> current-user Valuation impacts
  -> claim type + confidence + timestamp + completeness
  -> document/source/PDF links
```

`GET /alerts/{alert_id}/evidence-trail` enforces alert ownership.
`GET /events/{event_id}/evidence-trail` requires authentication and excludes
alerts belonging to any user. Both endpoints omit `raw_text`,
`raw_payload_json`, and binary content. When an `EventEvidenceReference` exists,
the projection includes its validated span/page/section metadata and bounded
quote; legacy events remain explicitly partial or document-level.

For `pdf_region`, exactness is stricter than a page reference. New writes must
store `page`, `coordinate_system=pdfplumber_top_left_points`, page width/height,
and an in-bounds `bounding_box`. The backend compares declared dimensions with
the immutable stored PDF before accepting the reference. Evidence trails use
`region` precision and the rendered overlay route only when that check passes;
legacy or corrupt geometry is downgraded to page precision and a source-context
fallback. The frontend independently rejects unknown, non-finite, mismatched,
or out-of-bounds geometry before drawing an overlay.

Historical text-span backfill is a separate, bounded workflow:

```text
Events without references (priority ordered, max 200)
  -> stored RawDocument text
  -> Event.description + current-user Alert.evidence candidates
  -> exact case-sensitive occurrence count
  -> preview: eligible / ambiguous / conflicting / missing / unmatched
  -> dry-run by default
  -> event row lock + duplicate recheck
  -> exact EventEvidenceReference + ProcessingRun provenance
```

Manual exact-span resolution handles the rows that deterministic backfill leaves
unapplied:

```text
Data Health unmatched / ambiguous / conflicting row
  -> event-linked RawDocument only
  -> exact case-sensitive query (8-300 characters)
  -> max 25 matches + max 300 characters of context per side
  -> user selects one occurrence
  -> event row lock
  -> document/company/hash/offset/quote/occurrence/duplicate revalidation
  -> EventEvidenceReference(origin=manual_exact_resolution, creator=current user)
```

Neither search nor save accepts a URL or returns `RawDocument.raw_text`. Search
is read-only. Save fails closed when the source hash or selected occurrence has
changed since search.

The workflow never uses fuzzy matching, does not normalize whitespace, does not
inspect another user's alerts, and does not infer PDF geometry. GET is a
read-only preview. Every POST records a processing run, including dry runs.

`GET /data-health/evidence-integrity` runs a bounded read-only corpus audit. It
checks source timestamps, document/asset relationships, recorded byte sizes and
SHA-256 hashes, event/document company consistency, text-span coordinates and
quotes, reproducible PDF page dimensions/region bounds, and low-confidence
references. At most 200
issues are returned with truncation metadata. It does not fetch external URLs,
repair records, run on a schedule, or prove every user-owned domain boundary.
- **Research Workspace:** Sessions and messages are user-owned. AI chat uses the unified execution/privacy contract and persists a source scope limited to the owned session. Stored AI outputs can be citation-validated, deterministically evaluated, and reviewed, but provider-generated citations and the evaluation corpus are not yet comprehensive.

### Authentication Boundary

Next.js page protection and signed backend identity assertions are implemented.
The aggregate FastAPI router now requires the verified current-user dependency;
only `GET /api/health` and `GET /health` are public application routes. An
automated inventory traverses FastAPI dependencies and fails when an
authenticated route loses that boundary. Direct unsigned port-8000 reads and
mutations return `401`.

User-owned child records resolve through an owned parent or an authenticated
owner filter. The negative matrix covers portfolio trees, alerts/evidence,
thesis children, valuation models/drafts/children/AI, decisions, research,
daily briefs, transfers, and raw-document AI output. This is a local boundary
and is not a public-deployment authentication architecture.

---

## 8. Current Implementation Status
The backend supports event extraction, SEC/RSS ingestion paths, deterministic rule-based event scoring, alert review, daily briefs, portfolio/holdings CRUD, market-aware company identity, provider health/status reporting, and a broad valuation layer. The API response envelope and processing-run patterns are widely used to stabilize data trust.

Repository release checks now include deterministic credential-shape scanning,
scanner unit tests, project-skill validation, frontend static integrity checks,
TypeScript, backend/frontend tests, and isolated browser workflows. The scanner
reports only path, line, and finding type so CI output does not echo suspected
secret values.

Portfolio parents and child resources are scoped to the authenticated user.
Thesis assumption/impact and valuation assumption/output/change-log routes
resolve child IDs through their user-owned parent instead of trusting a numeric
child identifier alone.
Valuation aggregates remain unavailable when any active holding lacks a market
price; missing data is not treated as a zero-valued position.

The valuation layer is one of the most mature parts of the app: FCFF DCF, diagnostics, WACC, sensitivity, scenario, reverse DCF, FCFE/DDM, relative valuation, macro sensitivity, real options, Damodaran ingestion, and benchmark priors exist with meaningful backend coverage. Do not treat newer financial extraction, industry mapping, assumption autofill, AI memo, or event-to-thesis impact features as fully trusted until their source provenance, tests, and UI states are verified.

Damodaran typed imports are moving to a preserved-version boundary in
`backend/app/services/damodaran_dataset_versions.py`. A dataset version stores
its source hash and source metadata independently from typed benchmark rows.
Exactly one version per dataset/country is selected by readers through the
active dataset-ID subquery. Same-source imports are row-count-verified no-ops;
changed sources preserve historical rows and supersede the prior active record.
Capex, ROE, Margin, Working Capital, Dividend, FCFE, Volatility, PE, PBV, PS,
EV/EBITDA, and Country Statistics use this boundary.
Exact-header validation occurs before version metadata is created, and an empty
parse rolls the transaction back. The four newer conversions preserve source
firm counts. FCFE stores the workbook's before-debt and after-debt aggregates;
the legacy `fcfe` field mirrors after-debt for compatibility, while component
fields absent from the source stay null. Volatility keeps unproven legacy rows
with a null dataset link, but active readers join only the active hashed version.
Its API exposes source/version metadata and never substitutes generic volatility
numbers for missing or null source values. Pricing rows remain source-separated
inside the shared table: the active PE, PBV, PS, and EV/EBITDA versions each own
their fields and provenance. `RelativeValuationBenchmarkService` assembles those
active sparse rows by source code and carries method-specific provenance into
each calculation; it never treats one source row as evidence for sibling fields.
Country-stat reads also join their active `countrystats` version and return that
version's provenance. Legacy rows remain stored but cannot satisfy active reads.
All current application source-specific typed Damodaran importers now use the
preserved boundary. This does not imply that unsupported mirror files have typed
parsers. The application does not retroactively assign a runtime-mirror hash to
legacy rows whose original imported bytes cannot be proven.
