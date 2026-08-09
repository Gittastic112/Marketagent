# AGENTS.md: Damodaran Valuation Knowledge Base

## Purpose
This folder is the canonical valuation and market-analysis knowledge layer for the Market Agent. Preserve provenance, distinguish reusable doctrine from examples/data, and keep intrinsic valuation separate from pricing and market-event interpretation.

## Agent quick start

From the repository root:

```bash
python3 damodaran_knowledge_base_v1/tools/audit_kb.py
sed -n '1,220p' damodaran_knowledge_base_v1/INDEX.md
sed -n '1,260p' damodaran_knowledge_base_v1/PROCESSING_PLAN.md
find damodaran_knowledge_base_v1/raw/inbox -type f ! -name README.md -print
```

Stop on audit exit code `1`. Exit code `2` means intact corpus with pending inbox
files and is the expected start of an intake run.

## Priority order when the agent needs valuation knowledge
1. `knowledge/rules.jsonl`, `knowledge/update_rules.jsonl`, `knowledge/anti_patterns.jsonl`
2. `core/*.md` and `market/*.md`
3. `reference/fcffginzu_architecture.md` and `reference/formula_map.csv`
4. `data/model_selector.csv` and `data/source_catalog.csv`
5. `cases/*` for worked examples only
6. `raw/*` for audit, detailed extraction, and resolving missing context

## Canonical architecture
`raw/models/fcffginzu(1).xlsx` is the primary reference model for a standard non-financial company when operating income is positive or can be normalized positive. It supports 2-stage/3-stage FCFF, up to 15 years of high growth, fundamental growth, R&D capitalization, operating-lease conversion, synthetic ratings, country ERP, multi-business beta, options, NOLs, failure risk and stable-growth consistency.

Use specialized models only when the company/problem requires them. See `data/model_selector.csv`.

## Knowledge types
Classify each extracted item as one of:
- `RAW_FACT`: reported historical data.
- `NORMALIZATION`: accounting adjustment.
- `MODEL_INPUT`: explicit company/case assumption.
- `MODEL_FORMULA`: reusable calculation.
- `CAUSAL_RULE`: evidence-to-assumption logic.
- `VALUATION_HEURISTIC`: reusable valuation principle.
- `UPDATE_RULE`: how new evidence changes beliefs/model.
- `MARKET_MECHANISM`: pricing, expectations, flows, catalysts.
- `ANTI_PATTERN`: behavior the agent should avoid.
- `CASE_APPLICATION`: company-specific worked example.
- `UNCERTAINTY`: distribution/confidence/correlation information.
- `CONFLICT`: inconsistent sources/versions.
- `TEMPLATE_CONTAMINATION`: stale text or cells from another model/case.

## Source handling
- Never edit a file in `raw/`.
- Hash every newly ingested source and check for duplicates.
- Use `data/processing_ledger.csv` to record intake, duplicate and routing decisions.
- Use `canonical_path` to join the source catalog and raw hash ledger.
- Maintain source provenance at atomic record level.
- Preserve source date/as-of date separately from ingestion date.
- Dated market data is data, not doctrine.
- If a source has no reliable as-of date, mark `date_confidence: low`.
- Do not silently replace old data with new data. Add a new version and mark which is latest.

## New-file routing
- Articles/notes/PDFs -> `raw/articles/` unless tied to one case, then `raw/cases/<case>/`.
- General valuation spreadsheets/models -> `raw/models/`.
- Benchmark/industry/country tables -> `raw/datasets/`.
- New unprocessed files begin in `raw/inbox/`.
- Company case models -> `raw/cases/<case>/`.

Filename is a clue, not authority. Inspect content/metadata before final classification.

## Extraction workflow for every new source
1. Inventory filename, type, hash, source/author, source date and probable topic.
2. Extract text, tables, formulas, comments, named ranges and relevant charts/figures.
3. Identify existing concepts touched by the source.
4. Separate general rules from case assumptions and raw data.
5. Compare with canonical rules and prior versions.
6. Add raw/tabular data with date and source.
7. Add/update case files when company-specific.
8. Propose new/changed canonical records only with direct support.
9. Run contradiction and template-contamination checks.
10. Put unresolved items in `review_queue/`.
11. Update `manifest.yaml` and `data/source_catalog.csv`.
12. Refresh the hash ledger only after routing and run `tools/audit_kb.py` plus its tests.

