# SpaceX Source Conflicts and Contamination

## Target-revenue conflict
The post-prospectus article table on page 9 shows approximately:
- Launch/Space target revenue: $70B
- Connectivity: $120B
- AI: $160B
- Expansion: $50B

The accompanying `SpaceX2026IPOUpdated.xlsx` input sheet instead uses:
- Launch: $40B
- Starlink: $120B
- xAI: $160B
- Other: $100B

The spreadsheet's actual valuation output follows its spreadsheet inputs, so use those values when reproducing the workbook, but keep the article values as a source conflict. Do not silently reconcile them.

## Stale template contamination
The workbook contains stale template indicators, including:
- valuation date cell corresponding to an old date rather than the 2026 case
- a `TeslaValue`/Tesla-related sheet or references
- stale Tesla story text in reused template areas

Treat those items as `STALE_TEMPLATE`, not SpaceX evidence.
