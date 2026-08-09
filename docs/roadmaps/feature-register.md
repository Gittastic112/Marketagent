# Feature Register

**Updated:** 2026-08-09

Status meanings:

- **Built:** real persisted behavior with meaningful tests.
- **Partial:** useful foundation exists, but coverage or workflow is incomplete.
- **Prototype:** visible behavior is mocked, simulated, or not decision-ready.
- **Not built:** no usable end-to-end implementation.

| Product area | Status | Current boundary |
|---|---|---|
| Local sign-in and owner scoping | Built | Localhost only; not production identity |
| Company CRUD and setup workflow | Built | India lookup/source automation partial |
| SEC filing ingestion | Built | Requires SEC identity/configuration and manual triggering |
| RSS ingestion | Built | Feed quality and scheduling remain limited |
| Official India PDF upload | Built | Automated NSE/BSE picker partial/not complete |
| Financial extraction candidates | Built | Layout coverage incomplete; review required |
| Financial normalization/reconciliation | Built | AAPL and APSEZ are certified; broader issuer/layout coverage partial |
| Exact PDF/text evidence | Built | Historical records can have coarse fallback |
| Events, scoring, and alerts | Built | Extraction remains primarily rule-based |
| Thesis notes and evidence ledger | Built | Contradiction workflow partial |
| Daily brief | Partial | Not a continuous autonomous daily process |
| Stored evidence search | Partial | Not unified across every research object |
| Portfolios, holdings, cash, transactions | Built | No broker sync |
| Manual and provider-backed prices | Partial | Provider breadth/freshness incomplete |
| Portfolio valuation and exposure | Built | Exposure and recorded activity by currency are real; period attribution, historical FX impact, and benchmark opportunity cost remain incomplete and explicitly unavailable |
| FCFF DCF and scenarios | Built | Assumption review remains mandatory |
| Reverse DCF and diagnostics | Built | Depends on reviewed market and financial inputs |
| FCFE/DDM | Built | Model suitability must be reviewed |
| Relative valuation | Built | Industry aggregates, not a reviewed peer set |
| WACC and synthetic ratings | Built | Operating-lease capitalization remains incomplete |
| Assumption methodology selection | Partial | Provenance exists; hardcoded India fallback values remain technical debt |
| Real options | Built | Industry volatility is a prior, not company fact |
| Macro sensitivity | Partial | Provider and company exposure coverage uneven |
| Weighted industry mapping | Built | User confirmation required |
| Damodaran source versioning | Built | 14 of 35 mirrors have typed rows |
| Data Health | Partial | Active provider checks need expansion |
| AI memo and narrative assistance | Partial | Review-only; citation generation incomplete |
| Research sessions | Built | Not yet a unified research workflow |
| Market regime | Prototype | Mock/simulated values are not trusted |
| Broker sync | Not built | Security design required first |
| Public deployment | Not built | Security and operations gates unmet |
| Documentation architecture | Built | One current source per concern, categorized archive, automated link/path gate |

## Next Status Changes Expected

1. India provider and issuer coverage expands beyond the certified APSEZ case.
2. Daily brief moves from a module to an integrated daily workflow.
3. Portfolio analytics gains attribution.
4. Market regime is either hidden or rebuilt as source-backed behavior.

Update this file when code changes a status. Put implementation proof in tests
and a dated archived checkpoint, not in additional columns here.
