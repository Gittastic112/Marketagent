# Local Development & Manual Setup Guide

This guide contains everything you need to run the Market Intelligence Engine locally via Docker, configure environments, verify its health, and debug issues.

Since this is a local-first application, you have full control over the environment variables and API integrations.

---

## 1. Environment Configuration (`.env`)

Before starting the app, you must configure your `.env` file in the project root. **Never commit this file.** A template is provided in `.env.example`.

### Required Settings

| Key | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string. | `postgresql+psycopg://marketintel:marketintel_password@postgres:5432/marketintel` |
| `SEC_USER_AGENT` | **CRITICAL**: The SEC EDGAR API requires a declared contact header. General or empty user agents are blocked. | `"MarketIntelligenceApp/0.1 contact: your-email@example.com"` |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend API URL. | `http://localhost:8000` |

### Third-Party API Keys (For later expansions)

Add these keys to your `.env` file to enable live external data imports and AI capabilities in the future:
```text
NEWS_API_KEY=
ALPHA_VANTAGE_API_KEY=
FRED_API_KEY=
GEMINI_API_KEY=
```
*(Note: If AI keys are not set, the app will gracefully fall back to a deterministic Mock AI Provider for local testing).*

> [!IMPORTANT]
> **After updating your `.env` file, you must restart your Docker containers** to load the new settings:
> `docker compose down && docker compose up -d`

---

## 2. Running Docker (The Whole Stack)

Ensure Docker Desktop is open and running.

**Start all services** (Frontend, Backend, PostgreSQL, pgAdmin) in the background:
```bash
docker compose up -d
```

**Rebuild after making code or dependency changes:**
```bash
docker compose up --build -d
```

**Completely reset the environment** (Warning: Deletes the database volume):
```bash
docker compose down -v
```

---

## 3. Database Setup & Migrations

The backend container is configured to automatically run migrations (`alembic upgrade head`) when it starts.

If you need to generate a new migration after modifying `app/models/`:
```bash
docker compose exec backend alembic revision --autogenerate -m "Add new table"
```
*(Note: Always review the generated python file in `backend/alembic/versions` before applying it).*

You can verify the database state by opening **pgAdmin** in your browser at `http://localhost:5050` and logging in with:
- **Email**: `admin@local.com`
- **Password**: `admin_password`

---

## 4. How to Inspect Logs

To view logs for all services in real-time:
```bash
docker compose logs -f
```

To view logs for a specific service (e.g., the backend):
```bash
docker compose logs -f backend
```

---

## 5. Verifying API Health & Connectivity

**1. Check Backend Container Health:**
Open your browser to: `http://localhost:8000/api/health`
You should see: `{"status": "ok", "timestamp": "..."}`

**2. Verify Frontend/Backend Connection:**
If the frontend UI at `http://localhost:3000` shows "Backend not reachable", check that `http://localhost:8000` is accessible from your host machine, and ensure CORS is properly configured in `backend/app/main.py`.

---

## 6. Testing Workflows via CLI

We provide a Python script to seed the database and test live connectivity:

Run the seed script inside the backend container:
```bash
docker compose exec backend python scripts/verify_milestone_a.py --write --rss-feed "https://example.com/feed.xml"
```

**Common CLI Failure Points:**
1. **"Backend health check failed"**: Backend is down. Run `docker compose ps`.
2. **"SEC company lookup failed (403)"**: Missing or invalid `SEC_USER_AGENT` in `.env`.
3. **"RSS feed returned errors"**: URL blocked or DNS issues in Docker. Restart Docker.

---

## Beginner Rule
If something breaks:
1. Check the Docker logs first (`docker compose logs backend`).
2. Do not run destructive migration commands (like `alembic stamp`) unless you understand the error.
3. Ask the AI: "Explain this error in plain English and identify the smallest likely fix."
