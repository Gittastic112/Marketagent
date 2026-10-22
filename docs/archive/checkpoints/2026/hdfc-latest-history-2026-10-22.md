# HDFC latest history and revision provenance: October 22, 2026

The normal local research/demo app now includes HDFC's selected FY2026 statements
and its bonus-adjusted FY2025 comparatives. Fundamentals exposes normalized values,
units, source identity, review basis and limitations through keyboard-accessible
details. This cross-cutting batch necessarily touches financial persistence,
source-history tests, the consuming UI/browser check, review receipts and their
linked status documents. No schema, dependency or public API change is needed.

## Source decision and actual application

[M05-HDFCBANK-12](../../../../data/reviews/hdfc-financial-review-20261022.json)
reviews the retained official FY2026 PDF, SHA-256
`ec2d162371db0a5b4af04fe1ed78b77bd50e097259e1b940b4155139b20b4848`.
PDF pages 471, 472 and 546 provide 64 source occurrences and 60 distinct annual
facts. Independent references and fresh parser output match all values, units and
locations. Four bonus comparisons and 14 statement equations pass. Three direct
EPS checks pass; FY2025 basic EPS is an explicit exception: reported INR46.41
versus calculated 46.4041488340, which rounds to 46.40. Halving prior rounded
92.81 is consistent with 46.41, but the issuer's internal rounding method is unknown.
The source figure stays unchanged, and that check is not marked passed.

Notes on PDF pages 377/378, 509/510, 546 and 554 distinguish bonus-adjusted weighted
shares, actual ending shares, proposed versus paid/special dividends, standalone
regulatory capital, consolidated accounting equity and the separate unaudited
Pillar 3 disclosures. Page 249 corroborates the July 1, 2023 merger; a comparable
FY2024 combined full-year earnings series is not reconstructed. No bank EV debt,
excess cash, option value, distributable capital or forecast is inferred.

[M05-HDFCBANK-13/14 application](../../../../data/reviews/hdfc-financial-application-20261022.json)
retains the PDF as document 19/asset 10. Runs 122/123 record intake and review.
Version-checked promotion adds FY2026 and revises four FY2025 numeric fields:
basic/diluted EPS and their weighted-share denominators. Twenty-six monetary unit
labels change from "INR crores" to the equivalent "INR crore" without rescaling.
FY2024, earlier source values/units/IDs, saved valuations and portfolios remain.

Run 124 commits promotion but fails its post-write audit: two older repeated EPS
occurrences remained active. The old helper retired just one active occurrence.
M05-HDFCBANK-14/Run 125 retires only obsolete flags on revisions 61 and 63 at the
actual repair time. No row, value, source ID or revision number is deleted or
rewritten. Run 124 remains failed; the successful fresh read-only audit and exact
repair receipt are separate. No second promotion is performed.

HDFC now has 90 facts, 128 revisions and 12 normalized values across three periods.
Across all 11 scoped securities: 33 periods, 901 facts, 975 revisions and 332
normalized values. Unrelated records, including HDFC FY2024, match their original
fingerprints. Five personal Apple approvals and original human-verdict fields are
unchanged. These are delegated agent decisions, not independent human certification.

## Code and browser verification

Normalization now joins the current source revision to its candidate and requires
matching company, period, value, unit and promoted state. Unapplied, superseded,
mutated or ambiguous sources cannot relabel a current value. Missing provenance
is explicit. The existing source-history writer now retires every active prior
occurrence within the same fact/period scope when a new fact is promoted.

Local tests pass 37 focused backend checks without a fixture database; frontend
tests pass 304, with TypeScript and the production build. Added integration tests
cover unapplied/revised candidates and legacy duplicate active revisions. The
existing PDF browser test also opens normalized details with the keyboard.
Full remote CI for this new source remains pending publication; the prior Next.js
head `767a8526` passes all five jobs on both PR and push runs.

Six normal desktop/mobile views pass 60 source-value comparisons, correct PDF
highlights, keyboard details, no writes/errors/overflow and zero axe violations.
Readiness is 369-2,105ms under the unchanged 15-second limit. Two narrower visual
views inspect the latest review notes; the first screenshots of the older FY2024
row remain retained. All 109 post-application table fingerprints stay unchanged.
No disposable database, invented trade or AI scan is created.

## Runtime, backup and retained evidence

Backend/workers use `market-intelligence-hdfc-revisions-runtime:20261022`,
`sha256:4dbb6f7411b042d36a108a51d3d7cea4416c1164e31090fe163430c7724fcb3c`.
Frontend uses `market-intelligence-hdfc-review-frontend:20261022`,
`sha256:ae3b16e35ee7028582cf3ff536ff1363586062d660eabf7c67364ca67b2d1b68`.
The original PostgreSQL volume/schema, runtime settings and localhost ports remain.
Daily Brief resumes; source refresh and pgAdmin remain stopped. Protected
environment files are not read. Seven additional rollback registrations retain
their files, logs and images outside the six-service active Compose project.

The unchanged pre-application database reuses the hash-verified October 21 dump.
After the reviewed data changes, a new quiesced dump is 128,206,582 bytes, mode 0600,
SHA-256 `5fe1b539edc5848ebd3cdfe45b5aa6089ef6d25da5c7a5ae56a00909e2cdb4f3`.
Archive listing passes; this is not a new restore/off-device test. Only its verified
temporary container staging copy is removed. Removing the successful frontend
builder stage separately reclaims 849,557,071 actual Docker layer bytes; runtime,
rollback images, persistent volumes, backups and failed evidence remain.

A dated post-work sample records 1,093.2MiB combined container working set and
0.75% CPU, excluding Docker VM overhead. Docker reports 25.94GB images, 3.341GB
volumes and 4.487GB build cache; shared layers make category totals non-additive.
Host free space is about 25.1GiB. These readings do not guarantee future usage.

Evidence and exact replay recipes live in `output/milestones/hdfc-latest-20261022/`.
Retained failures include directory ownership in the first audit harness, singular
versus plural unit spelling, and the legacy active-revision audit. None is hidden
by increasing tolerances or discarding prior evidence. The
[tracker](../../../roadmaps/completion-tracker.md) owns gates and the
[limitation ledger](../../../agent_capabilities_and_limitations.md) owns remaining
accounting/model/mapping work and operator inputs. Acceptance remains 20 points.
