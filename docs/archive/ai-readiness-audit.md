# AI Readiness Audit

Date: May 25, 2026

This is an audit only. No AI features are built yet.

## Readiness score

82/100

The source-backed foundation and deterministic score explanations are in place.
AI output provenance should still be added before calling an external model.

## Ready

- Raw documents preserve source ID, URL, raw text or raw payload, content hash,
  timestamps, and company links where available.
- Events link back to raw documents.
- Alerts link back to events.
- Deterministic scoring runs before alerts and daily briefs.
- Score explanations are persisted on events and shown in the UI.
- Human alert review status and notes are captured.
- Daily briefs are built from stored scored events and alerts.
- SEC/RSS ingestion errors and counts are persisted in `ProcessingRun`.
- SEC filing text and first-pass filing text changes are source-backed.

## Missing

- AI output has no dedicated table.
- There is no stored model name, prompt version, input hash, or generated
  timestamp for future AI output.
- There is no explicit human review field for AI-generated outputs.
- There is no policy yet for retrying failed AI calls or marking partial output.

## Minimal AI provenance schema proposal

Add an `ai_outputs` table only when AI is actually introduced.

Suggested fields:

```text
id
raw_document_id nullable
event_id nullable
alert_id nullable
output_type
model_name
prompt_version
input_hash
output_text
limitations
confidence_label
review_status
review_notes
created_at
```

Rules:

- Every AI output must link to at least one source object.
- Store the model and prompt version every time.
- Store a hash of the input text used for generation.
- Never overwrite AI output silently. Create a new row for regenerated output.

## Recommended first AI use case

Raw document summary.

Why:

- It is source-backed.
- It can link directly to one RawDocument.
- It is easy for a user to verify against the original text.
- It does not require investment advice, prediction, or autonomous ranking.

Do not make the first AI feature a buy/sell recommendation, autonomous thesis
change, or unsourced market call.

## Next prerequisites

1. Add the `ai_outputs` provenance table proposal only when starting the first
   AI feature.
2. Choose the first AI use case, preferably raw document summary.
3. Add mocked tests before any live model call.
