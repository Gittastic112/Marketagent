# Market Intelligence Engine Agent Operating Manual

**Purpose:** Replace the existing `AGENTS.md` with a sharper, more operational version for Codex, Antigravity, Claude Code, Cursor, or any AI coding agent working in this repository.

**Core idea:** This file is not a product brochure. It is an operating manual for agents. It should prevent common AI-agent failures: giant diffs, fake completed features, unsafe migrations, frontend mock data presented as real, fragile API changes, undocumented security risks, and feature creep.

---

# 0. How To Use This File

## 0.1 Placement

Place this file at the repository root as:

```text
AGENTS.md
```

If the repo later becomes large, create narrower `AGENTS.md` files inside specific directories, for example:

```text
backend/AGENTS.md
frontend/AGENTS.md
docs/AGENTS.md
```

More specific directory instructions should override root instructions for files inside that directory.

## 0.2 Instruction Precedence

When deciding what to do or how to behave, follow instructions in this order:

1. User request
2. Nearest applicable nested AGENTS.md
3. Parent/root AGENTS.md
4. Task-specific current docs
5. Framework conventions

## 0.3 Factual Truth Precedence

When deciding what is currently true about the system state, follow evidence in this order:

1. Running code and database reality
2. Tests
3. Current state documentation (`docs/00-current-state.md`)
4. Archived historical documentation
5. Planning documents

If instructions or facts conflict, stop and report the conflict. Do not guess silently.

## 0.4 Main recurring failure to avoid

Do not make the app look more advanced than it really is.

This repo is an investment intelligence app. Incorrect confidence is dangerous. A beautiful dashboard with stale, fake, or unsupported data is worse than an ugly but honest tool.

---

# 1. Project Summary

This repo is a local-first Market Intelligence Engine and portfolio tracker for public equity research.

It combines:

- company watchlists
- SEC filings
- RSS/news ingestion
- raw document storage
- event extraction
- explainable scoring
- alerts
- thesis notes
- portfolio holdings and transactions
- manual or provider-backed market prices
- valuation/DCF workflows
- data health monitoring
- future source-backed AI research

The core product question is:

```text
What changed, why does it matter, how credible is it, does it affect my thesis, and how exposed am I through my portfolio?
```

The product should become a source-backed investment cockpit, not a generic AI chatbot or a fake Bloomberg clone.

---

# 2. Product North Star

Every major feature should help answer at least one of these:

1. What changed since I last checked?
2. What evidence supports the claim?
3. How reliable is the information?
4. Is the data fresh, stale, partial, mocked, or missing?
5. Does this affect my thesis?
6. Does this affect a portfolio holding or exposure?
7. What assumptions drive the valuation?
8. What would falsify the investment thesis?
9. What should I inspect next?

If a proposed feature does not help answer one of these questions, do not build it without explicit approval.

---

# 3. Non-Negotiable Product Rules

## 3.1 No fake intelligence

Do not present mock, placeholder, hardcoded, guessed, or synthetic data as real.

If data is mocked, show a visible label:

```text
Mock Data
```

If a backend endpoint is missing, the frontend must show:

```text
Not available yet
```

or:

```text
Backend endpoint not implemented
```

Do not invent frontend numbers to make the UI look complete.

## 3.2 No buy/sell recommendations

The app may show:

- valuation attractiveness
- market regime support
- risk warnings
- evidence strength
- thesis support or contradiction
- decision readiness
- portfolio impact

The app must not say:

```text
Buy this stock
Sell this stock
You should buy now
Guaranteed upside
```

Acceptable language:

```text
Market structure appears supportive for cautious accumulation.
```

```text
The setup is incomplete because the latest filing has not been reviewed.
```

```text
The model suggests upside under the user's assumptions, but terminal value dependence is high.
```

## 3.3 Every claim must have a type

Any meaningful insight should be labeled as one of:

- Fact
- Source Summary
- Calculation
- User Assumption
- AI Interpretation
- Estimate
- Mock Data

## 3.4 Every important output needs traceability

For alerts, summaries, scores, DCF outputs, narrative claims, and AI outputs, preserve or display:

- source
- timestamp
- data freshness
- calculation basis
- confidence or uncertainty
- linked raw document or input assumption
- what would change the conclusion where applicable

---

# 4. Documentation Source of Truth

## 4.1 Docs reading order

Before major changes, read these files:

