# Next 10: Statement Identity and Certification Checkpoint

**Date:** 2026-08-02  
**Status:** Implemented and validated

## Completed Steps

1. Defined a financial-statement identity contract with absolute tolerance
   `0.01` and relative tolerance `0.000001`.
2. Added annual company/period evaluation for profit after tax and profit
   attribution to parent plus non-controlling interests.
3. Added an authenticated endpoint returning formulas, inputs, actual values,
   expected values, deltas, tolerances, and unavailable/duplicate facts.
4. Added a Statement Identities section to company fundamentals.
5. Made failed applicable identities block financial-history certification.
6. Added inspectable per-history certification detail to Data Health.
7. Propagated failed identities into valuation draft review requirements,
   warnings, and `valuation_trust_status=blocked`.
8. Added backend and frontend regression coverage for the full contract.
9. Verified the live APSEZ identities and portable AAPL/APSEZ certification.
10. Reconciled the current-state, architecture, runbook, handoff, execution
    roadmap, and product capability/ideation register.

## Live Proof

```text
APSEZ annual periods: 3
APSEZ applicable identities: 6
APSEZ passed identities: 6
APSEZ failed identities: 0
AAPL annual periods: 4
AAPL applicable identities: 0
AAPL unavailable identities: 8
portable certification: passed
certified histories: 2
certified markets: IN, US
Data Health blocking errors: 0
Data Health warnings: 1
```

The remaining warning is the previously documented missing single
document-level timestamp on the AAPL SEC Company Facts snapshot. Every promoted
AAPL XBRL locator still has its filed date.

## Validation

```text
backend: 397 passed, 4 upstream openpyxl deprecation warnings
frontend: 76 passed
TypeScript: passed
Next.js 16.2.11 webpack production build: passed
portable AAPL/APSEZ certification: passed
```

## Honest Limits

- AAPL's user-approved core fact set does not contain pretax income, tax
  expense, parent income, or NCI income. Its identities are unavailable, not
  passed. Expanding the approved source set is a separate review decision.
- The current identities cover consolidated profit arithmetic only. They do not
  establish balance-sheet equality, cash-flow movement, every statement total,
  accounting-policy consistency, or parser support for arbitrary issuers.
- The tolerance is scale-aware but not issuer-specific. Future statement
  profiles may need source-declared rounding precision.
- Certification remains representative proof for one structured US issuer and
  one targeted India PDF issuer.

## Next Recommended Work

Add balance-sheet and cash-flow identities only after the required facts can be
preserved with exact evidence. Then add rendered PDF region highlighting and a
second reviewed issuer per market without weakening the current fail-closed
gate.
