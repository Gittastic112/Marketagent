# Data Ingestion Workflow Skill

## Purpose

Add or debug ingestion while preserving provenance, processing runs, freshness, and security boundaries.

## When to use

- SEC, RSS, macro, market data, manual filing, provider, or source capability work.
- Adding a new external data source.
- Debugging ingestion failures.
- Changing provider health behavior.

## When NOT to use

- Pure valuation math changes with no source ingestion.
- UI-only display of already-ingested data.

## Prerequisites

- Read `docs/data-sources.md` and `docs/security.md`.
- Inspect provider/service, processing run model, relevant route, and tests.

## Inputs

- Source/provider.
- Company or market context.
- Credentials or explicit not-configured state.
- Expected freshness and provenance.

## Outputs

- Stored raw/normalized data with source links.
- Processing run with counts/errors.
- Provider health/source capability status.
- Tests using injected/mocked HTTP calls.

## Workflow

1. Classify the source: official API, licensed feed, RSS, SEC, manual, or unsupported.
2. Start the Processing Run for the attempted action and validate configuration
   before fetching; record not-configured/blocked outcomes without secret values.
3. Fetch through a provider/service, not route code.
4. Store raw payload/text and provenance.
5. Deduplicate safely.
6. Finish the run using the existing standardized outcome, counts, safe errors
   and metadata. Preserve duplicate, partial, failure and skipped distinctions.
7. Return explicit configured/failing/manual-only/not-supported states.
8. Test with mocks or injected clients.
9. For SEC ingestion, accept an optional preferred source id, validate it as an
   SEC-compatible source, and otherwise resolve/create the local SEC source.
   Do not make a source dropdown a prerequisite for an official-provider flow.
10. Keep downstream event/alert summaries bounded; collection routes should use
    raw-document summaries instead of transferring entire filing bodies.
11. Downstream search or citation helpers may inspect stored source text inside
    services, but responses must contain bounded exact spans and locators rather
    than the full raw body.

## Acceptance criteria

- No silent ingestion failures.
- No live network calls in automated tests.
- Source, timestamp, freshness, and errors are visible.
- Duplicate, preview, success, partial, and failure outcomes remain distinguishable in processing-run history.
- Unsupported providers do not appear live.
- Ingestion-created user-owned records carry the authenticated user id.
- Downstream evidence spans remain exact, bounded, and linked to stored source provenance.

## Common mistakes

- Hardcoding provider assumptions globally.
- Treating RSS or filing text as trusted HTML.
- Dropping failed rows without row-level errors.
- Bypassing processing runs.

## Do not do

- Do not scrape prohibited sites.
- Do not store broker passwords.
- Do not hardcode spreadsheet row numbers.
- Do not fabricate market/rate data when providers are missing.

## Related skills

- `security-review`
- `backend-api-change`
- `financial-statement-extraction`
- `local-operations`

## References

- `docs/data-sources.md`
- `docs/security.md`
- `docs/current-state.md`
