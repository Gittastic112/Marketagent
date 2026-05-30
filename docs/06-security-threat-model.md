# Security Threat Model

## Overview

This repository is a local-first market intelligence and portfolio tracker for
personal equity research. It runs a Next.js frontend, a FastAPI backend,
PostgreSQL, and local Docker Compose services.

The system stores research documents, SEC/RSS data, events, alerts, thesis
notes, daily briefs, and planned portfolio records. Future phases may add market
prices, financial metrics, DCF models, AI outputs, social posts, CSV imports,
and broker integrations.

The highest-value assets are:

- `.env` secrets and future API keys
- portfolio holdings, transactions, cash balances, and cost basis
- thesis notes and valuation assumptions
- source-backed documents and alerts
- future broker tokens, if broker integrations are ever added
- future AI prompts, model outputs, and source links

This app is currently local-first and single-user. That lowers some internet
threats, but it does not remove security responsibility. External source data,
CSV imports, user-provided URLs, social posts, and future AI inputs must all be
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
- markdown/text uploads
- social posts and forum text
- future AI model outputs
- future broker/provider API responses

Assumptions:

- The app is local-first and not exposed publicly.
- There is no authentication yet, so it must not be deployed to the public
  internet.
- Tests must not call live APIs.
- Secrets are kept out of source control.
- Future broker integrations use official OAuth or token flows, never stored
  passwords.

## Attack Surface, Mitigations, and Attacker Stories

### Web and API surface

Relevant files:

- `frontend/app/api/backend/[...path]/route.ts`
- `frontend/lib/api.ts`
- `backend/app/api/routers/`
- `backend/app/core/config.py`

Security requirements:

- The frontend proxy must remain a narrow backend proxy, not an arbitrary URL
  fetcher.
- Do not allow user-controlled full URLs to decide proxy destinations.
- Preserve backend error messages that help the user, but do not leak secrets.
- If this app is ever deployed beyond localhost, add authentication,
  authorization, CSRF review, CORS policy, rate limits, and HTTPS before
  exposing private portfolio data.

### External ingestion

Relevant areas:

- RSS ingestion
- SEC ingestion
- future market/fundamentals/social data ingestion

Security requirements:

- Treat all fetched content as untrusted text.
- Preserve provenance, source URL, timestamps, raw payload/text, and content
  hash.
- Avoid duplicate records through content hash and URL checks.
- Do not silently discard ingestion errors.
- Do not scrape sources that prohibit scraping.
- Use official APIs, licensed feeds, approved exports, or manual import.
- Add timeouts and clear error handling for future network fetches.

### CSV, markdown, and manual imports

Future import features will handle portfolio holdings, transactions, prices, and
thesis notes.

Security requirements:

- Validate every row.
- Return row-level errors.
- Do not execute formulas or scripts from uploaded spreadsheets.
- Escape spreadsheet-export cells that begin with `=`, `+`, `-`, or `@` to
  reduce CSV formula injection risk.
- Treat markdown and raw text as untrusted display content.

### Secrets and credentials

Relevant files:

- `.env`
- `.env.example`
- `docker-compose.yml`

Security requirements:

- Never commit `.env`.
- Keep `.env.example` placeholder-only.
- Do not log API keys, bearer tokens, broker tokens, or model keys.
- Do not store broker passwords.
- Future broker integrations must use official OAuth/token flows and should
  encrypt stored tokens if persistence is required.

### AI outputs

Future AI features are allowed only after source-backed storage and portfolio
context are stable.

Security requirements:

- Store model name, prompt version, input hash, generated timestamp,
  limitations, confidence label, and source links.
- Do not let AI invent sources.
- Do not auto-rewrite thesis notes or DCF assumptions.
- Do not generate buy/sell recommendations.
- Treat model output as untrusted text for display.

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
- Publicly deploying the app without authentication while it stores portfolio
  holdings, transactions, thesis notes, and valuations.
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
