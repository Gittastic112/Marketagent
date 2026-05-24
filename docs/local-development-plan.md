# Local Development Plan

## Goal

Build the Market Intelligence Engine locally on your computer before deploying anything online.

Local means:

- the app runs on your laptop
- the database runs through Docker
- the dashboard opens at localhost
- no public users
- no production security burden yet

---

## Tools needed

| Tool | Purpose |
|---|---|
| VS Code | Open and edit the project |
| Git | Track changes |
| GitHub | Back up the repo and connect Codex |
| Node.js LTS | Run the frontend |
| Python 3 | Run backend and data scripts |
| Docker Desktop | Run PostgreSQL locally |
| Codex | Help create, edit, and debug the code |

---

## Local services

The local app will eventually run:

| Service | Local URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| PostgreSQL | localhost:5432 |
| pgAdmin | http://localhost:5050 |

---

## Setup order

### 1. Create project folder

```bash
mkdir market-intelligence-engine
cd market-intelligence-engine
```

### 2. Add docs and root files

Add:

```text
README.md
AGENTS.md
docker-compose.yml
.env.example
docs/
```

### 3. Initialize Git

```bash
git init
git add .
git commit -m "Initial project docs and local setup"
```

### 4. Start Docker database

Make sure Docker Desktop is open.

Then run:

```bash
docker compose up -d
```

Check containers:

```bash
docker ps
```

You should see:

```text
market_intel_postgres
market_intel_pgadmin
```

### 5. Open pgAdmin

Go to:

```text
http://localhost:5050
```

Login:

```text
Email: admin@local.com
Password: admin_password
```

Postgres connection:

```text
Host: postgres
Port: 5432
User: marketintel
Password: marketintel_password
Database: marketintel
```

### 6. Ask Codex to create docs first

Do not ask Codex to write app code immediately.

First prompt:

```text
Read the docs folder and root project files.
Create or refine product-brief.md, architecture.md, roadmap.md, scoring-framework.md, data-sources.md, database-schema.md, and codex-prompts.md.
Do not write application code yet.
Keep the MVP local and Docker-based.
```

### 7. Build backend first

After docs are ready:

```text
Create a minimal FastAPI backend connected to PostgreSQL using the DATABASE_URL from .env.
Implement Company, Source, RawDocument, Event, Alert, and ThesisNote models.
Add migrations and tests.
```

### 8. Build frontend second

After backend works:

```text
Create a simple Next.js frontend with pages for companies, documents, alerts, and daily brief.
Connect it to the FastAPI backend.
```

---

## Beginner rule

If something breaks, do not ask Codex to rebuild the whole project.

Ask:

```text
Explain this error in plain English.
Identify the smallest likely fix.
Do not rewrite unrelated files.
```