```text
docs/HANDOFF.md
docs/00-current-state.md
docs/02-architecture.md
docs/roadmaps/product-roadmap.md
```

Then read only the task-specific current reference:

```text
docs/README.md
```

Do not read `docs/archive/` as current instructions. Archived checkpoints and
plans are historical evidence only. Search them by basename when a task needs
the rationale or validation record for an older implementation.

## 4.2 Code beats docs

Docs may be stale. The agent must verify the actual code before claiming a feature exists.

For any requested change, inspect:

```text
backend/app/
backend/alembic/versions/
backend/tests/
frontend/app/
frontend/components/
frontend/lib/
frontend/types/
docker-compose.yml
.env.example
```

Do not rely only on `README.md` or planning docs.

## 4.3 Update docs only when reality changes

When code changes affect behavior, update the relevant docs in the same task.

But do not rewrite all docs casually. Update only the docs affected by the change.

---

# 5. Standard Agent Workflow

Every coding task must follow this sequence.

## 5.1 Step 1: Restate the task briefly

State what you are about to do in one or two sentences.

Example:

```text
I will add the API response envelope to the health endpoint and one low-risk read endpoint, then update the frontend fetcher to tolerate both old and new response shapes.
```

## 5.2 Step 2: Inspect before editing

Before making changes, inspect relevant files.

Minimum inspection by task type:

| Task type | Files to inspect |
|---|---|
| Backend API | router, schema, service, model, tests |
| Database change | model, existing migrations, current schema docs, tests |
| Frontend page | page file, components, fetch client, types, existing styles |
| Ingestion | provider/service, processing run model, tests, security doc |
| DCF/valuation | valuation models, service, tests, finance formulas |
| Security | `.env.example`, config, logs, proxy, routes, user input paths |
| Docs | current-state, runbook, architecture, relevant feature doc |

## 5.3 Step 3: Make a small plan

Before editing, produce:

```text
Plan:
1. ...
2. ...
3. ...

Files likely to change:
- ...
```

If the change would touch more than 10 files, split it into phases unless the user explicitly asked for a large refactor. Note that the foundational features (like the DCF engine) are already built, so future agent work should be focused, narrow enhancements.

## 5.4 Step 4: Add tests first where practical

For backend behavior, add or update tests before implementation.

For frontend utility logic, add tests where the repo already has a test pattern.

For visual-only changes, add tests only if the repo has a feasible component or snapshot test setup.

## 5.5 Step 5: Implement the smallest safe change

Avoid broad rewrites. Do not reformat unrelated files.

## 5.6 Step 6: Run focused validation

Run the smallest relevant tests first. Then run broader tests if reasonable.

## 5.7 Step 7: Report exactly

At the end, report:

```text
Files changed:
- ...

Tests run:
- ...

Manual checks:
- ...

Known limitations:
- ...

Next recommended task:
- ...
```

Do not say "done" unless tests or manual checks support it.

---

# 6. Stop Conditions

Stop and ask for direction if any of these occur:

1. Alembic migration chain is broken.
2. A migration would drop or rewrite existing data.
3. A requested change requires storing broker credentials.
4. A requested change exposes API keys to frontend code.
5. A frontend feature would require fake data to look complete.
6. A test failure appears unrelated to the current task.
7. The requested change requires scraping a site that may prohibit scraping.
8. The task would require a public deployment security model.
9. The implementation touches more than 10 files without a clear reason.
10. Docs and code strongly contradict each other.
11. You cannot verify whether a feature is real or mocked.
12. The task would create buy/sell recommendation language.

When stopping, include:

```text
Blocked because:
Options:
Recommended option:
```

---

# 7. Git and Diff Discipline

## 7.1 No giant diffs

Keep changes narrow.

Good:

```text
Add API envelope to health endpoint and frontend fetcher compatibility.
```

Bad:

```text
Refactor backend, redesign dashboard, add DCF, change schema, update all docs.
```

## 7.2 Commit-sized phases

Prefer tasks that could become a single clean commit.

Suggested commit scopes:

```text
chore: stabilize healthcheck
feat: add api response envelope foundation
feat: add data state components
feat: add processing run status endpoint
feat: add revenue-driven dcf service
feat: add dcf guardrail warnings
feat: add market regime manual inputs
test: add valuation engine coverage
docs: reconcile current state with code
```

## 7.3 Never hide unrelated changes

