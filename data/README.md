# Versioned data and evidence

This directory contains inputs and receipts used by the application and its
verification tools. It is separate from the user's PostgreSQL database, uploads,
private environment, backups, and generated reports.

| Location | Purpose |
|---|---|
| [damodaran/](damodaran/) | Runtime workbook mirrors and source metadata for supported benchmark parsers |
| [contracts/](contracts/) | Explicit frontend/backend wire-contract fixtures |
| [certification/](certification/) | Source registers and reviewed-reference material for financial verification |
| [reviews/](reviews/) | Versioned decisions, source/application receipts, and historical reviews |
| [research-scope.json](research-scope.json) | Recorded research scope; not live holdings or authorization to seed data |

## Preserve the distinction

Benchmark priors are not company facts. Historical review receipts are not proof
of current database contents. Fixtures must identify Mock Data; real sources keep
their original provenance. Never create missing facts to make a check pass.

The independent [knowledge base](../damodaran_knowledge_base_v1/INDEX.md) owns
immutable originals, its catalog, and hash ledger. Runtime mirrors are intentional
consuming inputs. Do not deduplicate or move them without checking their readers,
configured paths, version identity, and source hashes.

Source access does not establish redistribution rights. This repository does not
grant a new license over third-party reports or workbooks. Keep private research
and local output outside publication, and review exact paths before staging.

[Data sources](../docs/data-sources.md) owns ingestion and
provenance. [Operations](../docs/operations.md) owns explicit intake commands.
