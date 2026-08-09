# Market Intelligence Engine

## What this project is

This project is a local-first Market Intelligence Engine and portfolio tracker
for public equity research.

It is not a trading bot.
It is not a generic AI summarizer.
It is not a Bloomberg clone.

It is a source-backed research and portfolio system that helps track:

- companies
- filings
- news
- macro data
- market data
- thesis notes
- holdings
- transactions
- portfolio exposure
- valuation assumptions
- catalysts
- narrative shifts
- alerts

The goal is to answer:

> What changed, why does it matter, how credible is it, does it affect my thesis, and how exposed am I through my portfolio?

---

## Product boundary

The current deployment boundary is intentionally narrow:

- local only
- single-user credential login
- source-backed data storage
- reviewed financial facts and evidence
- SEC, RSS, manual PDF, macro, and selected market-data ingestion
- portfolio holdings, transactions, cash, prices, and valuation
- deterministic valuation and scoring
- reviewable AI assistance

Do not add yet:

- trading execution
- buy/sell recommendations
- Twitter scraping
- broker credential storage
- broker sync before OAuth/token security is designed
- payment system
- production deployment

The active product roadmap lives in `docs/roadmaps/product-roadmap.md`.
The repository threat model lives in `docs/06-security-threat-model.md`.

---

## Current implementation status

Use `docs/00-current-state.md` as the source of truth.

Short version:

- Strongest areas: deterministic valuation, evidence/provenance foundations,
  local ownership, Damodaran source versioning, and broad backend coverage.
- Partial areas: India automation, providers, financial layout coverage, daily
  workflow integration, AI citations, portfolio attribution, and frontend parity.
- Not ready: market-regime decisions, broker sync, real-time trading data, or
  public deployment.

---

## Recommended local stack

| Layer | Tool |
|---|---|
| Editor | VS Code |
| AI coding assistant | Codex |
| Version control | Git + GitHub |
| Frontend | Next.js |
| Backend | FastAPI |
| Database | PostgreSQL through Docker |
| Database admin | pgAdmin or TablePlus optional |
| Background jobs | Simple scripts first |
| AI model calls | OpenAI API later |
| Documentation | Markdown files in `/docs` |

---

## Local Docker run

The simplest local path is Docker Compose:

```bash
docker compose up --build
```

Services:

| Service | URL |
|---|---|
| Frontend | `http://localhost:3000` |
| Backend API | `http://localhost:8000` |
| Backend health check | `http://localhost:8000/health` |
| pgAdmin | `http://localhost:5050` |
| PostgreSQL | `localhost:5432` |

The backend container uses PostgreSQL through the Docker service name `postgres`.
The frontend server talks to the backend through the Docker service name
`backend`. Browser-side frontend requests go through the frontend proxy at
`/api/backend`, so the browser does not need to resolve Docker service names.
The development container keeps Linux `node_modules` and `.next` data in
container-only volumes so Mac native packages cannot replace Linux binaries.
After upgrading from an older container layout, recreate only the frontend with:

```bash
docker compose up --build -d --force-recreate --renew-anon-volumes frontend
```

When running the backend directly on the laptop instead of inside Docker, use `localhost` in `DATABASE_URL`.

## Milestone A local verification & Manual Setup

If you are setting up API keys, running verification scripts, or configuring external sources, refer to the detailed [Local Development Guide](docs/07-local-development.md).

After Docker is running, run:

```bash
python3 scripts/verify_milestone_a.py
```

To create/reuse local verification records and test SEC plus three real RSS feeds:

```bash
python3 scripts/verify_milestone_a.py --write --ticker AAPL --form-type 10-K \
  --rss-feed "YOUR_RSS_FEED_1" \
  --rss-feed "YOUR_RSS_FEED_2" \
  --rss-feed "YOUR_RSS_FEED_3"
```

Replace the example RSS URLs with real feeds you want to track. Refer to [docs/07-local-development.md](docs/07-local-development.md) for troubleshooting feed errors and other common verification issues.

---

## Damodaran Valuation Benchmarks

The Market Intelligence Engine features a fully structured valuation flow that begins with Damodaran industry benchmarks.

1. **Canonical knowledge vs. app runtime data**: `damodaran_knowledge_base_v1/` is the immutable, hash-audited source and doctrine layer. `data/damodaran/raw/` is the backend runtime mirror mounted into Docker at `/workspace/data/damodaran/raw/`. Do not treat the runtime mirror as the provenance catalog.
2. **How ingestion works**: Run `docker compose exec backend python /workspace/scripts/ingest_damodaran.py`. The helper ingests a defined subset of the available workbooks; a file being present does not prove parser/database/UI support. Unsupported coverage must remain explicit.
3. **How industry mapping and autofill works**: When creating a valuation model, the user chooses a company, a country, and confirms a Damodaran industry. The app uses the `IndustryMappingService` to match the company's sector to the normalized industries, and uses the `IndustryAssumptionService` to automatically build assumption priors from the ingested benchmark data.
4. **Differentiation of assumptions**: In the final UI, company actuals (extracted from uploaded financials), industry priors (from Damodaran), formula-derived metrics, and user-entered assumptions are explicitly labeled and tracked using an explicit `confidence` and `sourceType`.

Audit the canonical corpus with:

```bash
python3 damodaran_knowledge_base_v1/tools/audit_kb.py
```

See `damodaran_knowledge_base_v1/INDEX.md` and
`damodaran_knowledge_base_v1/PROCESSING_PLAN.md` before adding or using sources.

---

## Folder structure

```text
market-intelligence-engine/
├── README.md
├── AGENTS.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── README.md (Documentation Index)
│   ├── 00-current-state.md
│   ├── 01-product-brief.md
│   ├── 07-local-development.md
│   ├── 08-execution-runbook.md
│   ├── roadmaps/
│   ├── valuation-agent/
│   ├── archive/
│   └── (other numbered docs)
├── backend/
├── frontend/
└── scripts/
```

---

## Build principle

Build the source-backed system first.

Then add AI.

Bad architecture:

```text
Raw source → LLM summary → answer
```

Better architecture:

```text
Raw source → stored with provenance → normalized event → scored → brief/alert
```

AI should assist the system. It should not replace the system.
