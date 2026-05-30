# Data Sources & Ingestion Flow

## Principle
Start with clean, legal, source-backed inputs. The first version should prioritize public, stable, structured sources.

This file explains what data sources exist, how ingestion flows operate (manual vs. automatic), and what data is preserved.

---

## 1. Current Ingestion Flow

```text
manual setup or ingestion trigger
-> RawDocument
-> Event
-> score Event
-> generate Alert if priority is high enough
-> DailyBrief reads scored Events and Alerts
```

No AI is currently involved. 

### 1.1 Automatic Steps
- **RSS Ingestion:** Stores each feed item as a `RawDocument`. Links a company only when deterministic matching finds exactly one active company by ticker, company name, or alias.
- **SEC Ingestion:** Stores each filing metadata item as a `RawDocument`.
- **Post-Ingestion Pipeline:**
  - Extracts events from raw documents that do not already have events.
  - Scores those events deterministically.
  - Generates alerts for events whose priority passes the alert threshold.
- **Processing Runs:** Each SEC/RSS ingestion attempt creates a `ProcessingRun` record with counts, status, timestamps, errors, and source/company links where available.
- **Daily Brief:** Automatically pulls the highest-priority scored events and latest alerts when requested.

### 1.2 Manual Inputs
- Companies, Sources, Raw Documents, Events, Alerts, and Thesis Notes can all be added manually via `POST` routes or their respective UI pages.
- RSS sources use the existing Source record with `source_type="rss"`, a feed URL in `base_url`, manual `reliability_score`, and `active` status.
- Alert review status and notes are manual human feedback.
- Daily briefs are generated live and saved manually.

---

## 2. Source-Specific Strategies (Design Brief Alignment)

### 2.1 SEC EDGAR Strategy
SEC ingestion exists in `backend/app/services/sec_ingestion.py`.
- **SEC User-Agent:** SEC APIs require respectful access. The system must enforce a valid `SEC_USER_AGENT` environment variable (e.g., `MarketIntelligenceApp/0.1 contact: email@example.com`) before any SEC API calls are made.
- **CIK Lookup:** The backend needs a dedicated, robust CIK lookup endpoint (`/api/sec/company/{ticker}/cik`) for the frontend to display lookup status.
- **Filing Diffs:** When filing text is present, event extraction compares the current filing with the prior stored filing for the same company and form type. If the text changed, it creates a `filing_text_change` event with prior/current RawDocument IDs, source URLs, and a first-pass line diff.

### 2.2 RSS / News Strategy
RSS ingestion exists in `backend/app/services/rss_ingestion.py`.
- News will expand beyond manual RSS to structured News APIs.
- The pipeline will require `NEWS_API_KEY` configurations.

### 2.3 Price Data Strategy
- Currently manual.
- Future state: integration with stable end-of-day providers (e.g., Alpha Vantage, Yahoo Finance). Requires `ALPHA_VANTAGE_API_KEY` configuration.

### 2.4 Social / Forum Strategy
- The system will NOT scrape Reddit or X/Twitter HTML.
- Will only use official/approved APIs. Social posts must maintain exact source URLs and hashes.

---

## 3. Data Freshness & Trust Rules
Trust is the app's primary feature. If the data is broken, the user must know.

### 3.1 Data Freshness Definitions
- **Healthy:** Data fetched successfully within expected timeframes.
- **Stale:** A scheduled run failed or data is older than the configured threshold (e.g., 24 hours).
- **Not Configured:** The user has not provided required API keys or User-Agents.
- **Partial:** Some sources for a company succeeded, others failed.

### 3.2 Stale Data Rules
If data is stale, the frontend must clearly display a warning (e.g., `"Sentiment score may be stale. Last successful ingestion: May 28, 2026."`). The backend must support this by returning `last_updated` and `is_stale` in the `meta` envelope of the API response.

### 3.3 Mock Data Labeling
During development, if the frontend displays fake intelligence (because the backend endpoint isn't built yet), it **must be clearly labeled as Mock Data**. The frontend must never invent intelligence the backend doesn't provide.

---

## 4. Data Provenance Requirements
Every source record must store:
- provider
- source type
- source URL
- published timestamp
- ingestion timestamp
- raw text or raw payload
- content hash
- linked company if applicable

---

## 5. Security Notes
- Treat imported CSV, markdown, RSS, social posts, and AI output as untrusted inputs.
- Do not store broker passwords.
- Do not sync brokers until OAuth is fully implemented.
