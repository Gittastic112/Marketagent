# Codex Prompts

This file is intentionally short. Old prompts were removed because they describe
work that is already done and could cause Codex to rebuild completed features.

Before using any prompt, read:

- `docs/current-state.md`
- `docs/execution-runbook.md`
- `docs/portfolio-expansion-plan.md`
- `docs/security-threat-model.md`

## Current Next Prompt

```text
Read AGENTS.md, docs/current-state.md, docs/portfolio-expansion-plan.md,
docs/execution-runbook.md, docs/database-schema.md, docs/architecture.md, and
docs/security-threat-model.md.

Implement the portfolio data foundation only.

Add:
1. Portfolio model.
2. PortfolioHolding model.
3. PortfolioTransaction model.
4. PortfolioCashBalance model.
5. PortfolioSnapshot model.
6. Alembic migration.
7. Pydantic schemas.
8. Focused backend CRUD routes.
9. Backend tests for create/list/get/update/delete.
10. Basic frontend /portfolio page.
11. Portfolio create form.
12. Holding create form.
13. Transaction create form.
14. Holdings table.
15. Transactions table.

Security and scope constraints:
- Do not add market price APIs yet.
- Do not add AI.
- Do not add social scraping.
- Do not add DCF yet.
- Do not add broker sync.
- Do not store broker credentials.
- Validate quantities, prices, fees, dates, transaction types, and currencies.
- Block unsafe deletes with clear conflict messages.
- Use mocked/local tests only.
- Follow the existing backend router structure and frontend form conventions.

After completion, report files changed, tests run, manual test steps, and known
limitations.
```
