# Product Brief: Market Intelligence Engine

## 1. Product North Star
The Market Intelligence App is a local-first, source-backed financial research and portfolio intelligence cockpit. It combines portfolio analytics, company research, SEC filings, news flow, narrative tracking, sentiment, scoring, and valuation tools into a unified, source-backed research workflow.

**Core User Question (Every screen must answer):**
> What is happening, why does it matter, how reliable is it, and what should I investigate next?

---

## 2. Core Problem & Design Principle
Markets produce too much information. The problem is knowing what changed, what matters, what is credible, and how it affects your thesis or portfolio.

**Design Principle:**
> Never add visual complexity unless it improves decision clarity.

---

## 3. Core Workflows
The application is structured around six core workflows. Some are implemented, some are partial, and all must keep source/provenance state visible:
1. **Daily Intelligence Workflow:** "What changed since I last checked?" (Dashboard, Top Movers, Filings, Risk Alerts)
2. **Portfolio Monitoring Workflow:** "What am I actually exposed to?" (Sector/Theme exposure, concentration, narrative exposure)
3. **Company Research Workflow:** "Do I understand this company better after 5 minutes?" (Filings, News, Financials, Narratives, DCF)
4. **Narrative Intelligence Workflow:** "Is this market story real, rising, fading, or priced in?"
5. **Research Workspace Workflow:** "Can I convert scattered information into a research view or memo?" (Source-backed AI chat)
6. **Valuation Workflow:** "How do my assumptions change the valuation?" (DCF modeling, scenarios, sensitivity)

---

## 4. Intelligence Hierarchy
Every major view follows a strict 4-layer hierarchy to prevent data dumping:
1. **Layer 1: Executive Summary** (What changed, why it matters, current signal, confidence)
2. **Layer 2: Key Metrics** (Top-level numbers only: price change, exposure, narrative score)
3. **Layer 3: Evidence and Sources** (Links to SEC filings, news, and the distinction between facts, calculations, and AI judgments)
4. **Layer 4: Deep Dive** (Full charts, long tables, DCF inputs, full filing texts)

---

## 5. Target User
The configured scope is personal research in US and Indian equities, with USD
portfolio reporting. Professional data licensing and public deployment are not
established by the current local setup. Potential user personas include:
- Individual investor
- Finance student
- Research analyst
- Founder/researcher building a personal research OS
- Someone tracking a concentrated watchlist of 10 to 25 companies

---

## 6. MVP Scope (Current Phase)
The current app remains local-first, but the MVP has expanded into a broader research and valuation cockpit:
- [x] Company watchlist
- [x] Manual thesis notes
- [x] Raw document storage
- [x] Basic event classification
- [x] Credibility scoring
- [x] Daily Brief with source inspection, review history and an opt-in local schedule
- [x] Private paste/PDF research inbox with explicit, review-only AI triage
- [x] Company/portfolio filing-backed business context and reviewed-peer Comps workspace
- [x] Portfolio holdings and transactions
- [x] Manual market prices
- [x] Portfolio valuation and exposure analytics
- [x] SEC filing ingestion for US companies when `SEC_USER_AGENT` is configured
- [x] RSS/news ingestion through configured RSS sources
- [x] Market-aware US/India company identity
- [x] Provider health and source capability visibility
- [x] Damodaran-style valuation engine with DCF, source-backed synthetic-rating WACC, sensitivity, scenarios, reverse DCF, FCFE/DDM, macro sensitivity, real options, and benchmark priors
- [x] Financial extraction candidate workflow from reviewed filing text
- [x] SEC XBRL `companyfacts` candidate extraction foundation
- [x] Candidate review/reject/override/promote UI foundation
- [~] Narrative tracking and research workspace: modeled and routed, but still needs UX/provenance hardening
- [~] India data support: structurally supported and manual-first; automated NSE/BSE/provider ingestion is not complete
- [~] Assumption autofill: annual SEC/FRED/benchmark inputs feed review-required drafts; company mapping, India coverage and unsupported assumptions remain incomplete

---

## 7. What the App Should NOT Become (Explicit Non-goals)
Do not build:
- A generic SaaS dashboard
- A crypto-style trading toy
- An AI chatbot with dashboards attached
- A fake Bloomberg clone
- Automated trading or buy/sell recommendations
- Portfolio execution or broker syncing (before security design is finalized)
- Social scraping tools
- A frontend that invents intelligence the backend cannot support

---

## 8. Source-Backed AI Principle
AI is an optional research aid. Stored sources and explicit review remain the
trust boundary; an exact quote does not certify the interpretation built on it.
**The Flow:** `source → storage → classification → scoring → brief/alert`
AI-generated outputs must:
- Claim reasoning with direct links to evidence (filings, news).
- Include confidence levels (Low, Medium, High).
- Separate facts from AI interpretations and user assumptions.
- Identify what would falsify the interpretation.
