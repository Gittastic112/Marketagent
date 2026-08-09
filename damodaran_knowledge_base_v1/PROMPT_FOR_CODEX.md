# Codex Prompt

Process `damodaran_knowledge_base_v1/raw/inbox/` according to
`damodaran_knowledge_base_v1/AGENTS.md`.

First run the integrity auditor and stop on exit code `1`. For each pending file:
hash it, inspect content and metadata, check exact duplicates, classify and route
one untouched canonical copy, preserve source/as-of dates, compare with canonical
knowledge and application behavior, and add rules only with direct support. Dated
data is not doctrine. Company assumptions are not universal rules. Put unresolved
conflicts in `review_queue/`.

Update `data/processing_ledger.csv`, `data/source_catalog.csv`,
`data/raw_file_hashes.csv`, `manifest.yaml`, affected references/docs, and focused
tests. Finish only when the inbox is empty and the auditor plus unit tests pass.

Report: files processed/routed, duplicates, canonical records changed,
conflicts requiring review, tests, and known limitations.
