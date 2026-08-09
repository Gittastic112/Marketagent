# Data Indexes

These files are indexes over immutable evidence. They may be updated; files in
`raw/` may not.

| File | Purpose |
|---|---|
| `source_catalog.csv` | One row per canonical raw source with type, purpose, date confidence, usage, and status. |
| `raw_file_hashes.csv` | SHA-256 and byte-size ledger for every canonical raw file. |
| `processing_ledger.csv` | Intake audit trail, including duplicate decisions and application mirrors. |
| `model_selector.csv` | Model choice by company/problem economics. |

`canonical_path` is the stable join key between the catalog and hash ledger.
`source_path` in the processing ledger records where an intake file was found;
it is not a canonical source location.

Use only rows with an appropriate `status` for the task:

- `active`: available subject to its dated-use notes
- `superseded`: retained for reproducibility, not the default current version
- `historical_only`: method/history only, not a current input
- `review_required`: blocked for current use until the linked issue is resolved
- `case_only`: example evidence, never general doctrine by itself