If you touch unrelated files accidentally, revert them or explain why they changed.

---

# 8. Local Development Rules

## 8.1 Standard local commands

Use these commands from repo root.

Start all services:

```bash
docker compose up -d
```

Rebuild services:

```bash
docker compose up --build -d
```

Stop services:

```bash
docker compose down
```

Delete local database volume, only if explicitly acceptable:

```bash
docker compose down -v
```

Check containers:

```bash
docker compose ps
```

Backend logs:

```bash
docker compose logs backend --tail=100
```

Frontend logs:

```bash
docker compose logs frontend --tail=100
```

Backend health:

```bash
curl http://localhost:8000/api/health
```

Run migrations:

```bash
docker compose exec backend alembic upgrade head
```

Inspect migration heads:

```bash
docker compose exec backend alembic heads
```

Inspect DB migration version:

```bash
docker compose exec postgres psql -U marketintel -d marketintel -c "SELECT * FROM alembic_version;"
```

## 8.2 Docker socket permission

If Docker says:

```text
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

Do not recommend:

```bash
sudo chmod 666 /var/run/docker.sock
```

Instead:

1. Confirm Docker Desktop is running.
2. Restart Docker Desktop.
3. Check Docker context.
4. Run commands in normal Mac Terminal, not inside a restricted sandbox.

## 8.3 Frontend cannot reach backend

Use this checklist:

1. Is backend running?
2. Is frontend running?
3. Does `curl http://localhost:8000/api/health` work?
4. Does backend log show Python stack traces?
5. Is `NEXT_PUBLIC_API_BASE_URL` correct?
6. Is the frontend proxy using the correct backend URL?
7. Is CORS configured if direct browser calls are used?
8. Are migrations failing at backend startup?

## 8.4 Alembic missing revision

Known error:

```text
Can't locate revision identified by 'a2afaa43a162'
```

Do not immediately run destructive commands.

First inspect:

```bash
ls backend/alembic/versions
grep -R "a2afaa43a162" backend/alembic/versions || true
docker compose exec postgres psql -U marketintel -d marketintel -c "SELECT * FROM alembic_version;"
docker compose exec backend alembic heads
```

If this is disposable local data, the clean reset may be acceptable:

```bash
docker compose down -v
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

If preserving data matters, do not wipe volumes. Restore missing migration or stamp carefully only after explaining risk.

---

# 11. Security Rules

## 11.1 Secrets

Never commit:

```text
.env
API keys
bearer tokens
broker tokens
model keys
database passwords beyond local placeholders
```

`.env.example` must contain placeholders only.

Frontend must never contain:

```text
DATABASE_URL
SEC_USER_AGENT
OPENAI_API_KEY
GEMINI_API_KEY
ALPHA_VANTAGE_API_KEY
FRED_API_KEY
broker tokens
```

## 11.2 External input

Treat these as untrusted:

- RSS feed content
- SEC filing text
- CSV imports
- markdown/text uploads
- user-provided URLs
- social posts
- AI output
- provider API responses

Do not render imported HTML as trusted HTML.

## 11.3 URL fetching and SSRF

Do not allow user-controlled URLs to make backend fetch arbitrary internal resources.

If adding URL ingestion:

- validate scheme
- allow only `http` and `https`
- block localhost/private IP ranges
- use timeouts
- limit response size
- log provider errors safely

## 11.4 CSV import/export

Before CSV import:

- validate every row
- validate dates, quantities, prices, currencies
- return row-level errors
- enforce file size limits

Before CSV export:

- escape cells starting with:
  - `=`
  - `+`
  - `-`
  - `@`

## 11.5 AI security

Before AI features:

- create AI output provenance storage
- store model name
- store prompt version
- store input hash
- store generated timestamp
- link source IDs
- store limitations
- store confidence label
- store review status

Do not send private portfolio data, thesis notes, or DCF assumptions to external AI unless the feature explicitly requires it and logs the action.

## 11.6 Broker integrations

Do not store broker passwords.

Broker sync requires:

- official OAuth/token flow
- encrypted token storage if persisted
- explicit permission model
- audit logging
- revocation path

Do not build broker sync until security design is approved.

## 11.7 Public deployment

Do not expose this app beyond localhost until these exist:

- authentication
- authorization
- HTTPS
- CSRF review
- strict CORS
- rate limiting
- secret manager
- backup policy
- privacy model
- audit logging

---
