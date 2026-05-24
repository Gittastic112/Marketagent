# Database Schema

## Purpose

The database is the memory of the Market Intelligence Engine.

Without a database, the project becomes a one-off summarizer.

The database should preserve:

- sources
- companies
- documents
- events
- alerts
- thesis notes
- scoring history
- human review

---

## Core tables

### Company

Stores tracked companies.

Fields:

```text
id
ticker
name
sector
industry
exchange
cik
active
created_at
updated_at
```

---

### Source

Stores source providers.

Fields:

```text
id
name
source_type
base_url
reliability_score
created_at
updated_at
```

Examples:

- SEC EDGAR
- RSS feed
- FRED
- Alpha Vantage
- manual note

---

### RawDocument

Stores raw source material.

Fields:

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

Document types:

- filing
- news
- transcript
- macro_release
- manual_note
- report

---

### Event

Stores normalized events extracted from documents.

Fields:

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
created_at
```

---

### Alert

Stores generated alerts.

Fields:

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
created_at
```

Review statuses:

- unreviewed
- useful
- not_useful
- false_positive
- needs_follow_up

---

### ThesisNote

Stores user's investment/research thesis notes.

Fields:

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

Statuses:

- active
- revised
- rejected
- archived

---

### ThesisChange

Stores changes to thesis assumptions.

Fields:

```text
id
company_id
thesis_note_id
event_id
change_type
explanation
confidence_score
created_at
```

Change types:

- supports_thesis
- weakens_thesis
- contradicts_thesis
- requires_review
- irrelevant

---

### ProcessingRun

Stores processing/audit logs.

Fields:

```text
id
run_type
started_at
finished_at
status
input_count
output_count
error_message
metadata_json
```

---

## Minimum MVP schema

If building incrementally, start with:

- Company
- Source
- RawDocument
- Event
- Alert
- ThesisNote

Add the rest later.
