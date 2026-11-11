# Backend operational commands

These commands use application services and the configured database. Run them
only in the intended environment from the [runbook](../../docs/execution-runbook.md)
or [Operations](../../docs/operations.md). A name beginning with check does not
imply that the command leaves no audit record.

| Command | Purpose | Access and effects |
|---|---|---|
| [check_public_providers.py](check_public_providers.py) | Explicit SEC, FRED, or market-provider connectivity probe | External request and persisted Processing Run; requires provider configuration and explicit security scope where applicable |
| [check_ai_provider.py](check_ai_provider.py) | One fixed Gemini connectivity prompt | External AI request and sanitized Processing Run; configurable model; no research or portfolio prompt |
| [check_portfolio_real_input_readiness.py](check_portfolio_real_input_readiness.py) | Audit one owned portfolio's persisted inputs | Read-only database access; requires portfolio and user IDs; missing inputs remain unavailable |
| [report_financial_coverage.py](report_financial_coverage.py) | Report source/financial coverage for an explicit scope and checklist | Read-only database access and a local report file; no fetching, promotion, or approval |
| [seed_assumption_methods.py](seed_assumption_methods.py) | Import reviewed India/country assumption workbooks | Database writes; requires all named workbooks under the configured workspace data path; no numeric fallback |
| [stage_adani_reference_data.py](stage_adani_reference_data.py) | Issuer-specific APSEZ source staging | Default refusal to apply; --apply creates/updates company, source, candidate, and draft records from hash-verified supplied PDFs |
| [finalize_adani_reference_data.py](finalize_adani_reference_data.py) | Finalize the scoped APSEZ reference workflow | Default refusal to apply; --apply can repair, review, promote, normalize, and refresh scoped records; explicit cutoff and source checks required |

The issuer-specific tools remain because their source contracts and regression
coverage are maintained. They are not onboarding steps or authorization to
restore the historical company universe. The current approved scope is in
[current state](../../docs/current-state.md).

The uncalled manual ledger smoke script is [retired](../../scripts/retired/README.md).
Its behavior is covered by [assumption-diff tests](../tests/test_assumption_diff_service.py)
and [version-integrity tests](../tests/test_assumption_version_integrity.py).

[Root tools](../../scripts/README.md) own repository checks, recovery, and broader
ingestion commands. The documentation checker requires every maintained command
in both directories to appear in its owning guide.
