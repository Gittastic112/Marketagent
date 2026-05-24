# Market Intelligence Engine

## What this project is

This project is a local-first Market Intelligence Engine for public equity research.

It is not a trading bot.  
It is not a generic AI summarizer.  
It is not a Bloomberg clone.

It is a source-backed research system that helps track:

- companies
- filings
- news
- macro data
- market data
- thesis notes
- catalysts
- narrative shifts
- alerts

The goal is to answer:

> What changed, why does it matter, how credible is it, and does it affect my thesis?

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
- credibility scoring
- change detection
- daily intelligence brief

Do not build:

- trading execution
- buy/sell recommendations
- Twitter scraping
- options flow engine
- multi-user authentication
- payment system
- production deployment

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
The frontend container talks to the backend through the Docker service name `backend`.

When running the backend directly on the laptop instead of inside Docker, use `localhost` in `DATABASE_URL`.

---

## Folder structure

```text
market-intelligence-engine/
├── README.md
├── AGENTS.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── product-brief.md
│   ├── local-development-plan.md
│   ├── architecture.md
│   ├── roadmap.md
│   ├── scoring-framework.md
│   ├── data-sources.md
│   ├── database-schema.md
│   ├── codex-prompts.md
│   └── beginner-glossary.md
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
