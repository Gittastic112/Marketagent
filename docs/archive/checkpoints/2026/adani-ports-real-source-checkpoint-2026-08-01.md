# Adani Ports Real-Source Checkpoint

**Date:** 2026-08-01  
**Valuation cutoff:** 2026-08-02, Asia/Kolkata  
**Status:** FY2023-FY2025 promoted, normalized, reconciled, and certified

## Company Identity

| Field | Value |
|---|---|
| Local company ID | `6` |
| Legal name | Adani Ports and Special Economic Zone Limited |
| NSE symbol | `ADANIPORTS` |
| Primary exchange | NSE |
| ISIN | `INE742F01042` |
| Market / currency | India / INR |

The identity is verified against the official NSE quote and filing records.
The source profile classification is `Transport Infrastructure`; this is a
company classification, not an approved Damodaran benchmark mapping.
The setup workflow is `identity_status=reviewed`, `source_status=manual_only`,
`filing_status=complete`, `financial_extraction_status=reviewed`, and remains in
valuation review until the user reviews the actual valuation assumptions.

## Primary Sources

| Source | Local document | SHA-256 | Targeted PDF pages |
|---|---:|---|---|
| [NSE FY2024-25 annual report](https://nsearchives.nseindia.com/annual_reports/AR_26467_ADANIPORTS_2024_2025_A_30052025204446.pdf) | `3` | `2ec4e75290acf3845677ab4a2efd64869d5c9ea5c472a3f0421d9d1611527262` | 465, 466, 542 |
| [NSE FY2023-24 annual-report filing](https://nsearchives.nseindia.com/corporate/ADANIPORTS_28052024214257_IntimationofAnnualReport.pdf) | `4` | `7f4ff812ea46d1d1c091e58f2161719285fee9ad39ea5e29c3b4beca13aea03f` | 438, 439, 514 |
| [Official APSEZ investor page](https://www.adaniports.com/investors) for the supplied Q1 FY27 presentation | `5` | `f02e198abf211727c24adeea41b9b861dd6ff0afbb5d96664a1271dcad2edafd` | Stored in full; not certification evidence |

The latest statutory quarter source is the [revised unaudited consolidated NSE
iXBRL for 30 June 2026](https://nsearchives.nseindia.com/corporate/ixbrl/INTEGRATED_FILING_INDAS_180165_29072026202624_iXBRL_WEB.html), broadcast on
29 July 2026. The supplied Q1 PDF is an official media release and investor
presentation. It is a **Source Summary**, not a statutory financial statement.

## Staged Annual Facts

The parser retained FY2024 and FY2025 from the latest FY2024-25 report and
FY2023 from the FY2023-24 comparative. This avoids duplicate FY2024 review
candidates from two reports.

All 48 candidates were explicitly approved and promoted. Three additional
operating-EBIT `Calculation` candidates were added after line-item reconstruction.

The following are promoted audited facts in INR crore:

| FY | Revenue | Consolidated profit | Parent profit | Cash | Debt | NCI balance | Associates / JV investments | Diluted shares |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 20,851.91 | 5,390.85 | 5,308.85 | 1,121.11 | 50,518.43 | 1,361.06 | 2,498.38 | 2,160,138,945 |
| 2024 | 26,710.56 | 8,103.99 | 8,110.64 | 1,575.73 | 46,279.23 | 1,598.23 | 2,707.26 | 2,160,138,945 |
| 2025 | 30,475.33 | 11,061.26 | 11,092.31 | 3,406.32 | 45,810.03 | 2,537.95 | 3,082.64 | 2,160,138,945 |

Debt is a **Calculation** from reported financing components:

```text
FY2025: 35,830.68 non-current borrowings + 9,979.35 current borrowings = 45,810.03
FY2024: 37,662.93 non-current borrowings + 8,616.30 current borrowings = 46,279.23
FY2023: 46,516.94 non-current borrowings + 3,302.37 current borrowings
        + 699.12 customers' bills discounted = 50,518.43
```

Lease liabilities are stored separately and are not silently folded into debt:
FY2023 `2,749.26`, FY2024 `3,024.48`, FY2025 `5,644.17` INR crore.

Each year also has source-backed candidates for book equity, total assets,
depreciation and amortization, interest and bank charges, pre-tax income, tax
expense, parent/NCI profit attribution, and investments accounted for using the
equity method.

## Operating EBIT Calculation

APSEZ's consolidated statement does not report a clean operating EBIT line.
The reviewed method therefore reconstructs EBIT from the audited statement:

```text
Operating EBIT = Revenue from operations
               - Operating expenses
               - Employee benefits expense
               - Depreciation and amortisation expense
               - Other expenses
```

| FY | Formula, INR crore | EBIT |
|---:|---|---:|
| 2023 | 20,851.91 - 5,654.56 - 1,178.17 - 3,424.71 - 1,185.73 | 9,408.74 |
| 2024 | 26,710.56 - 7,116.34 - 1,896.40 - 3,888.46 - 1,833.90 | 11,975.46 |
| 2025 | 30,475.33 - 8,069.75 - 2,008.66 - 4,378.93 - 1,975.55 | 14,042.44 |

The formula excludes other income, finance costs and finance-related gains or
losses, equity-accounted associate/JV results, exceptional items, and the FY2025
stake-sale gain. Each candidate stores the five components, formula, exclusions,
PDF page, March 31 period end, and `claim_type=Calculation`.

## Q1 FY27 Boundary

The revised NSE iXBRL reports consolidated revenue of `1,082,080` INR lakh and
total profit of `364,950` INR lakh for the quarter. The presentation rounds these
to revenue `10,821` crore and PAT `3,650` crore and separately reports EBITDA of
`6,541` crore. These are current-quarter context only. They were not inserted as
annual candidates and cannot satisfy the three-year history gate.

## Valuation Draft

Valuation setup draft `2` stores:

```text
valuation_cutoff_date: 2026-08-02
valuation_cutoff_timezone: Asia/Kolkata
financial_history_status: complete
financial_history_certification_status: passed
latest_statutory_financial_source: revised Q1 FY27 consolidated NSE iXBRL
```

No market price or valuation output has been fabricated. The draft remains a
review object because valuation assumptions and market price still require
explicit user review.

## Industry Mapping Guard

Validation found that the former suggestion fallback could select the first
alphabetical benchmark when no profile match existed. That had incorrectly put
`Advertising` on APSEZ and refreshed draft `2` without preserving its cutoff
metadata. The invalid, unreviewed mapping was cleared.

The repaired mapper now:

- requires candidates to share a meaningful company-profile token
- validates confirmations against the loaded country taxonomy
- reports actual per-module benchmark availability instead of hardcoded `true`
- updates the setup workflow when a mapping is explicitly confirmed
- exposes the full loaded taxonomy for manual selection when no reliable match exists
- preserves attached cutoff and statutory-source metadata on draft update/refresh

The valuation page now supports a persisted revenue-weighted segment mix. The
existing approved `Packaging & Container` selection was migrated to a 100%
`Core operations` user-assumption row. This preserves the user's choice but does
not claim it is the correct whole-company classification. Replace it with actual
segment weights when available. Blended priors are estimates, weights must total
100%, and missing component benchmarks are never silently renormalized.

## Validation

```text
backend: 391 passed, 4 upstream openpyxl deprecation warnings
frontend: 75 passed
TypeScript: passed
Next.js webpack production build: passed
```

The live verification reports AAPL eligible with 24 reviewed exact facts and
APSEZ eligible with 51 reviewed exact facts/calculations. APSEZ has three
trust-ready periods and 27/27 exact canonical reconciliation checks. The
two-market report passes with `certified_count=2` and markets `IN` and `US`.
All seven AAPL FY2021 candidates remain `needs_review`.

The live on-demand Data Health audit checks 75 promoted financial facts and
seven annual periods, reports two eligible histories, markets `IN` and `US`,
`financial_certification_status=passed`, and no financial integrity issue.
The guarded metadata repair set annual-report assets `3` and `4` to 673 and 609
physical pages respectively; an immediate repeat made zero corrections.

## Review Sequence

1. Open `http://localhost:3000/companies/6/valuation`.
2. Replace the preserved 100% row with reviewed revenue segment weights.
3. Link the mix to an official company-owned source document when the segment
   basis is available.
4. Review the resulting blended benchmark priors as estimates.
5. Keep the certification harness green when changing extraction or normalization.

## Reproducible Staging Command

Run from the repository root after making the PDFs available inside the backend
container:

```bash
docker compose exec backend python /workspace/backend/scripts/stage_adani_reference_data.py \
  --fy25-pdf /tmp/adani-fy25.pdf \
  --fy24-pdf /tmp/adani-fy24.pdf \
  --q1-fy27-pdf /tmp/adani-q1-fy27.pdf \
  --valuation-cutoff-date 2026-08-01 \
  --apply
```

The command verifies all three SHA-256 hashes, refuses to promote candidates,
is idempotent for already stored source documents, clears the known unreviewed
alphabetical-fallback artifact, and restores the valuation cutoff metadata.

After explicit approval, finalize with:

```bash
docker compose exec backend python /workspace/backend/scripts/finalize_adani_reference_data.py \
  --valuation-cutoff-date 2026-08-02 \
  --apply
```

This command is idempotent and fails closed on source, value, unit, evidence,
or promotion-scope drift. It also verifies the original PDF physical page count
and repairs the legacy targeted-scan metadata bug without changing source bytes.
