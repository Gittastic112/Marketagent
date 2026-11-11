# Beginner Glossary

This glossary explains the technical and financial terms used in the Market Intelligence App, especially for non-technical users.

## Core Architecture

### Frontend
The part of the app you see in your web browser (built with Next.js). It displays dashboards, buttons, and charts.

### Backend
The hidden "brain" of the app (built with Python FastAPI). It processes data, scores events, and talks to the database.

### API (Application Programming Interface)
The bridge that allows the Frontend to talk to the Backend, or the Backend to talk to external services (like the SEC).

### Endpoint
A specific URL in the API that does one specific job. For example, the `GET /api/health` endpoint checks if the server is running.

### Database (PostgreSQL)
Where application records and uploaded filing/research PDF bytes are persisted.
Runtime benchmark mirrors and the separate knowledge corpus live on disk. Neither
storage location guarantees recovery without verified backups.

### Migration (Alembic)
A versioned database change script. Generated migrations require review and
testing; Alembic does not guarantee safety or prevent data loss.

---

## Infrastructure

### Docker
A tool that packages software into containers. It improves reproducibility;
host architecture, configuration, networking and stored data can still differ.

### Docker Compose
A tool that lets you start the whole system (Frontend, Backend, Database) with a single command: `docker compose up`.

### Container
A running instance of a Docker image. Think of it as a mini virtual machine dedicated to running just one part of the app.

### Environment Variable (.env)
A process setting, sometimes loaded from a local .env file. Some values are
secrets, others are ordinary configuration. Keep credential values out of commits.

### CORS (Cross-Origin Resource Sharing)
A browser rule for requests between different origins. Normal app requests use
the same-origin frontend proxy; backend CORS settings are not authentication or
a substitute for the app's signed identity and ownership checks.

---

## Data & Ingestion

### Ingestion
Bringing provider data or user-supplied files/text into audited storage. It may
be explicit or scheduled; ingestion does not mean the contents have been reviewed.

### Processing Run
A record in the database that tracks an ingestion job. It logs when the job started, how many items it found, and if it threw any errors.

### SEC User-Agent
The SEC requires anyone downloading their data to politely identify themselves. The `SEC_USER_AGENT` environment variable tells the SEC who is making the request (e.g., your email).

### CIK (Central Index Key)
A unique 10-digit number the SEC uses to identify companies. Tickers (like AAPL) can change, but CIKs are permanent.

### Mock Data
Synthetic data for isolated tests or explicitly enabled demonstrations. It is
useful even after the backend is built, but must never be confused with real sources.

### Stale Data
Stored data older than its freshness threshold. A failed fetch is separately
unavailable; it does not prove the age or validity of earlier stored data.

---

## Intelligence & Finance

### Source-backed AI
AI output linked to stored evidence and subject to review. Exact citation checks
can verify a text span exists, but do not prove the claim follows from that text.

### Scoring Model
The math used to rank if a piece of news actually matters. We use scores for Credibility, Impact, and Novelty to filter out noise.

### Narrative Tracking
Grouping isolated news events into a broader market "story" (e.g., "AI Capex Cycle"). The app tracks if a narrative is gaining or losing momentum.

### DCF (Discounted Cash Flow)
A valuation method that estimates the value of an investment based on its expected future cash flows.

### Sensitivity Table
A grid used in DCF valuation that shows how changing your assumptions (like growth rate or discount rate) changes the final estimated stock price.

### Portfolio
A named group of holdings, cash, and transactions (e.g., "Personal Portfolio").

### Holding
A position currently owned in a portfolio (e.g., 10 shares of AAPL).

### Transaction
A historical portfolio action (buy, sell, dividend, fee).

### Cost Basis
What you paid for a holding, including price and fees.

### Market Value
What the holding is worth using the latest available price.

### Unrealized P&L
Profit or loss on a holding that has not been sold yet.

### Portfolio Weight
How much of the portfolio a single holding represents (e.g., 18%).

### Exposure
What the portfolio is sensitive to (e.g., sector exposure, country exposure, interest rate exposure).
