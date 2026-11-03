# Repository architecture refactor

Date: 2026-09-09. Scope: architecture and agent navigation, not new financial
features, dependency upgrades, migration changes or a normal-runtime deployment.

## Review and issues found

Reviewed the root/nested agent manuals, current handoff/state/architecture and
roadmap, active document/workflow indexes, CI/release/browser scripts, runtime
manifests, dependency manifests, application entry points, identity/proxy path,
router/model/service/provider structure, schema/client definitions and test layout.
The separate knowledge-base boundary and untracked scratch material were treated
as distinct from application code. This is an architectural review, not a claim
to have audited every financial formula, dependency vulnerability or source file.

Concrete issues:

1. Backend HTTP schemas mixed unrelated domains in 3,353 lines. Calculation
   services imported that HTTP collection, loading unrelated contracts.
2. Two different FinancialMetricRead classes silently reused one name. The chart
   export hid the stored-record definition and generated unstable OpenAPI names.
3. Frontend lib/api.ts mixed 3,838 lines of contracts, configuration, transport,
   parsing and domain requests. Server API code imported this browser graph just
   for a shared type/error; JSON requests and metadata envelopes were duplicated.
4. Root/nested instructions mixed hard rules with speculative directory trees
   and product planning. Agent cold start included a 533-line handoff and a
   465-line current-state history despite rules saying not to append history.
5. Documentation checks omitted backend/frontend nested AGENTS.md and were not
   wired into CI/release verification. No guard prevented onboarding bloat.
6. Large action/UI/service owners, split provider placement, manually mirrored
   types and source-string tests remain follow-ups. Unverified root scripts were
   not safe deletion candidates in this heavily dirty worktree.

## Implemented phases

### Backend contracts

- Extracted 30 valuation classes into valuation_inputs.py, valuation_outputs.py
  and valuation.py under backend/app/schemas.
- Preserved compatibility exports as the same class objects.
- Migrated seven valuation-service imports to narrow owning contracts.
- Kept input/output contracts importable without HTTP, ORM or service modules.
- Renamed the stored metric definition to StoredFinancialMetricRead; kept the
  legacy chart FinancialMetricRead export and both response field sets.
- Added seven boundary/compatibility tests. Financial formulas, validators,
  ownership, non-writing historical reconciliation and persistence are unchanged.

### Frontend APIs

- Replaced lib/api.ts with a compatibility-only export facade.
- Split domain contracts and endpoints into named modules under lib/api, all
  below 600 lines; the largest is the relative-valuation module.
- Isolated shared envelope/error identity in contract.ts and browser HTTP in
  transport.ts. Cross-domain references are type-only.
- Consolidated JSON mutations, checked requests, optional-404 reads, binary
  exports and error envelopes. Preserved existing request bodies, multipart
  content-type handling, response/error semantics, default-client envelopes and
  aliases. Server GET/POST metadata handling now shares one implementation.
- Server API imports only the shared contract; its runtime connection, session
  decoding, timeout and signed-identity boundaries remain intact.
- Added nine behavioral/export/dependency checks. Existing static integrity
  assertions now inspect the owning domain files instead of one monolith.

### Navigation and verification

- Root manual: 657 to 115 lines; backend manual to 99 and frontend to 71.
- Handoff: 533 to 73 lines; current state: 465 to 105 lines.
- Archived the original manuals/current-state/handoff/readme/runbook instead of
  discarding historical evidence. No source datasets or unknown scratch files
  were deleted or relocated.
- Added docs/code-map.md, clarified document ownership and selective workflow
  reading, updated actual dependency paths and production-vs-development commands.
- Added nested-agent discovery and onboarding line budgets to the docs checker,
  three checker regressions, and CI/release-script invocation.
- Remaining issues stay in docs/agent_capabilities_and_limitations.md.

## Validation

- Baseline frontend suite before edits: 191 passed.
- New backend boundary tests failed before extraction, then passed afterward.
- Focused backend valuation/boundary suite: 55 passed.
- Full source-mounted backend suite: 852 passed, four upstream openpyxl UTC
  deprecation warnings. Fixtures were isolated; normal user data was not changed.
- Full frontend suite: 200 passed. TypeScript passed.
- Full OpenAPI comparison: all 263 paths and 468 schemas retained. After
  canonicalizing the deliberate stored/chart metric component-name distinction,
  the before/after document is identical. OpenAPI component names/titles for that
  collision changed; JSON request/response shapes did not.
- Production frontend, backend and scheduler images built successfully. Next.js
  authenticated pages remained dynamic. The normal containers were not replaced.
- Documentation checker tests: seven passed. Secret-checker tests: two passed.
  All eleven project workflow validations passed. git diff --check passed.
- Documentation gate: 65 active Markdown files and 366 local links checked.
- Knowledge-base read-only audit: 61 canonical files, 61 catalog rows, 38 ledger
  rows and no pending inbox files. Four audit tests passed. Corrected the runbook
  to use unittest discovery so the tool's local imports resolve from the root.
- Final rerun after cleanup: seven backend schema-boundary tests, all 200
  frontend tests, TypeScript and seven documentation-checker tests passed.

### Focused production browser proof

Used Playwright against the production images in the isolated
architecture-review-20260909 Compose project, with a tmpfs database and frontend
bound only to 127.0.0.1:13106. The stack had stopped during the interruption;
restarting it recreated the disposable database, not the normal user database.

- Local credential sign-in and authenticated dashboard passed.
- Created an explicitly named Mock Data company/model through the signed browser
  proxy. Saved assumptions returned a finite output and the saved valuation page
  rendered its USD estimate, source/input warnings and unavailable comparison
  price without inventing a quote.
- Clicking Scenario Range exercised the compiled frontend client and returned
  HTTP 200. All six deterministic scenarios rendered; the base case matched the
  saved estimate and absent-price gaps remained unavailable.
- Daily Brief navigation returned HTTP 200 and rendered the empty source set,
  disabled schedule and no saved briefs. No AI refresh or ingestion was invoked.
- The browser console reported zero errors and zero warnings for the completed
  route checks. Snapshots remain under output/playwright/.playwright-cli.

This is focused Mock Data compatibility proof, not genuine-input certification,
a full responsive matrix, or a test of every valuation panel. The browser session
and disposable containers/network were removed after verification; their tmpfs
fixtures are intentionally nonpersistent. Normal containers and data were untouched.

## Deliberate exclusions

No database migrations, finance-default changes, dependency updates, user-data
imports, skill permission changes, public deployment or broker integration.
Backend non-valuation schemas are not yet fully modular. Large workflows and
existing saved-input/Reverse-DCF limitations were not hidden by this refactor.
No commit was created; prior/user work remains uncommitted and preserved.
