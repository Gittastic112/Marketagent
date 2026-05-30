# Database Schema

This file summarizes the current schema and the immediate next schema work based on the frontend/backend design brief.

## Purpose
The database is the app's memory. It must preserve source provenance, portfolio data, explainable scores, human review decisions, and strictly track the health of data ingestion.

## Implemented Tables

### Company
```text
id
ticker
name
sector
industry
exchange
cik
aliases_json
country
region
currency
asset_type
security_type
market_cap_category
is_etf
etf_provider
active
created_at
updated_at
```

### Source
```text
id
name
source_type
base_url
reliability_score
active
created_at
updated_at
```

### RawDocument
```text
id
company_id
source_id
document_type
title
url
published_at
ingested_at
raw_text
raw_payload_json
content_hash
created_at
```

### Event
```text
id
company_id
raw_document_id
event_type
information_speed
title
description
event_time
credibility_score
novelty_score
impact_score
priority_score
score_explanation_json
created_at
```

### Alert
```text
id
event_id
company_id
alert_type
severity
title
summary
why_it_matters
what_changed
evidence
confidence_bucket
review_status
review_notes
reviewed_at
created_at
```

### ThesisNote
```text
id
company_id
title
thesis_text
assumptions_json
status
created_at
updated_at
```

### DailyBrief
```text
id
brief_date
title
summary
payload_json
created_at
```

### ProcessingRun
```text
id
run_type
source_type
source_id
company_id
started_at
finished_at
status
fetched_count
created_count
skipped_duplicate_count
error_count
error_details_json
metadata_json
created_at
```

### Portfolio
```text
id
name
base_currency
description
created_at
updated_at
```

### PortfolioHolding
```text
id
portfolio_id
company_id
ticker
quantity
average_cost
currency
as_of_date
created_at
updated_at
```

### PortfolioTransaction
```text
id
portfolio_id
company_id
ticker
transaction_type
quantity
price
fees
currency
transaction_date
notes
created_at
updated_at
```

### PortfolioCashBalance
```text
id
portfolio_id
currency
amount
as_of_date
created_at
updated_at
```

### PortfolioSnapshot
```text
id
portfolio_id
snapshot_date
total_market_value
total_cost_basis
total_cash
payload_json
created_at
```

---

## Planned Tables (Design Brief Alignment)

### Score
*(Required to support explainable scoring framework)*
```text
id
entity_type
entity_id
score_type
value
label
direction
confidence
explanation
inputs_json
created_at
updated_at
```

### Narrative
*(Required to track thematic stories linking companies)*
```text
id
name
description
status
confidence
first_seen_at
last_seen_at
created_at
updated_at
```

### NarrativeSource
```text
id
narrative_id
source_type
source_id
relevance_score
evidence_summary
created_at
```

### NarrativeCompanyLink
```text
id
narrative_id
company_id
ticker
relationship_type
strength
created_at
```

### ResearchSession
*(Required to support source-backed AI workflow)*
```text
id
title
question
status
created_at
updated_at
```

### ResearchMessage
```text
id
session_id
role
content
citations_json
confidence
created_at
```

### ValuationCase
*(Required to support DCF builder)*
```text
id
ticker
company_id
case_name
scenario
assumptions_json
outputs_json
notes
created_at
updated_at
```

---

## Security Notes
- Portfolio data is private financial data.
- Do not store broker passwords.
- Do not add broker sync until OAuth/token handling is designed.
- Treat imported CSV, markdown, RSS, social posts, and AI output as untrusted.
- See `docs/security-threat-model.md` before adding imports, external APIs, AI, broker integrations, or deployment.
