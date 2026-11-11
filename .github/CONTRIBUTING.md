# Contributing

Start with the [setup guide](../docs/local-development.md),
[architecture](../docs/architecture.md), and [code map](../docs/code-map.md).
Agents also follow [AGENTS.md](../AGENTS.md) and the nearest nested rules.

## Make a change

1. Inspect Git status and preserve existing edits and untracked files.
2. Find the owning route, contract, service, callers, and tests in the code map.
3. Make a focused change. Keep public imports, review gates, ownership checks,
   provenance, and missing/zero distinctions intact.
4. Run the relevant [verification commands](../docs/execution-runbook.md).
   Use isolated tests; do not point fixtures at a user's database.
5. Update the current document that owns the changed behavior.
6. Describe the problem, resulting behavior, validation, and remaining limits.

Use branches prefixed `codex/` for agent work. Do not bundle unrelated changes,
generated reports, copied helper packages, credentials, or user databases.
Dependency changes need a concrete reason and matching lockfile review.

## Documentation

[The documentation index](../docs/README.md) assigns one owner per concern.
Keep setup, validation, operations, product status, and limitations separate.
Archive dated evidence; do not copy old task lists into current instructions.
Run `python3 -m unittest scripts.test_check_docs` and
`python3 scripts/check_docs.py` after edits.

## Data and security

Source corpora and review receipts are evidence, not disposable fixtures.
See the [data guide](../data/README.md) before changing datasets.
Report sensitive security findings privately as described in
[SECURITY.md](SECURITY.md). No contribution authorizes public deployment,
financial recommendations, or disclosure of private research.
