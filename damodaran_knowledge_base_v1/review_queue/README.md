# Review Queue

This folder contains unresolved source conflicts, possible doctrine changes,
template contamination, ambiguous dates, and application behavior that cannot be
certified from the source corpus.

Each item must include a `Status` and a concrete required decision. Resolve an
item by recording the decision in the file, moving any resulting reusable rule
into `knowledge/`, updating the catalog/manifest, and then moving the item to a
future `review_queue/resolved/` directory. Never delete the audit trail.

Current open items: none.

Resolved decisions are preserved under `resolved/`.
