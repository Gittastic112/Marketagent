# Security Threat Model

## Overview

Implemented controls were reviewed September 30, 2026, with October 11 source
hardening recorded in the [M03 checkpoint](archive/checkpoints/2026/m03-security-2026-10-11.md). The dated
[security checkpoint](archive/checkpoints/2026/security-and-comparison-reviews-2026-09-30.md)
records evidence; prioritized residual work lives only in the
[limitation ledger](agent_capabilities_and_limitations.md#security-boundary).
Requirements below are not a claim of complete public-deployment readiness.

This repository is a local-first market intelligence and portfolio tracker for
personal equity research. It runs a Next.js frontend, a FastAPI backend,
PostgreSQL, and local Docker Compose services.

The system stores research documents, SEC/RSS data, events, alerts, thesis
notes, daily briefs, portfolios, holdings, transactions, market prices,
financial metrics, DCF models, AI outputs, social posts, and valuation
assumptions. Future phases may add broader CSV imports, more provider-backed
data feeds, and broker integrations.

The highest-value assets are:

- `.env` secrets and future API keys
- portfolio holdings, transactions, cash balances, and cost basis
- thesis notes and valuation assumptions
- source-backed documents and alerts
- future broker tokens, if broker integrations are ever added
- AI prompts, model outputs, and source links

This app is currently local-first and single-user. That lowers some internet
threats, but it does not remove security responsibility. External source data,
CSV imports, user-provided URLs, social posts, and AI inputs must all be
treated as untrusted.

## Threat Model, Trust Boundaries, and Assumptions

Trust boundaries:

- Browser to Next.js frontend.
- Next.js frontend to FastAPI backend through the `/api/backend` proxy or
  server-side `API_BASE_URL`.
- FastAPI backend to PostgreSQL.
- Backend to external data providers such as SEC, RSS feeds, future market data
  providers, FRED, AI APIs, or broker APIs.
- User-provided files and text into backend import/parsing logic.
- Future AI model calls and returned text back into the app.

Operator-controlled inputs:

- `.env`
- Docker Compose settings
- SEC user agent
- alert thresholds
- future API keys
- manually entered companies, holdings, transactions, prices, and thesis notes

Attacker-controlled or untrusted inputs:

- RSS feed content
- SEC filing text, even though source credibility is high
- URLs entered into source records
- CSV imports
- Excel workbook uploads
- markdown/text uploads
- social posts and forum text
- AI model outputs
- future broker/provider API responses

Assumptions:

- The app is intended for local use. Checked-in Compose publishes on 127.0.0.1;
  older containers can retain all-interface bindings until recreated. Inspect
  actual bindings and host/network controls rather than inferring isolation.
- Local credentials and a NextAuth session protect the current single-user
  workflow, but there is no production-ready authentication or authorization
  design. It must not be deployed to the public internet.
- Tests must not call live APIs.
- Secrets are kept out of source control.
- Future broker integrations use official OAuth or token flows, never stored
  passwords.

## Attack Surface, Mitigations, and Attacker Stories

### Web and API surface

Relevant files:

- `frontend/app/api/backend/[...path]/route.ts`
- `frontend/app/api/auth/readiness/route.ts`
- `frontend/proxy.ts`
- `frontend/lib/auth-options.ts`
- `frontend/lib/internal-auth.ts`
- `frontend/lib/server-api.ts`
- `frontend/lib/api.ts`
- `backend/app/api/routers/`
- `backend/app/core/config.py`

Security requirements:

- The frontend proxy must remain a narrow backend proxy, not an arbitrary URL
  fetcher.
- The Next.js page proxy is an optimistic signed-out redirect only. Next.js
  validates the JWT again at server-rendered and browser-proxy request
  boundaries, then signs a 60-second internal identity assertion with
  `NEXTAUTH_SECRET`. FastAPI verifies the assertion locally before applying
  per-record ownership checks.
- Never forward raw NextAuth cookies to FastAPI. The browser backend proxy must
  allow only content type, accept and request-id headers before generating its
  own signed identity. Reject untrusted Host and cross-origin/missing-Origin
  mutations; never trust forwarded-host headers or follow upstream redirects.
- Frontend and backend bound request bodies at 42 MiB with a 30-second body
  deadline. The backend spools above 1 MiB before parsing. File-specific limits
  remain smaller. Backend per-path/IP throttling covers included routes;
  local credential login allows ten attempts per process/minute. These are not
  distributed per-user abuse controls. Private responses are no-store, validation
  errors omit raw input/context, and browser responses add basic CSP/frame headers.
- `NEXTAUTH_SECRET` is shared by the frontend and backend containers only for
  this local single-user assertion flow. It must remain secret and must not be
  exposed through any `NEXT_PUBLIC_*` variable.
- The aggregate FastAPI router requires the verified current-user dependency.
  The explicit public APIRoute allowlist is `GET /api/health`,
  `GET /api/readiness` and `GET /health`. Framework documentation/OpenAPI
  routes are outside that inventory. Shared company/source catalogs require
  authentication but are not owner-private tables. The
  automated route-security inventory must fail if an authenticated operation
  loses that dependency.
- Backend and server-rendered frontend requests must use finite timeouts so an
  unavailable service cannot leave the UI compiling or rendering indefinitely.
- Portfolio parents and every portfolio child route must verify current-user
  ownership. Ingestion-created alerts must store the authenticated user id and
  deduplicate within that user's records.
- Portfolio valuation derives private DCF, thesis and alert context from its
  persisted owner even for internal callers; an explicit different owner is
  rejected. Event-driven valuation alerts derive their owner from the model,
  require matching company/event/change-log relationships and link only that
  owner's portfolios. Price-ingestion alerts use the requesting owner.
- Alert evidence reads must resolve the alert with the current user id before
  following event/document relationships. Event evidence reads must require
  authentication and filter thesis and valuation impacts through their
  user-owned parent records. Evidence responses must use explicit summary
  schemas and must never serialize `RawDocument.raw_text`,
  `RawDocument.raw_payload_json`, document bytes, or another user's alerts.
- Event PDF-region creation may inspect only the already stored authenticated
  `DocumentAsset`. Reject missing boxes, unknown coordinate systems, non-finite
  or out-of-page bounds, page mismatches, and declared dimensions that do not
  match the stored PDF. Overlay pages must continue using the bounded private
  page renderer and must never accept arbitrary URLs or request-supplied PDFs.
- Historical evidence backfill must read alert-derived claims only from the
  authenticated user's alerts. It may create a span only for one bounded exact
  case-sensitive occurrence in stored source text. Apply must lock the event,
  recheck existing references, preserve creator and processing-run provenance,
  and leave ambiguous, conflicting, fuzzy, or unmatched claims unapplied.
- Manual event-evidence search may inspect only the event's already stored linked
  document. It must return bounded context snippets rather than the full source
  body, enforce query/context/result limits, and preserve exact case and
  whitespace. Save must lock the event and revalidate the linked document,
  company, content hash, offsets, quote, occurrence index, and duplicate state.
  Search parameters and locator provenance are generated or verified server-side;
  creator identity comes only from the authenticated backend identity.
- Unified stored-research search must preserve each model's access boundary.
  Shared documents, events, and narratives may be searched as shared records;
  alerts, theses, decisions, valuations, research sessions/messages, and AI
  outputs must be filtered by the authenticated owner. User messages may return
  only bounded excerpts. Assistant message text must not bypass AI review by
  appearing as a generic message result.
- Search may index AI output only when execution succeeded, human review is
  approved, `is_blocked` is false, and a review timestamp exists. The result
  remains `AI Interpretation`, carries mock state, and does not become a fact
  merely because it is searchable.
- Thesis assumptions/impacts and valuation child records must never be resolved
  by child ID alone. Join or resolve through the current user's `ThesisNote` or
  `ValuationModel`, including updates, deletes, outputs, scenarios, diagnostics,
  change logs, and reverse DCF.
- Keep `/api` routes outside the page redirect so protected API failures remain
  structured JSON responses instead of HTML redirects.
- Auth readiness may expose required environment-variable names and boolean
  configuration state. It must never return secret or credential values, and
  its response must remain non-cacheable.
- Browser automation must use the isolated `market-intel-e2e` Compose project
  or an explicitly scoped disposable equivalent,
  its tmpfs database, and non-default ports. It may read local credentials from
  the ignored root `.env`, but tests, traces, logs, screenshots, and docs must
  not contain credential values. The runner must remove its containers,
  network, and volumes on every exit path.
- Runtime schema mutation endpoints are prohibited. Database tables and indexes
  must be owned by reviewed Alembic migrations; the temporary
  `/companies/setup_db_temp_script` route has been removed.
- Do not allow user-controlled full URLs to decide proxy destinations.
- Preserve backend error messages that help the user, but do not leak secrets.
- If this app is ever deployed beyond localhost, add a reviewed production
  authentication and authorization design, CSRF review, CORS policy, rate
  limits, and HTTPS before exposing private portfolio data. Local credential
  environment variables are not a substitute.

### External ingestion

Relevant areas:

- RSS ingestion
- SEC ingestion
- market/fundamentals/social data ingestion

Security requirements:

- Treat all fetched content as untrusted text.
- Preserve provenance, source URL, timestamps, raw payload/text, and content
  hash.
- Avoid duplicate records through content hash and URL checks.
- Do not silently discard ingestion errors.
- Do not scrape sources that prohibit scraping.
- Use official APIs, licensed feeds, approved exports, or manual import.
- Add timeouts and clear error handling for future network fetches.
- Public RSS and filing-text downloads validate every DNS answer, including
  IPv6, reject non-public addresses, pin the numeric connection while preserving
  TLS verification/Host, and disable redirects/environment proxies. RSS is capped
  at 4 MiB and filing text at 40 MiB; unexpected compression is rejected.
  Other fixed-provider clients have separate policies, not blanket pinning.
- RSS parsing rejects DTD/entities through defusedxml and caps inline XML too.

### CSV, markdown, and manual imports

Import features may handle portfolio holdings, transactions, prices, thesis
notes, filing text, and other source documents.

Security requirements:

- Validate every row.
- Return row-level errors.
- Require authenticated access for every transfer route.
- Resolve every imported or exported portfolio row through the current user's
  portfolio.
- Enforce finite UTF-8 file-size and row-count limits before applying records.
- Reject ambiguous headers/cell counts and malformed parser input; preview must
  reject values outside the stored numeric range/precision instead of rounding them.
- General and evidence-bundle import failures log only exception type, never
  exception bodies that can contain uploaded values or SQL parameters.
- Keep preview read-only and roll back the full apply transaction when any
  blocking row or downstream portfolio update fails.
- Do not execute formulas or scripts from uploaded spreadsheets.
- Manual benchmark workbooks cap intake at 12 MiB; Screener keeps its 2 MiB cap.
  ZIP preflight rejects encrypted, excessive-entry and oversized-expanded files
  before parsing. Legacy XLS still needs its parser; these are not CPU isolation.
- Escape spreadsheet-export cells that begin with `=`, `+`, `-`, or `@` to
  reduce CSV formula injection risk, including whitespace-prefixed formulas and
  leading tab/newline/carriage-return values.
- Treat markdown and raw text as untrusted display content.
- Filing section diffs may render only parser-recognized generator-owned `<ins>` and `<del>` semantics. Escape every source token before storage, parse stored legacy diff strings into React text segments, and keep regression tests for changed and first-time sections. Filing diff rendering must not use `dangerouslySetInnerHTML`.
- Accept Screener uploads as `.xlsx` only, cap them at 2MB, hash bytes before
  persistence, reject duplicate content, and delete temporary files in a
  `finally` path.
- Persist source, raw-document metadata, content hash, and processing-run
  outcome. Do not persist temporary file paths or workbook bytes.
- Current and legacy SEC companyfacts HTTP intake use the bounded issuer-checked
  transport and create review candidates only. Ingestion is not financial approval.
- Accept PDF uploads only through authenticated routes. Require `.pdf`, an
  allowlisted MIME type, `%PDF-` magic bytes, a 40MB size cap, a 1,000-page hard
  cap, a sanitized basename, a SHA-256 digest, company-scoped duplicate
  rejection, controlled parser errors, and a processing-run outcome. Full scans
  stop at 500 pages; longer files require at most 75 explicitly targeted pages.
- Keep original PDF bytes in the one-to-one `document_assets` table, never in
  normal raw-document/asset metadata responses. Stream them only through an
  authenticated route with `private, no-store`, inline disposition, and
  `nosniff` headers.
- Raw-document collection and picker routes must return metadata summaries
  without `raw_text`. Metadata updates must use a metadata-only schema so an
  omitted body cannot erase stored filing evidence.
- Treat extracted PDF text, table labels, filenames, and parser metadata as
  untrusted. Do not render extracted HTML or expose local paths/tracebacks.
- PDF extraction, geometry and rendering run in limited Linux child processes.
  CPU, memory, output, wall-time and concurrent-job caps bound resource consumption;
  children receive no credential environment. This is not a filesystem/native-code
  sandbox, malware scanner or content-disarm control for public deployment.
- Render evidence images only from stored authenticated assets. Restrict scale
  to `0.5`-`2.0`, reject nonexistent pages, cap output at 16 million pixels, and
  return PNG bytes with `private, no-store`, inline disposition, and `nosniff`.
  The renderer must not fetch user-controlled URLs or accept arbitrary bytes.
- Do not return parser stack traces or local file paths to the browser.
- Daily Brief uploads use a separate owner-private `brief_sources` table, never
  the shared raw-document catalog. Text is capped at 60,000 characters; PDFs at
  12 MB, 1,000 total pages and 20 selected pages. Oversized ranges are rejected
  before allocating page lists. Resolve indirect content streams and bound each
  decoded page before text extraction. No OCR or visual/table-layout analysis.
  Original PDF bytes and source text are deferred and excluded from collections;
  only owned detail/binary routes expose them, with private/no-store headers.
- Inbox scans require explicit current disclosure. Only selected source text,
  source date, public company identity and field names leave the machine. Stored
  portfolio/thesis/model values do not. Exact unique quotes, declared source IDs,
  a fixed valuation-field catalog and recommendation checks guard publication.
  Failed or unverifiable output stays blocked; successful output remains pending
  human review. Source matching does not certify interpretation or materiality.
  No scan endpoint promotes facts or changes valuation drafts/saved models.
  Evaluation v3 explicitly limits automated success to citation/policy checks and
  leaves interpretation quality unevaluated. Adversarial Mock Data covers exact
  quotes paired with wrong numbers, mismatched periods, unsupported inferences and
  source-text instructions. Passing these text checks never grants human review;
  this fixture suite does not certify a provider's prompt-injection resistance.
- Archive/restore requires the source owner and viewed lifecycle version. It
  retains private evidence and review state rather than deleting or approving it.
  Archived sources cannot initiate scans. Active attempts block archiving; expired
  attempts can be abandoned. Publication/failure must match the claimed scan
  timestamp and lifecycle version, never overwrite a newer attempt, and never
  resolve a failure by taking another request's latest AI output.

### Dependency supply chain

- Keep direct frontend framework/auth dependencies on reviewed patch releases.
- Use narrow npm overrides only when a transitive advisory has a compatible
  patched release and prove the override with unit tests, typecheck,
  production build, and browser workflows.
- Do not follow an audit suggestion that downgrades the framework to an
  incompatible historical major version.
- Run the current dependency audit against the checked-in lockfile. Do not
  carry an old zero-vulnerability result forward as proof of current safety.

### Secrets and credentials

Relevant files:

- `.env`
- `.env.example`
- `docker-compose.yml`

Security requirements:

- Never commit `.env`.
- Keep `.env.example` placeholder-only.
- Do not log API keys, bearer tokens, broker tokens, or model keys.
- Gemini credentials use the x-goog-api-key header, never URL query parameters.
  The explicit connectivity check sends a fixed non-private prompt, records a
  model-specific Processing Run and suppresses raw provider failure bodies.
- Do not store broker passwords.
- Future broker integrations must use official OAuth/token flows and should
  encrypt stored tokens if persistence is required.
- Legacy generic `/oauth/store-token` writes are disabled with 503 because the
  table lacks a supported owner-scoped provider workflow. Status returns no
  global inventory and explicitly says not configured; existing rows are retained.

### AI outputs

AI features are allowed only when source-backed storage, provenance, and
portfolio/valuation privacy boundaries are explicit.

Security requirements:

- Store authenticated owner, provider, model, prompt version, SHA-256 input
  hash, generated timestamp, explicit mock state, source IDs/scope,
  limitations, confidence, review metadata, privacy-disclosure version,
  external data classes, transmission scope, and safe execution/failure state.
- Permit mock output only in tests or explicit `AI_DEMO_MODE`; missing provider
  configuration and provider failure must remain visible failures.
- Display the exact data classes that may leave the machine and require the
  current disclosure version before every external-capable AI action.
- Require a current owner/provider/action grant in addition to that per-action
  acknowledgement. Settings records append-only grant/refusal/revocation decisions
  with disclosure/scope hashes and optimistic revision checks. Missing, refused,
  revoked or outdated permission sends no provider request; no migration or old
  output creates consent. Scope changes invalidate old grants.
- Recheck permission immediately before each external callback, including each
  item in a batch. Record the precise permitting decision on successful or failed
  dispatched outputs. Revocation stops subsequent sends; it cannot recall sent
  data or cancel an already dispatched request. Permission history is owner-only.
- Research chat discloses selected document titles/excerpts as well as private
  messages, and checks permission before saving the new message. Existing
  provider-failure message recovery remains separate from an absent permission.
- Exempt only the actual local MockAIProvider implementation, never a provider
  merely claiming a mock name. The operator CLI's fixed non-private connectivity
  prompt is a separate diagnostic, not a grant to use application records.
- Manual and scheduled Daily Brief assembly do not invoke external AI. Individual
  evidence/valuation AI actions retain their own permission and review gates.
- Do not let AI invent sources.
- Citation suggestions may inspect only source IDs declared by an owned AI
  output. They must use already stored raw-document text, bound scan and quote
  sizes, preserve exact offsets, expose low-confidence and unavailable states,
  and make no external calls.
- Selecting a suggested passage must not validate a citation, change review
  status, or approve an output. Manual edits must discard previously suggested
  offsets so the validator resolves the edited text again.
- Reviewed-AI search must remain owner-scoped, omit pending/blocked/failed
  output, and return bounded excerpts rather than full private output bodies.
- Do not auto-rewrite thesis notes, thesis impacts, or DCF assumptions. AI may
  return proposals that require a separate reviewed write.
- Do not generate buy/sell recommendations.
- Treat model output as untrusted text for display.
- Do not include prompts, provider bodies, raw documents, private request
  bodies, holdings, thesis text, credentials, or raw exception text in logs.

Implemented boundaries include `backend/app/services/ai_contract.py`,
`backend/app/services/ai_citations.py`, and
`backend/app/services/ai_citation_suggestions.py`. Active entry points use the
execution contract; exact declared-source citation validation, local
deterministic passage candidates, owner-scoped review, and approval blocking
exist. Providers do not yet generate complete citations reliably and the
evaluation corpus remains small, so AI text is not certified source-backed
research.

### Portfolio and financial privacy

Portfolio records reveal private financial behavior.

Security requirements:

- Keep the app local-first until auth and deployment are explicitly designed.
- Do not add analytics, telemetry, or external logging of user portfolio data.
- Do not send portfolio holdings, thesis notes, or DCF assumptions to AI or
  external providers unless the feature explicitly requires it and stores an
  audit trail.

## Severity Calibration

Critical:

- Exposing `.env`, API keys, broker tokens, or future OAuth refresh tokens.
- Publicly deploying the app with only its local credential flow while it
  stores portfolio holdings, transactions, thesis notes, and valuations.
- Adding broker password storage or unsafe broker credential handling.

High:

- SSRF through user-controlled URLs that can make the backend fetch arbitrary
  internal resources.
- CSV import that executes formulas when exported/opened elsewhere.
- XSS from rendering imported RSS/social/markdown/AI text as trusted HTML.
- Sending private portfolio or thesis data to external AI APIs without explicit
  provenance and user-visible design.

Medium:

- Silent ingestion failures that make the user trust incomplete data.
- Weak duplicate detection causing misleading repeated alerts.
- Overly broad proxy routes that accidentally expose unintended backend paths.
- Missing validation on transaction quantities, prices, currencies, or dates.

Low:

- Local-only debug logs that expose non-secret request paths.
- Styling or display bugs that do not affect data integrity.
- Documentation drift that misstates what features are built, unless it causes
  unsafe operation.
