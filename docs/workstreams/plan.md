# Workstream scope index

Use this index only for an explicitly assigned parallel batch. Current product
priorities live in the [roadmap](../roadmaps/product-roadmap.md); acceptance lives
in the [completion tracker](../roadmaps/completion-tracker.md).

The [October 5 design](../archive/plans/workstreams-2026-10-05.md) retains the
original technical analysis and sequencing. Its defect descriptions are dated
observations, not a list of current defects or instructions to launch agents.

## Coordination

- [ownership.tsv](ownership.tsv) is the exclusive file allowlist during an assigned
  batch. Review it against the intended change before allocating work; unlisted
  paths and shared contracts remain frozen for that batch.
- The coordinator owns shared-document reconciliation and integration. Each
  worker records evidence within its assigned area.
- Follow the [parallel-workstream workflow](../skills/operations/parallel-workstreams.md)
  and the [runbook](../execution-runbook.md#parallel-workstream-checks) for isolation,
  ownership checks, and test-lane coordination.
- [Historical evidence](evidence/README.md) stays at its recorded paths. A past
  receipt does not grant new data changes, provider calls, or valuation approval.

## Scope and acceptance owners

| Workstream | Boundary | Acceptance owner |
|---|---|---|
| W1 | Reviewed private evidence in Daily Brief | M08 |
| W2 | Reviewed financial-source coverage | M05 |
| W3 | Historical positions, cash, and portfolio proof | M07 |
| W4 | Sensitivity calculation integrity | M06 |
| W5 | Consistent backups and recovery evidence | M03 |

These mappings organize work. Completion of a workstream does not close a
milestone without its current acceptance gate and evidence.

<a id="5-w1-reviewed-private-evidence-in-daily-brief"></a>
## W1: Brief evidence

Private source and review context enters the deterministic brief with its exact
basis. See the [original design](../archive/plans/workstreams-2026-10-05.md#5-w1-reviewed-private-evidence-in-daily-brief).

<a id="6-w2-reviewed-usindia-financial-source-coverage"></a>
## W2: Financial sources

Review extraction, reconciliation, normalization, and security/share/unit scope.
See the [original design](../archive/plans/workstreams-2026-10-05.md#6-w2-reviewed-usindia-financial-source-coverage).

<a id="7-w3-historical-positions-cash-and-portfolio-proof"></a>
## W3: Portfolio history

Replay dated transactions and preserve incomplete-history states in snapshots,
returns, and readiness. See the [original design](../archive/plans/workstreams-2026-10-05.md#7-w3-historical-positions-cash-and-portfolio-proof).

<a id="8-w4-trustworthy-sensitivity-calculations"></a>
## W4: Sensitivity

Preserve the saved model basis and explain invalid or unavailable calculations.
See the [original design](../archive/plans/workstreams-2026-10-05.md#8-w4-trustworthy-sensitivity-calculations).

<a id="9-w5-consistent-backup-and-recoverable-evidence"></a>
## W5: Recovery

Keep database and document-store evidence consistent and verify isolated restores.
See the [original design](../archive/plans/workstreams-2026-10-05.md#9-w5-consistent-backup-and-recoverable-evidence).