## Inbox completion criteria

Do not report an inbox batch complete unless:

- every intake file has a processing-ledger row
- every unique source has exactly one cataloged canonical raw path
- every duplicate points to a verified identical canonical hash
- source date and date confidence are explicit
- the literal inbox contains no pending files
- unresolved conflicts have review items
- the integrity auditor exits `0`

## Canonical rule update policy
- Additive changes with clear support can be added automatically.
- Do not silently overwrite or delete a reviewed rule.
- A later source may supersede a dated input, but does not automatically supersede doctrine.
- If two Damodaran sources conflict on a model assumption, retain both as versions and flag the conflict.
- If a spreadsheet and accompanying article conflict, record which value actually drives the spreadsheet formula and separately preserve the article value.

## Valuation behavior
- Start with corporate life-cycle stage and business model.
- Separate materially different business segments when growth, margins, capital intensity, risk or competition differ.
- Normalize accounting before calculating economics when relevant.
- Translate story into target revenues, margins and reinvestment/capital efficiency.
- Prefer economic endpoints and convergence paths over blind historical extrapolation.
- Tie growth to reinvestment. Do not allow unfinanced/free growth.
- Use risk in discount rates and company-specific uncertainty in scenarios/distributions where appropriate.
- Enforce stable-growth consistency.
- Keep enterprise value, equity bridge, options/dilution and non-operating assets explicit.
- Keep intrinsic valuation and relative pricing as separate analyses.

## Model selection rules
Read `data/model_selector.csv`. In brief:
- Standard non-financial, EBIT positive/normalizable -> FCFF (`fcffginzu`).
- Young/high-growth with negative or hard-to-normalize EBIT -> `higrowth` framework.
- Financial service firm where debt is operating input and book equity/ROE is central -> excess return or dividend/FCFE framework.
- Mature dividend-paying firm with defensible payout policy -> dividend model.
- Product patent/project right -> project real option.
- Distressed/highly levered equity -> equity-as-option plus distress analysis as relevant.
- Pricing/comps -> PE, EV/Sales, EV/EBITDA datasets; never substitute pricing for intrinsic value.

## Data selection
- Use benchmark files as priors/reality checks, not automatic answers.
- US, Global and India variants must remain distinct.
- Use India datasets when India sector structure is the relevant benchmark; use Global/US when economics or peer universe warrants it.
- Country risk follows where operations/revenues/production create risk, not incorporation alone.
- Revenue exposure is often appropriate for consumer/service businesses, production for natural resources, and a mix for manufacturing.
- Multi-business beta should use business-specific unlevered betas and economically sensible weights. The FCFF workbook uses estimated business value weights based on revenue × EV/Sales.

## Current-data policy
Files such as country premiums, tax rates, betas and implied ERP may become stale. When running a current valuation:
1. Check the as-of date.
2. Prefer a newer approved dataset/API when available.
3. Preserve the old value for reproducibility.
4. Record the exact value, source and date used in the valuation.

## Market-agent separation
Maintain three layers:
- `intrinsic`: cash flows, growth, margins, reinvestment, risk, value.
- `pricing`: multiples, peers, transactions, market-implied expectations.
- `market_event`: consensus, revisions, whisper expectations, catalysts, momentum, flows, index effects.

A market event should only change intrinsic value if it changes a value driver. Technical flows/sentiment may affect price without changing value.

## Required audit output for each valuation
Store:
- facts used and sources
- normalizations
- assumptions and rationales
- model selected and why
- base/bull/bear or distributions where material
- intrinsic value
- pricing comparison
- price/value gap
- key sensitivities
- assumptions changed since prior valuation
- attribution of value change
- unresolved conflicts/data gaps

## Never do these
See `knowledge/anti_patterns.jsonl`. Most important: do not use a giant TAM uncritically; do not choose peers/multiples to justify a desired price; do not put all uncertainty into WACC; do not treat one case assumption as doctrine; do not double count cash/cross-holdings/growth; do not let stable growth exceed economic constraints without explicit override.
