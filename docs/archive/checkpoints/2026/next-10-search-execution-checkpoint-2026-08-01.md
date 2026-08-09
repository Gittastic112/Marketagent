# Next 10 Search Execution Checkpoint

Date: 2026-08-01

This checkpoint follows the reliability batch in
`next-10-execution-checkpoint-2026-08-01.md`. The Linux ARM64 frontend repair
was completed first because the application could not compile reliably in the
normal Docker development layout.

## Blocking Error Repair

The lockfile already contained `lightningcss-linux-arm64-gnu`. The failure was
caused by `./frontend:/app` exposing Mac `node_modules` to the Linux container.
Docker Compose now masks `/app/node_modules` and `/app/.next` with
container-only volumes and runs `npm ci` inside Linux before `next dev`.

Upgrade an existing local frontend without deleting PostgreSQL data:

```bash
docker compose up --build -d --force-recreate --renew-anon-volumes frontend
```

## Ten Completed Search Tasks

| # | Task | Verified result | Remaining limit |
|---:|---|---|---|
| 1 | Expand result contracts | Six record types and three claim types are explicit in backend/frontend schemas | Research messages, AI outputs, and sections are not separate result types |
| 2 | Thesis search | Title/body search is owner-scoped and links to the thesis | Mutable text has no immutable locator |
| 3 | Alert search | Alert fields are owner-scoped; manual alerts are `User Assumption`, generated alerts are `Source Summary` | Alert-generation provenance is not a ranking feature |
| 4 | Decision search | Decision creation now persists/validates `company_id`; search is owner-scoped and deep-links to the company journal | The page does not yet focus the selected decision row |
| 5 | Valuation search | Owned model name/description search links to the exact model | Assumption-level search and evidence graph remain |
| 6 | PostgreSQL indexes | Four new GIN expression indexes extend the existing document/event indexes | Index size and maintenance cost need representative corpus measurement |
| 7 | Filtering and metadata | `type`, `company_id`, bounded result limits, UTC timestamps, processing time, source labels, and warning metadata are implemented | Saved queries and advanced facets remain |
| 8 | Search UI | Corpus menu, result/claim badges, source timestamps, data-state notices, and deep links are visible | No inline exact highlighting for mutable records |
| 9 | Automated contracts | Ownership, filtering, timestamp normalization, ranking output, and a maximum 14-query/750-ms local backend budget are tested | The latency fixture is small and not a load test |
| 10 | Browser workflow | Authenticated production-stack search creates, finds, links, and filters four owned research record types | Live multi-user concurrency and large-corpus rendering remain |

## Architecture Decisions

- Documents rank at base `1.0`, events `0.9`, alerts `0.85`, theses `0.8`,
  decisions `0.75`, and valuations `0.7`; PostgreSQL `ts_rank_cd` refines rank
  within each class. This intentionally keeps stored source evidence ahead of
  mutable judgment records.
- User-authored search records carry `User Assumption`, not `Fact`.
- Search normalizes legacy timezone-naive valuation timestamps to UTC at the
  response boundary instead of silently comparing mixed datetime types.
- Search returns stored records only. It generates no answer or recommendation.

## Verification

```text
Backend: 358 passed
Frontend: 70 passed
TypeScript: passed
Production build: passed in the isolated Docker browser stack
Alembic: h4h4h4h4h4h4 (single head)
Playwright: 14 passed
Repository static gates: secret scanner tests, secret scan, and 11 skill docs passed
Diff validation: git diff --check passed
```

The responsive semantic gate waits for React's hidden server-stream transport
node to be applied before auditing duplicate IDs. Interactive selectors target
visible controls so temporary hidden stream payloads cannot create false strict
locator failures.

## Honest Next Gate

Evaluate ranking against a representative corpus before changing weights.
Then add section-level results and assumption-level valuation provenance. Real
US/India normalized-history certification remains the higher trust blocker and
is still at zero certified histories.
