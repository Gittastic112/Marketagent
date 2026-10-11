# FCFE/DDM explicit-input integrity

September 16, 2026. Historical evidence, not an execution queue.

## Findings and implementation

- Both supplementary methods discounted equity cash flows with terminal WACC,
  ignored explicit cost of equity, and silently substituted 2% growth and one
  share for zero/missing inputs. Missing FCFE components also became zero.
- The two methods now share one deterministic Gordon-growth helper in
  backend/app/services/fcfe_ddm_engine.py. Cost of equity, growth, diluted shares
  and cash flow must be explicit and finite. The rate must exceed growth; shares
  must be positive. No WACC, 10% rate, 2% growth or one-share substitution remains.
- FCFE requires net income, capex, depreciation, working-capital change, new debt
  and debt repayments. Explicit zeros are accepted; incomplete/nonfinite inputs
  return unavailable. Aggregate cash returned similarly requires all components.
- Valid zero cash flow/dividends produce zero estimates; a zero equity rate is
  retained and can converge only with lower growth. Negative cash flow is outside
  this one-stage estimate, not silently replaced with a positive default.
- Missing/invalid attempted methods receive watch diagnostics with affected fields
  and the formula. Core FCFF values remain unchanged; quality scores can reflect
  the added warnings. This is not a new global block on valid FCFF calculations.
- Payout messages use saved currency, identify saved assumptions and no longer
  assert actual borrowing, issuance causation or value destruction as facts.

## Verification scope

- New test file: backend/tests/test_fcfe_ddm_integrity.py, 43 regressions.
  Before correction, 40 failed and three passed. After correction, all passed.
- Focused suite: 97 passed, including DCF math, zero defaults and scenario consumers.
- Backend and scheduler production image builds passed. No normal deployment,
  source data writes, dependency changes or migrations.
- API regression covers persisted corrected values and a sparse versioned resave.
  Historical reads and storage preserve an explicitly seeded legacy result.
- Full backend suite: 992 passed, four upstream openpyxl deprecation warnings.
  Documentation/secret checker tests, link/context checks, secret scan, project
  workflow validation and whitespace checks passed. No fresh browser check is claimed for this backend-
  only change; the preceding Real Options browser proof is a separate batch.

Scope remains the supplementary one-stage FCFE/DDM calculation and payout
diagnostics. Model suitability, historical/legacy UI, scenario assumptions and
specialized-engine work remain in the [single ledger](../../../agent_capabilities_and_limitations.md).
