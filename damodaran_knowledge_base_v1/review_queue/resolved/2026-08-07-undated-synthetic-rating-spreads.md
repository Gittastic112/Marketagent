# Undated Synthetic-Rating Spreads

Status: `resolved_by_user_approval`

Resolved: `2026-08-07`

## Finding

`raw/models/ratings.xls` contains reusable interest-coverage-to-rating logic and
a default-spread table, but no reliable embedded as-of date for the spreads.
File modification time is not accepted as source provenance.

## User decision

The user explicitly approved treating the table as recent for the current
personal, local workflow. This does not create a source date. Any value derived
from the table must retain:

- `source_as_of: unknown`
- `date_confidence: low`
- `claim_type: User Assumption` for the recency decision
- the approval date `2026-08-07`

If a dated replacement is later added, preserve this workbook and approval for
reproducibility instead of silently overwriting them.
