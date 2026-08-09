# Agent Capabilities and Limitations

**Audited:** 2026-08-08

This document is the practical trust boundary for the product. It intentionally
summarizes capabilities instead of duplicating route-by-route implementation.

## What the Product Can Do

| Capability | State | Evidence boundary |
|---|---|---|
| Track companies and market identity | Built | Company ownership, setup workflow, aliases, source capabilities |
| Store and inspect source documents | Built | Raw documents, sections, PDF assets, exact locators where available |
| Ingest SEC filings and RSS | Built when configured | Manual triggering and provider constraints remain |
| Upload India filing PDFs | Built | Automated NSE/BSE discovery is incomplete |
| Extract and review financial candidates | Built | Review is required before promotion |
| Normalize and reconcile financial histories | Built for covered metrics | Broad issuer/layout certification remains incomplete |
| Extract events and deterministic scores | Built | Rule-based extraction can miss nuance |
| Review alerts and thesis impact | Built | Historical evidence precision varies |
| Track portfolios, transactions, cash, and prices | Built | No broker sync; provider freshness varies |
| Run multi-stage valuation workflows | Built | Output quality depends on reviewed assumptions and source definitions |
| Use Damodaran benchmark priors | Built for 14 typed sources | 21 mirrored sources remain partial or unsupported |
| Run research sessions and AI assistance | Partial | Exact-source review and approval gates exist; generated claims are not automatically factual |
| Search stored evidence | Partial | Coverage is strongest for documents and events, not every domain |
| Generate a daily brief | Built but not autonomous | Continuous scheduling and complete provider coverage are absent |

## What Still Requires the User

- Choose and verify companies, market identity, and reporting currency.
- Supply or approve source documents and provider keys.
- Review extracted financial candidates and reconciliation results.
- Confirm weighted industry mappings.
- Review valuation model choice, assumptions, and source age.
- Interpret thesis impact and approve AI-assisted output.
- Enter or validate prices when provider data is missing or stale.
- Decide whether a source is acceptable for personal/internal use.

## What Is Not Product-Ready

| Gap | Consequence |
|---|---|
| Public deployment security | Keep the app on localhost |
| Production India provider coverage | India workflows remain manual/partial |
| Broker integration | Portfolio activity must be entered/imported manually |
| Real-time data | Do not infer trading-grade freshness |
| Automated market-regime feeds | Manual/provider input workflow exists, but automated module coverage is not configured |
| Fully automatic statements | Review and normalization are still required |
| Fully cited AI research | AI remains assistive and review-only |
| Complete frontend parity | Some pages still need source/data-state auditing |
| Portfolio comparison | Performance attribution exists; marginal-risk and expected-return comparisons remain incomplete |

## Reliability Baseline

- 483 backend tests and 90 frontend tests passed at the latest full baseline.
- TypeScript and the Next.js production build passed.
- Exact evidence, ownership, response contracts, valuation math, migrations,
  Damodaran versioning, and representative source workflows have targeted tests.
- Browser coverage exists for selected workflows, not every active route.
- A passing build does not prove live providers, credentials, or source freshness.

## AI Boundary

AI may summarize, propose, compare, and draft. It must not silently create trusted
facts, overwrite reviewed assumptions, or issue buy/sell recommendations. Store
provider/model, prompt version, source links, generation time, limitations,
confidence, and review status. Private portfolio or thesis data must not leave
the local boundary without an explicit feature and disclosure.

## Valuation Boundary

The deterministic engines are serious, but a mathematically correct model can
still be economically wrong. Review starting financials, accounting adjustments,
growth, margins, reinvestment, WACC, terminal assumptions, equity bridge,
currency, diluted shares, and source comparability. Industry data is a prior,
not a company fact.

## Data Boundary

- AAPL FY2022-FY2025 and APSEZ FY2023-FY2025 are reviewed, reconciled,
  real-source histories. The representative US/India certification gate passes.
- Manual prices and explicit personal-use Yahoo data must remain labeled.
- Damodaran generic workbook inventory is not the same as typed application support.
- Historical source rows without provable versions remain excluded from active reads.

## Security Boundary

Local credential authentication and owner scoping reduce accidental cross-user
access, but they do not make the application safe for the public internet. Public
deployment requires production identity, authorization review, HTTPS, CSRF and
CORS hardening, rate limits, secret management, backups, privacy controls, and
audit logging.

## Highest-Value Improvements

1. Finish frontend/backend data-state parity.
2. Expand real-issuer coverage beyond AAPL/APSEZ and improve official India providers.
3. Turn separate modules into one daily evidence-to-decision workflow.
4. Add marginal-risk and expected-return portfolio comparisons.
5. Add compliant automated market-regime sources without hiding provenance.
6. Improve automatic exact-passage selection while retaining review gates.

The former 2,450-line audit is preserved at
[`archive/assessments/agent_capabilities_and_limitations.md`](archive/assessments/agent_capabilities_and_limitations.md).
