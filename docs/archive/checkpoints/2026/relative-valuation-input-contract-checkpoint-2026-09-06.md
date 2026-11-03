# Relative Valuation Input Contract

**Date:** 2026-09-06

## Ten Completed Tasks

1. Rejected NaN, infinity, and boolean values across all relative-valuation
   financial fields.
2. Required nonnegative debt/cash and strictly positive supplied diluted shares;
   retained explicit missing values and genuine losses in income/equity fields.
3. Rejected unknown financial and request fields rather than ignoring typos.
4. Required one to six supported, unique multiple methods.
5. Required exactly one benchmark basis: peer set or country/industry.
6. Validated company and peer identifiers against positive database integer
   bounds, and trimmed source-selection strings.
7. Marked overflowing method calculations unavailable while retaining valid
   results from other methods.
8. Calculated the displayed mean using scaled summation to avoid overflow from
   otherwise finite per-share estimates.
9. Added regressions for malformed requests, preserved losses/missing values,
   multiplication/division/equity-bridge overflow, mixed valid/unavailable methods,
   finite averages, and JSON-safe validation errors.
10. Completed regression, build, local deployment, and documentation updates.

## Implementation Boundary

Changed `backend/app/services/relative_valuation.py`,
`backend/app/api/errors.py`, and added
`backend/tests/test_relative_valuation_input_contract.py`.
The existing frontend already renders API errors and unavailable-method reasons.
No database migration or new financial assumptions were introduced.

The error serializer now converts non-finite values in legacy error detail to
JSON null. This ensures a rejected non-finite request can return a valid 422
envelope instead of failing while constructing the error response.

## Validation

- Focused input, pricing, peer, API-error, and response-contract gate: 127 passed.
- Full backend suite: 774 passed with four existing upstream `openpyxl` warnings.
- Frontend boundary remains 138 passing tests, TypeScript, and a successful
  production build from the immediately preceding 20-step increment.
- Backend and scheduler images rebuilt successfully.
- Local deployment passed: backend schema readiness at `o6o6o6o6o6o6` with
  no missing tables/columns/constraints; backend, frontend, PostgreSQL, and
  scheduler healthy/running.
- Documentation: 62 active Markdown files, 311 local links, 11 project-skill
  validations, and clean diff whitespace.
- The 66 new test cases include all nine financial fields, both benchmark modes,
  database identifier bounds, and large-number calculation behavior.

The current product constraints remain in the single
[`../../../agent_capabilities_and_limitations.md`](../../../agent_capabilities_and_limitations.md)
ledger.
