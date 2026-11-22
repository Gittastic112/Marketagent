# Valuation and assumption methods

For an issuer valuation, start with a dated financial revision, review the draft's remaining inputs, preview the calculation and confirm the version with a reason. The research date controls financial revision and benchmark eligibility. Other inputs retain their own dates. [User walkthrough](../user-guide.md#review-a-filing-and-valuation) · [First-valuation implementation](../../backend/app/services/first_valuation.py)

## Calculation owners

| Question | Where to look |
|---|---|
| How are cash flow, WACC, terminal value, the equity bridge, projections and sensitivity calculated? | [DCF engine](../../backend/app/services/dcf.py) · [Valuation owners and tests](../code-map.md#valuation-and-assumptions) |
| Which other models are available? | [Reverse DCF](../../backend/app/services/reverse_dcf_service.py) solves against a supported saved basis subject to convergence. [FCFE and dividend discounts](../../backend/app/services/fcfe_ddm_engine.py) use explicit, single-stage inputs. The [feature register](../roadmaps/feature-register.md) covers sector-specific models, synthetic ratings, macro sensitivity and experimental options. |
| How are relative prices compared? | [Relative valuation](../../backend/app/services/relative_valuation.py) uses reviewed benchmark or peer inputs. A saved DCF comparison retains net income, book equity, revenue, margin, currency and scale. Missing EBITDA stays unavailable. Applying a reviewed peer input requires the exact preview and its source basis. [Peer review limits](../limitations.md#relative-valuation-and-peer-review) |
| What happens on save or retry? | The [first-model review](../../frontend/components/valuation/first-model-review.tsx) previews before confirmation. Subsequent edits use [saved assumption versions](../../backend/app/services/assumption_versions.py). Each version retains its calculation basis, source selections and decision history. |

Draft and saved-model forms accept decimal rates where specified. Historical invalid units remain visible and block calculation and sensitivity until corrected. Missing comparison prices require acknowledgement in the draft, and a supplied price must be positive. Quality diagnostics and any estimate remain attached to their basis. The option panel checks saved FCFF currency, equity and shares. Legacy custom-base option calculations retain their compatibility status. [Valuation boundaries](../limitations.md#valuation-boundary)

## Assumption methods

The engine stores the chosen method, applied value, source, confidence, review state and notes. It supports risk-free rates, equity risk premiums, beta, cost of debt, tax, margin, sales-to-capital, terminal growth and return on capital. Reviewed company facts take precedence over applicable benchmark estimates. A custom assumption remains available. [Method service](../../backend/app/services/assumption_methodology.py) · [Provenance model](../../backend/app/models/assumption_methodology.py)

| Endpoint under `/api/assumptions` | Purpose |
|---|---|
| `GET /methods/{assumption_key}` | Inspect available methods for a country, with optional industry and currency. |
| `GET /country/{country}` | Get the country's available assumptions with the same optional filters. |
| `POST /valuations/{valuation_id}/select-method` | Record a reviewed selection or a custom override for an owned valuation. |

The mounted controls are [draft review](../../frontend/components/valuation/autofill-draft-review.tsx) and the [saved workspace](../../frontend/components/advanced-workspace.tsx). The standalone method selector was retired. Draft creation can acknowledge eligible current defaults together. [Assumptions API](../../backend/app/api/routers/assumptions.py)

### Source and publication basis

An unseeded service offers the custom method and has no source-backed default. Versioned January 2026 India and US workbooks supply benchmark priors. A sourced value retains its dataset ID, hash, date, path, sheet, row and column. The India WACC workbook's D10/D11 cells contain global weighted averages. Preserve that label.

The versioned importer handles `betaIndia.xls`, `waccIndia.xls`, `taxrateIndia.xls` and `countrytaxrates.xls`. The US intake loads six dated contracts covering beta/WACC, margins, reinvestment, ROE and working capital. Missing cells stay missing. A stored FRED DGS10 observation can supply a dated USD risk-free proxy. Eligibility for the research date requires publication evidence for the dataset version. [Data sources](../data-sources.md) · [US benchmark intake](../operations.md#us-benchmark-intake) · [Outstanding disclosures](../limitations.md#selected-company-review-follow-up)

### Industry mixes and review

Aggregation version 2 applies revenue weights to margins, net capital expenditure/sales and working capital/sales. Blended sales-to-capital is `1 / sum(revenue_weight / component_sales_to_capital)`. Every component must be present and finite, and capital ratios must be positive. The calculation normalizes accepted rounding differences to the actual total. A missing component withholds the field.

Revenue weights alone cannot establish capital weights, equity weights or matching growth periods. Multi-industry ROE, ROC, beta, WACC, financing ratios and multi-year growth require an appropriate basis. Absolute financing totals are excluded. Segments mapped to one industry retain that industry's own prior. The aggregation version participates in the draft source signature. A refresh preserves explicit manual edits.

The DCF tax default uses reviewed company effective tax when available, then the country marginal rate. Industry effective tax is an inspectable alternative. Bridge, share-count, payout, price and special-case fields need their own evidence or reviewed assumption. The [decision register](../roadmaps/review-decisions.md) records historical mix choices, including the October 22 provisional mixes and withheld Reliance allocation. The [financial ledger](../limitations.md#selected-company-review-follow-up) records the current four-company scope.

Valuation doctrine and source materials live in the [knowledge base](../../damodaran_knowledge_base_v1/INDEX.md). Prior specifications and six source-batch plans remain in the [valuation plan archive](../archive/plans/valuation-agent/).
