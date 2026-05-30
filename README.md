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

## First MVP

The first version should be intentionally narrow:

- local only
- 10 to 25 public companies
- source-backed data storage
- manual thesis notes
- SEC filing ingestion
- RSS/news ingestion
- macro data ingestion later
- market data ingestion later
- portfolio holdings and transactions next
- manual prices and portfolio valuation after holdings
- credibility scoring
- change detection
- daily intelligence brief

Do not build:

- trading execution
- buy/sell recommendations
- Twitter scraping
- options flow engine
- broker credential storage
- broker sync before OAuth/token security is designed
- multi-user authentication
- payment system
- production deployment

The expanded product plan lives in `docs/archive/portfolio-expansion-plan.md`.
The repository threat model lives in `docs/06-security-threat-model.md`.

---

## Current implementation status

Use `docs/00-current-state.md` as the source of truth.

Short version:

- Built: local Docker app, FastAPI backend, Next.js frontend, PostgreSQL,
  companies, sources, raw documents, events, alerts, thesis notes, SEC/RSS
  ingestion, scoring, alert review, daily briefs, and manual portfolio tracking
  for portfolios, holdings, and transactions.
- Built (Milestones D-K): Deterministic portfolio valuation, manual prices, DCF
  models, section-aware SEC diffs, AI provenance foundations, compliant sentiment,
  narrative clustering, thesis-aware alerts, and macro/exposure metrics.
- Not built: real-time market data, broker sync, auth, or production deployment.

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

When running the backend directly on the laptop instead of inside Docker, use `localhost` in `DATABASE_URL`.

## Milestone A local verification & Manual Setup

If you are setting up API keys, running verification scripts, or configuring external sources, please refer to the detailed [Local Development Guide](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/07-local-development.md).

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

Replace the example RSS URLs with real feeds you want to track. Refer to [docs/07-local-development.md](file:///Users/mananmaheshwari/Documents/Codex/Market%20Intelligence%20App/market-intelligence-md-files%20copy/docs/07-local-development.md) for troubleshooting feed errors and other common verification issues.

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
