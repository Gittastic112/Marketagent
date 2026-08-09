# Damodaran Knowledge Base Index

## Start

1. Read `AGENTS.md` for non-negotiable source handling.
2. Run `python3 tools/audit_kb.py` from this directory, or use the repository-root command in `PROCESSING_PLAN.md`.
3. Read `PROCESSING_PLAN.md` for current corpus status and next work.
4. Check `review_queue/README.md` before using blocked sources.

## Canonical knowledge

- Core valuation doctrine: `core/`
- Machine-readable rules and anti-patterns: `knowledge/`
- Market-event/pricing logic: `market/`
- Model selection: `data/model_selector.csv`
- Formula index: `reference/formula_map.csv`

## Source retrieval

- Source and status catalog: `data/source_catalog.csv`
- Intake audit trail: `data/processing_ledger.csv`
- Raw integrity ledger: `data/raw_file_hashes.csv`
- Data-index definitions: `data/README.md`
- Immutable originals and inbox: `raw/`

## Model references

- Primary FCFF architecture: `reference/fcffginzu_architecture.md`
- January 2025 empirical priors: `reference/regression_priors_2025.md`
- Synthetic ratings: `reference/ratings_model_architecture.md`
- Macro sensitivity/duration: `reference/macrodur_architecture.md`

## Other

- User/operator guide: `README_USER.md`
- Reusable prompt: `PROMPT_FOR_CODEX.md`
- Worked cases: `cases/`
- Manual review: `review_queue/`
