# M05 financial evidence checkpoint

October 11, 2026. M05 is in progress; no company was approved or certified.

The fixed [source checklist](../../../../data/certification/scoped-source-checklist.json)
records three target annual periods, official issuer/SEC entry points and required
statement, unit, borrowing, share-class and bank-equity reviews for all 11 securities.
The historical AAPL/APSEZ reference manifest remains unchanged. Its original
source assets are needed to reproduce those older certifications.

The read-only inventory uses six scalar database queries and does not load PDF
bytes or full SEC payloads, fetch providers, promote candidates or change models.
Normal-database evidence is retained in
`output/milestones/m05/financial-coverage.json` (October 11, 19:29 UTC).

| Security | Stored annual candidate years | Candidates awaiting review | Normalized snapshots | Model review |
|---|---|---:|---:|---|
| NVDA | 2022-2026 | 117 | 0 | Operating company; split/share and borrowing scope |
| AAPL | 2021-2025 | 123 | 0 | Operating company; debt and diluted shares |
| GOOG | 2021-2025 | 103 | 0 | Alphabet issuer versus Class C security |
| MSFT | 2022-2026 | 106 | 0 | Operating company; debt and leases |
| AMZN | 2021-2025 | 115 | 0 | Operating company; financed assets and leases |
| RELIANCE | None | 0 | 0 | Consolidated statements, segments and minority interests |
| HDFCBANK | None | 0 | 0 | Bank equity/capital and merger comparability |
| BHARTIARTL | None | 0 | 0 | Spectrum/leases, Africa and partly paid shares |
| ICICIBANK | None | 0 | 0 | Bank equity/capital; NSE shares versus ADR units |
| SBIN | None | 0 | 0 | Bank equity/capital; standalone/consolidated basis |
| GOOGL | 2021-2025 | 103 | 0 | Alphabet issuer versus Class A security |

All 667 candidates remain unreviewed. None of the 11 has a stored weighted
industry mapping. Existing AAPL/NVDA documents explicitly titled **Mock Data**
remain in the inventory and do not establish genuine financial coverage.
The JSON matrix lists metric, unit, period, review and source-document gaps.

Certification v3 rejects missing units, cross-company references, XBRL values
with the wrong unit/annual period, changed retained payloads, and PDF references
with absent/out-of-range pages, malformed/out-of-bounds boxes or changed bytes.
Hash work is reused only within one read/report. Historical reports are not
rewritten. This verifies retained identity and locator structure, not independent
numeric transcription, completeness or financial interpretation.

Validation: seven new negative cases first reproduced the certification bug.
After the fix, 52 focused tests passed across certification, inventory, PDF
extraction, evidence integrity and SEC extraction. A real parser fixture (labeled
**Mock Data**) retains all 12 valid locators; six-query/no-write inventory checks
pass. This is not new genuine issuer/layout parser certification.

M05-01 and M05-07 are evidenced. Review, reconciliation, additional independently
reviewed layouts and the full genuine-input browser path remain open. See the
[single limitation ledger](../../../agent_capabilities_and_limitations.md).
