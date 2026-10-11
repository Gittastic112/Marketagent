# Review Queue

This folder contains unresolved source conflicts, possible doctrine changes,
template contamination, ambiguous dates, and application behavior that cannot be
certified from the source corpus.

Each item must include a `Status` and a concrete required decision. Resolve an
item by recording the decision in the file, moving any resulting reusable rule
into `knowledge/`, updating the catalog/manifest, and then moving the item to a
existing `review_queue/resolved/` directory. Never delete the audit trail.

Current queue items: none. This does not mean every source agrees: known
case-specific conflicts remain documented in [SpaceX conflicts](../cases/spacex_2026/conflicts.md).

Resolved decisions are preserved under `resolved/`.
