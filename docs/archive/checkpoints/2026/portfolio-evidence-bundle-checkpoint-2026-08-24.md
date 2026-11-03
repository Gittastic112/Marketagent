# Portfolio Evidence Bundle Checkpoint

**Date:** 2026-08-24

**Boundary:** 100 commit-sized increments that make genuine historical market
price and FX entry practical for the pending real-input portfolio smoke. This
does not certify a portfolio or supply any investment data.

## Increments 1-100

1. Defined one owned portfolio evidence-bundle boundary.
2. Limited the bundle to market-price and FX facts.
3. Kept the legacy generic CSV importer compatible.
4. Defined a strict canonical column order.
5. Added a downloadable CSV template.
6. Labeled imported claims as `Fact`.
7. Disclosed that upstream sources remain user-supplied.
8. Set a 2 MiB file limit.
9. Set a 5,000-row limit.
10. Defined preview-before-apply semantics.
11. Required a `.csv` filename.
12. Required non-empty file content.
13. Required UTF-8 or UTF-8 BOM encoding.
14. Enabled strict CSV parsing.
15. Rejected duplicate column names.
16. Rejected missing canonical columns.
17. Rejected unexpected columns.
18. Ignored fully blank rows.
19. Rejected files without data rows.
20. Calculated the exact content SHA-256.
21. Resolved portfolio ownership before reading scope.
22. Returned 404 for cross-owner access.
23. Scoped holdings to positive quantities.
24. Collected allowed holding tickers.
25. Required each price ticker to link to a Company.
26. Added the active benchmark ticker to price scope.
27. Resolved the benchmark Company by ticker.
28. Enforced the holding or benchmark price currency.
29. Derived required foreign currencies from holdings and benchmark.
30. Allowed only direct or inverse portfolio-base FX pairs.
31. Normalized tickers to uppercase.
32. Bounded ticker length.
33. Restricted ticker characters to market-symbol-safe characters.
34. Required finite positive prices.
35. Required three-letter alphabetic price currencies.
36. Required non-future ISO observation dates.
37. Bounded price provider symbols.
38. Rejected spreadsheet-formula provider symbols.
39. Restricted price types to close, adjusted close, official close, or NAV.
40. Derived adjustment state from price type.
41. Required distinct three-letter FX currencies.
42. Required finite positive FX rates.
43. Required non-future FX observation dates.
44. Rejected portfolio-irrelevant FX pairs.
45. Bounded FX provider symbols.
46. Rejected spreadsheet-formula FX provider symbols.
47. Normalized FX currencies to uppercase.
48. Preserved quote-units-per-base-unit semantics.
49. Preserved the exact source URL.
50. Preserved the exact source timestamp.
51. Required a named upstream provider.
52. Rejected generic `manual` and `unknown` provider labels.
53. Bounded provider-name length.
54. Rejected spreadsheet-formula provider names.
55. Required an HTTP or HTTPS source URL.
56. Required a source URL hostname.
57. Rejected source URLs containing credentials.
58. Rejected localhost source URLs.
59. Rejected private and non-global IP source URLs.
60. Bounded source-URL length.
61. Required an ISO 8601 source timestamp.
62. Required an explicit timestamp timezone.
63. Rejected materially future source timestamps.
64. Rejected source timestamps before the observation date.
65. Rejected known Mock Data markers in source labels.
66. Rejected fields that do not belong to a row type.
67. Returned field-level row errors.
68. Returned explicit create, skip, and error actions.
69. Returned bundle and row-type counts.
70. Returned the exact resolved import scope.
71. Defined a source-aware market-price identity.
72. Defined a source-aware FX identity.
73. Skipped exact duplicates within one file.
74. Blocked conflicting duplicates within one file.
75. Skipped exact stored market-price duplicates.
76. Blocked conflicting stored market-price facts.
77. Compared provider names case-insensitively.
78. Skipped exact stored FX duplicates.
79. Blocked conflicting stored FX facts.
80. Normalized SQLite and PostgreSQL timestamp comparison.
81. Added authenticated template download.
82. Added authenticated non-writing preview.
83. Added authenticated apply.
84. Required apply to carry the preview SHA-256.
85. Rejected changed files with HTTP 409.
86. Revalidated every row during apply.
87. Made all accepted writes atomic.
88. Added a Processing Run for every reached apply attempt.
89. Sanitized failed-run error codes.
90. Recorded filename, byte size, portfolio ID, and bundle hash.
91. Linked imported market prices to their Processing Run.
92. Linked imported FX observations to their Processing Run.
93. Added market-price `source_url` persistence.
94. Added price and FX `claim_type` persistence.
95. Added migration `g8g8g8g8g8g8` and readiness columns.
96. Added explicit binary response-contract inventory coverage.
97. Added portfolio UI loading, empty, error, blocked, ready, and success states.
98. Disabled apply unless the server preview is clean and creates facts.
99. Added 15 focused ownership, validation, atomicity, conflict, and idempotency tests.
100. Reconciled current-state, schema, roadmap, handoff, and validation evidence.

## Validation

- Backend: 619 passed, 4 upstream `openpyxl` deprecation warnings.
- Focused portfolio evidence tests: 15 passed.
- Frontend: 125 passed.
- TypeScript: passed.
- Alembic: full empty-PostgreSQL upgrade passed; one head,
  `g8g8g8g8g8g8`; all five new provenance columns were present.
- Docker connection: working. The normal backend, frontend, scheduler,
  PostgreSQL, and pgAdmin containers were running when inspected.
- Normal database: intentionally unchanged at `ee6ee6ee6ee6`.

## Known Limitations

- The importer does not independently verify the upstream URL or data value.
- DNS hostnames are syntax-checked but not resolved because the URL is stored,
  not fetched.
- Holdings, benchmark configuration, snapshots, and trusted DCF outputs remain
  separate workflows.
- The real-input portfolio smoke remains pending until a genuine owned dataset
  satisfies the readiness audit.
