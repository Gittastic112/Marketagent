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
Where all your companies, documents, events, and portfolio data are permanently stored.

### Migration (Alembic)
A version-control file for the database. When we want to add a new table (like "narratives"), Alembic creates a "migration" script to safely update the database schema without losing old data.

---

## Infrastructure

### Docker
A tool that runs software in isolated boxes (Containers). It ensures the app runs exactly the same way on your Mac as it does on a server.

### Docker Compose
A tool that lets you start the whole system (Frontend, Backend, Database) with a single command: `docker compose up`.

### Container
A running instance of a Docker image. Think of it as a mini virtual machine dedicated to running just one part of the app.

### Environment Variable (.env)
A secret setting stored outside the code. We use this for passwords, database URLs, and API keys so they don't accidentally get shared online.

### CORS (Cross-Origin Resource Sharing)
A security feature in web browsers. It dictates whether the Frontend (running on port 3000) is allowed to ask the Backend (running on port 8000) for data.

---

## Data & Ingestion

### Ingestion
The process of the app automatically downloading external data (like news or filings) and saving it into the database.

### Processing Run
A record in the database that tracks an ingestion job. It logs when the job started, how many items it found, and if it threw any errors.

### SEC User-Agent
The SEC requires anyone downloading their data to politely identify themselves. The `SEC_USER_AGENT` environment variable tells the SEC who is making the request (e.g., your email).

### CIK (Central Index Key)
A unique 10-digit number the SEC uses to identify companies. Tickers (like AAPL) can change, but CIKs are permanent.

### Mock Data
Fake data used by developers to design the Frontend before the Backend is actually built. The app must strictly label mock data so users don't mistake it for real intelligence.

### Stale Data
Data that hasn't been successfully updated recently. If the app fails to download today's news, yesterday's news is considered "stale" and must be flagged with a warning.

---

## Intelligence & Finance

### Source-backed AI
An AI rule: The AI is not allowed to invent answers. Every claim the AI makes must link directly back to a raw document (like a filing or news article) stored in the database.

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
