# Agent Operating Rules

Local-first equity research, valuation and portfolio software with source traceability.
Do not make the app look more capable or certain than it is.

## Compact repository map

```json
{
  "backend/app": {"entry": "main.py", "owners": ["api/routers", "schemas", "services", "models", "providers"]},
  "backend/tests": "backend behavior and isolated fixtures",
  "backend/alembic": "ordered database migrations",
  "frontend": {"entry": "app/layout.tsx", "owners": ["app", "components", "lib/api", "e2e"]},
  "scripts": "repository checks and operations",
  "docs": {"start": "HANDOFF.md", "lookup": "code-map.md", "commands": "08-execution-runbook.md"},
  "data": "runtime assets and versioned review receipts",
  "damodaran_knowledge_base_v1": "immutable source corpus; read its AGENTS.md"
}
```

Quick checks: `python3 scripts/check_docs.py`; `npm --prefix frontend test`;
`npm --prefix frontend run typecheck`. Backend tests and production builds use the
[runbook's environment table](docs/08-execution-runbook.md#choose-the-right-environment).

## Start with the smallest relevant context

1. Read [the handoff](docs/HANDOFF.md) and the nearest nested AGENTS.md.
2. Search [the code map](docs/code-map.md) for the affected domain, then read its
   matching row and owning files. Do not load the whole map for a narrow change.
3. Read only the relevant current reference from [the docs index](docs/README.md).
4. For major architectural work, also read [current state](docs/00-current-state.md),
   [architecture](docs/02-architecture.md), and [the roadmap](docs/roadmaps/product-roadmap.md).
5. Use `rg --files <owning-directory>` before content searches, with bounded output.
   Inspect actual code before editing. Archive files are historical evidence,
   not current instructions or an execution queue.

Routine searches honor .gitignore/.rgignore. Open an exact lockfile, decision
register or historical path only when needed; never run an unrestricted dump of
the repository, raw corpus or output directory. Respect protected-file restrictions.

Specific directory rules refine these rules. User instructions take precedence
over repository instructions. For facts, prefer running code/database, then
tests, current-state docs, archived evidence, and finally plans. Report meaningful
conflicts; do not guess silently.

## Workflow

- For an assigned parallel batch, use [Knull](Knull%28readme%29.md) and its
  [exclusive file ownership](docs/workstreams/ownership.tsv). Unlisted paths and
  shared contracts are frozen during parallel edits. Request boundary changes
  through the coordinator; never duplicate another agent's implementation.
  A plan does not itself launch agents. Central docs are reconciled once after
  integration; each agent keeps evidence in its own allocated directory.
- Restate the task in one or two sentences.
- Check git status first. Preserve user/prior-agent changes and untracked files.
- Inspect the owning route, contract, service, model, callers, and tests.
  Inspect migrations for persisted changes; inspect auth and input paths for
  security changes.
- State a small plan and likely files. Split changes into commit-sized phases.
  More than 10 files requires an explicit cross-cutting reason.
- Add regression tests first where practical. Implement the smallest safe change.
  Do not reformat unrelated files or invent a framework to wrap one function.
- Run focused tests, then broader checks proportional to risk. A build is not a
  browser test; Mock Data proof is not genuine-input proof.
- Update only affected current docs. Keep limitations in
  [one ledger](docs/agent_capabilities_and_limitations.md), not duplicate chat lists.
- Report changed files, tests, manual checks, unresolved risks, and next work.
  Do not claim completion without evidence.

## Product truth and traceability

- Never present placeholder, guessed, synthetic, or stale data as live fact.
  Label fixtures **Mock Data**. Missing endpoints show **Not available yet**.
- Preserve loading, empty, error, stale, partial, not-configured, mock, and success
  states. Transport failure is unavailable, not stale cached data.
- Meaningful claims must be Fact, Source Summary, Calculation, User Assumption,
  AI Interpretation, Estimate, or Mock Data.
- Important outputs retain source, timestamp/as-of date, freshness, basis,
  uncertainty, source/input links, and relevant review state.
- Valuation and risk outputs structure judgment. Never emit buy/sell
  recommendations, guaranteed upside, or trading instructions.
- Reviewed benchmark priors are not company facts. AI output cannot silently
  overwrite reviewed evidence or valuation assumptions.

## Dependency and code boundaries

- HTTP routes validate, authorize, and serialize. Services own workflows and
  calculations. Models own persistence, not response formatting.
- Keep calculations deterministic and backend-owned. Frontend owns presentation.
- New valuation contracts belong in backend/app/schemas, not the legacy HTTP
  facade. Pure inputs and calculation outputs must not depend on HTTP or ORM.
- New frontend API work belongs in the domain modules under frontend/lib/api.
  The old api.ts is a compatibility facade, not a place for new implementations.
- Do not bypass existing auth, response envelopes, provenance, or review gates.
- Do not move public imports without a compatibility or migration plan.
- Do not add dependencies without a concrete need. Check the manifests/lockfile
  and existing helpers first.
- Prefer shallow domain ownership, not a flat folder or catch-all utilities module.
  Preserve framework routes, package boundaries, migrations and public imports.
- Cleanup starts with measured sizes, callers and tracked status. Untracked is not
  disposable. Delete only identified generated material; retain source reports,
  review receipts, backups, failed evidence and rollback images. Ignore rules
  control discovery, not retention. Record removed paths and actual byte savings.

## Security and external input

- Never commit secrets or print environment/credential values. .env.example uses
  placeholders. Provider/database keys, SEC identity, encryption keys, and broker
  tokens must not enter browser code. Server-only session signing stays server-only.
- Treat uploads, CSV, URLs, RSS/SEC text, provider responses, and AI output as
  untrusted. Never render imported HTML as trusted content.
- URL fetching: allow only HTTP(S), reject private/loopback destinations, bound
  response size and time, and sanitize errors. Reuse the existing safe-URL helper.
- CSV imports validate every row, size, dates, quantities, prices, and currencies.
  Exports escape formula-leading =, +, -, and @ cells.
- External ingestion/provider actions require observable Processing Runs:
  configuration, timing, counts, failures, freshness, and source context.
- AI output must retain model/provider, prompt version, input hash, source IDs,
  generation time, limitations, confidence, and review status. No private
  portfolio, thesis, or DCF data goes to external AI without a feature explicitly
  requiring it, disclosure, and audit evidence.
- No broker passwords. Broker sync requires an approved official OAuth/token
  design, encrypted persisted tokens, explicit permissions, audit, and revocation.
- Public deployment is not authorized. It needs authentication/authorization,
  HTTPS, CSRF/CORS review, rate limits, secrets, backups, privacy, and audit logging.
  Checked-in Compose ports bind 127.0.0.1; older running containers can retain
  all-interface bindings until recreated. Inspect actual ports; do not broaden exposure.

## Stop and request direction

Stop for a broken migration chain, destructive data rewrite, exposed secrets,
broker credential storage, unapproved public deployment, prohibited scraping,
fake data required to complete a feature, buy/sell language, an unrelated test
failure, unverifiable real/mock status, or a strong unresolved code/docs conflict.
Explain the blocker, options, and recommended option.

Never reset/clean/revert user work, drop a database volume, stamp migrations, or
delete source files to make tests pass. Confirm exact targets and data-loss
authorization before destructive operations. Never chmod a Docker socket to 666.

## Commands and documentation ownership

[Execution runbook](docs/08-execution-runbook.md) owns development and validation
commands. [Local setup](docs/07-local-development.md) owns environment and Docker
troubleshooting. [Architecture](docs/02-architecture.md) owns runtime boundaries.
[Project workflows](docs/skills/README.md) are optional task-specific references,
not a second universal instruction stack. The separate knowledge-base AGENTS.md
governs its immutable source corpus.

Read only the workflow matching the task; add security/operations references when
their boundaries are actually involved. A packaged SKILL.md and implicit
invocation metadata do not prove that a skill is installed in the agent session.

Keep this file under 160 lines and the handoff under 120. Replace status instead
of appending history. Run python3 scripts/check_docs.py after documentation edits.
