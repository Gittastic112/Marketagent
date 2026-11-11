# Backend API map

58 HTTP router modules. This inventory maps source ownership; capability
status remains in the [feature register](../roadmaps/feature-register.md).

[Route registration](../../backend/app/api/routes.py) assembles the authenticated
router groups. [Application entry](../../backend/app/main.py) owns middleware and
health/readiness endpoints outside those groups. The
[security inventory](../../backend/app/api/route_security.py) and its
[tests](../../backend/tests/test_route_security_inventory.py) check exposure.

Use the owning router's schema and service imports for request/response contracts
and implementation. The [code map](../code-map.md#route-a-domain-change) connects
common changes to calculation, persistence, frontend, and test owners.

| Domain | HTTP owner |
|---|---|
| Accounting | [accounting.py](../../backend/app/api/routers/accounting.py) |
| Admin damodaran | [admin_damodaran.py](../../backend/app/api/routers/admin_damodaran.py) |
| AI | [ai.py](../../backend/app/api/routers/ai.py) |
| AI consent | [ai_consent.py](../../backend/app/api/routers/ai_consent.py) |
| AI outputs | [ai_outputs.py](../../backend/app/api/routers/ai_outputs.py) |
| AI research | [ai_research.py](../../backend/app/api/routers/ai_research.py) |
| Alerts | [alerts.py](../../backend/app/api/routers/alerts.py) |
| Assumptions | [assumptions.py](../../backend/app/api/routers/assumptions.py) |
| Benchmarks | [benchmarks.py](../../backend/app/api/routers/benchmarks.py) |
| Brief sources | [brief_sources.py](../../backend/app/api/routers/brief_sources.py) |
| Companies | [companies.py](../../backend/app/api/routers/companies.py) |
| Company research | [company_research.py](../../backend/app/api/routers/company_research.py) |
| Company setup | [company_setup.py](../../backend/app/api/routers/company_setup.py) |
| Country market | [country_market.py](../../backend/app/api/routers/country_market.py) |
| Daily brief | [daily_brief.py](../../backend/app/api/routers/daily_brief.py) |
| Daily brief schedule | [daily_brief_schedule.py](../../backend/app/api/routers/daily_brief_schedule.py) |
| Dashboard | [dashboard.py](../../backend/app/api/routers/dashboard.py) |
| Data transfer | [data_transfer.py](../../backend/app/api/routers/data_transfer.py) |
| Decisions | [decisions.py](../../backend/app/api/routers/decisions.py) |
| Evaluation | [evaluation.py](../../backend/app/api/routers/evaluation.py) |
| Events | [events.py](../../backend/app/api/routers/events.py) |
| Evidence | [evidence.py](../../backend/app/api/routers/evidence.py) |
| Evidence integrity | [evidence_integrity.py](../../backend/app/api/routers/evidence_integrity.py) |
| Exposure tags | [exposure_tags.py](../../backend/app/api/routers/exposure_tags.py) |
| Filing acquisition | [filing_acquisition.py](../../backend/app/api/routers/filing_acquisition.py) |
| Fundamentals | [fundamentals.py](../../backend/app/api/routers/fundamentals.py) |
| FX rates | [fx_rates.py](../../backend/app/api/routers/fx_rates.py) |
| Ingestion | [ingestion.py](../../backend/app/api/routers/ingestion.py) |
| Intelligence review | [intelligence_review.py](../../backend/app/api/routers/intelligence_review.py) |
| Macro | [macro.py](../../backend/app/api/routers/macro.py) |
| Macro valuation | [macro_valuation.py](../../backend/app/api/routers/macro_valuation.py) |
| Manual processing | [manual_processing.py](../../backend/app/api/routers/manual_processing.py) |
| Market | [market.py](../../backend/app/api/routers/market.py) |
| Market prices | [market_prices.py](../../backend/app/api/routers/market_prices.py) |
| Market regime | [market_regime.py](../../backend/app/api/routers/market_regime.py) |
| Narratives | [narratives.py](../../backend/app/api/routers/narratives.py) |
| OAUTH | [oauth.py](../../backend/app/api/routers/oauth.py) |
| PDF filings | [pdf_filings.py](../../backend/app/api/routers/pdf_filings.py) |
| Portfolios | [portfolios.py](../../backend/app/api/routers/portfolios.py) |
| Processing runs | [processing_runs.py](../../backend/app/api/routers/processing_runs.py) |
| Providers | [providers.py](../../backend/app/api/routers/providers.py) |
| Raw documents | [raw_documents.py](../../backend/app/api/routers/raw_documents.py) |
| Real options | [real_options.py](../../backend/app/api/routers/real_options.py) |
| Regression priors | [regression_priors.py](../../backend/app/api/routers/regression_priors.py) |
| Relative valuation | [relative_valuation.py](../../backend/app/api/routers/relative_valuation.py) |
| Research | [research.py](../../backend/app/api/routers/research.py) |
| Scoring config | [scoring_config.py](../../backend/app/api/routers/scoring_config.py) |
| Search | [search.py](../../backend/app/api/routers/search.py) |
| Social | [social.py](../../backend/app/api/routers/social.py) |
| Source capabilities | [source_capabilities.py](../../backend/app/api/routers/source_capabilities.py) |
| Source facts | [source_facts.py](../../backend/app/api/routers/source_facts.py) |
| Sources | [sources.py](../../backend/app/api/routers/sources.py) |
| Thesis evidence | [thesis_evidence.py](../../backend/app/api/routers/thesis_evidence.py) |
| Thesis notes | [thesis_notes.py](../../backend/app/api/routers/thesis_notes.py) |
| Valuation refresh | [valuation_refresh.py](../../backend/app/api/routers/valuation_refresh.py) |
| Valuations | [valuations.py](../../backend/app/api/routers/valuations.py) |
| Variant perception | [variant_perception.py](../../backend/app/api/routers/variant_perception.py) |
| WACC | [wacc.py](../../backend/app/api/routers/wacc.py) |

The documentation checker verifies every module and the count against source.
Update this inventory when adding or removing a router module. Preserve the
[shared API boundaries](../code-map.md#api-boundaries-to-preserve).
