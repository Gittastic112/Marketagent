# Damodaran Knowledge Base Operator Guide

This folder is already installed at the repository root as
`damodaran_knowledge_base_v1/`. Do not create another copy under `knowledge/`.

## Normal use

1. Start with `INDEX.md` and `AGENTS.md`.
2. Use `core/` and `knowledge/` before opening raw files.
3. Select models through `data/model_selector.csv`.
4. Select benchmark sources through `data/source_catalog.csv`; filter by
   geography, as-of date, status, and usage.
5. Use `cases/` only as worked examples.
6. Keep every valuation's exact input value, source path, and as-of date.

## Add a source

1. Put the untouched file in `raw/inbox/`.
2. Run `python3 tools/audit_kb.py`; exit code `2` confirms pending intake rather
   than corruption.
3. Tell Codex: `Process the Damodaran inbox according to AGENTS.md.`
4. Review only the resulting files listed in `review_queue/README.md`.
5. Require a final clean audit before considering the batch processed.

## What the agent may change

The agent may update derived doctrine, references, catalogs, ledgers, manifest,
cases, review items, tools, and tests when directly supported. It must never edit
canonical files under `raw/` or silently overwrite reviewed rules.

## Current state

The legacy `Data for Model/` intake was reconciled on `2026-08-07`. The canonical
raw corpus contains `61` files and the literal inbox is empty. See
`PROCESSING_PLAN.md` for the completed work and prioritized follow-up.

## Commands

From the repository root:

```bash
python3 damodaran_knowledge_base_v1/tools/audit_kb.py
python3 -m unittest discover -s damodaran_knowledge_base_v1/tools -p 'test_*.py'
```

Only use `--refresh-hashes` after intentionally routing new immutable originals:

```bash
python3 damodaran_knowledge_base_v1/tools/audit_kb.py --refresh-hashes
```
