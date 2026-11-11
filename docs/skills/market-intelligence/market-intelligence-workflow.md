# Market Intelligence Workflow Skill

## Purpose

Build source-backed intelligence workflows for events, evidence, scoring, alerts, thesis impact, narratives, daily briefs, and portfolio exposure.

## When to use

- Event extraction/scoring.
- Alert generation/review.
- Evidence ledger.
- Thesis impact or contradiction workflows.
- Narrative/research workspace.
- Daily brief or portfolio-impact intelligence.

## When NOT to use

- Pure valuation math.
- Provider setup without intelligence outputs. Use `data-ingestion-workflow`.

## Prerequisites

- Read `docs/product-brief.md`, `docs/scoring.md`, and `docs/current-state.md`.
- Inspect route/service/model/tests for the relevant object.

## Inputs

- Source document or event.
- Company/thesis/portfolio context.
- Scoring config.
- Evidence and freshness metadata.

## Outputs

- Source-backed events, alerts, evidence, brief items, thesis impacts, or narrative records.
- Explainable scoring and review states.

## Workflow

1. Start from stored source material or explicit user input.
2. Preserve source links and timestamps.
3. Extract or update events deterministically where possible.
4. Score with visible inputs, weights, and explanation.
5. Link to thesis, narrative, and portfolio exposure when applicable.
6. Create alerts only when thresholds and evidence support them.
7. Show review status and human feedback fields.
8. Keep AI output labeled as interpretation.
9. For alert evidence, resolve the user-owned alert before following event and
   document links. For event evidence, require authentication and filter
   thesis/valuation impacts through user-owned parents.
10. Return bounded source metadata and claim context. Never serialize raw filing
    bodies, provider payloads, document bytes, or another user's alerts.
11. Record locator precision explicitly as document, page, section, or none.
    Do not imply exact-passage support when only a document link exists.
12. Keep AI evidence phases distinct: a source marker declares provenance, a
    deterministic lexical candidate proposes an exact span, the validator proves
    stored-text identity, and human review decides whether the claim is usable.
13. Scheduled Daily Brief generation remains deterministic and no-external-AI;
    external AI checks belong only to explicit refresh actions.
14. Unified search may combine shared evidence and private research only when
    every model retains its ownership and claim-type semantics. Index user
    messages as assumptions; index assistant output only through an approved,
    successful, reviewed, and unblocked AI record.
15. For private-source comparison, retain exact quotes, duplicate/exclusion coverage,
    source scope and immutable analyst receipts. Unknown or incompatible periods
    cannot silently become corroboration; opposing directions are not verified
    contradictions. Hash/version changes invalidate current review applicability.
16. When adding reviewed research to a scheduled snapshot, preserve owner scope,
    claim types, as-generated dates and stale/exclusion states. Do not rewrite old
    briefs or call AI from deterministic scheduled reads/generation.

## Acceptance criteria

- Every meaningful claim has a source or claim type.
- Scores expose formula inputs and explanation.
- Alerts are not buy/sell recommendations.
- UI allows tracing from alert to source evidence.
- Missing evidence is an explicit missing/partial state.
- Evidence responses include claim type, confidence, source timestamp, and
  locator precision.
- Selecting a passage candidate cannot validate or approve an AI output.
- Searchability cannot turn a narrative or reviewed AI interpretation into a fact.

## Common mistakes

- Summarizing without evidence.
- Hiding score formulas.
- Treating AI interpretation as fact.
- Creating high-confidence alerts from weak source text.
- Returning ORM objects from an evidence endpoint.
- Treating a document-level link as an exact source citation.

## Do not do

- Do not scrape Twitter/X or Reddit HTML.
- Do not call market regime a buy/sell signal.
- Do not create action language like "buy now" or "sell."

## Related skills

- `data-ingestion-workflow`
- `frontend-data-state`
- `security-review`
- `valuation-workflow`

## References

- `docs/product-brief.md`
- `docs/scoring.md`
- `docs/roadmaps/product-roadmap.md`
