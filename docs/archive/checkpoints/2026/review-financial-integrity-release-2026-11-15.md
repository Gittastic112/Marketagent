# Financial integrity and Today release

November 15, 2026 local date; installation completed November 16 at 04:09 UTC.
This is dated release evidence, not the next-work queue. The
[limitation ledger](../../../limitations.md#returned-code-review) owns open work.
The original [implementation receipt](../../../../data/reviews/review-financial-integrity-ten-sets-20261115.json)
remains an unchanged checkpoint; its pending release fields are superseded here.

## Published scope

[PR 18](https://github.com/Gittastic112/Marketagent/pull/18) is merged as
`d6902dfa014a4f249677efcd7ba3cc0c0d1d4c4b`. Its ten earlier repairs were installed
before this batch. [PR 19](https://github.com/Gittastic112/Marketagent/pull/19) is
merged as `92a3ba722c7e06a27d235de4f89cc17fa1a0178b`, preserving the tested source
tree at `5dfe94076ec9cabb48939707f901163f2fd9195e` and both parent histories.

The ten additional findings are A1-F6/F7, A2-1/2/3/8 and A3-2/3/4/5. They cover
unit and percentage interpretation, saved-valuation validation, financial-sector
context, duration sign, WACC bounds, atomic transaction corrections, snapshot
currency, benchmark freshness and unknown portfolio weights. Original records
and source bytes are not rewritten to make those guards pass.

Today starts with portfolio summary cards, followed by the daily brief and active
alerts. The research queue comes afterward and shows six records, defaulting to
Needs review. All remains an explicit filter. Recent notes and company shortcuts
remain available; source activity and additional event detail use disclosures.
Source coverage, timestamps, stale evidence and missing-input states remain visible.

## Final verification

All seven gates pass in the [final source workflow](https://github.com/Gittastic112/Marketagent/actions/runs/43801386306):

- Clean release baseline: 2,101 backend tests passed, 15 skipped; 395 frontend
  tests passed; type checking and production builds passed.
- Browser job: 71 workflows and seven PostgreSQL integration checks passed.
- Repository, dependency security, container security, recovery and aggregate
  result gates passed. The 36 maintained wire contracts also passed locally.
- Signed-in normal-app viewing: overview precedes the queue; both filters retain
  accurate bounded counts; visible home text is at least 12px. Desktop page and
  client widths were both 1270px; phone widths were both 380px with no overflow.

An earlier local PDF test hit its processing-time bound, then passed in isolation.
Earlier browser failures identified sub-12px text and two incorrectly funded or
duplicated portfolio fixtures. These were corrected without weakening assertions;
the final hosted run above passed cleanly. Isolated Mock Data workflows and normal
app viewing do not establish genuine-input financial accuracy or actual daily use.

## Installation and preservation

The existing Compose project was reused. Only backend, frontend and scheduler
were recreated; all bindings stayed on localhost and optional services stayed disabled.

| Role | Installed image identity |
|---|---|
| Backend and scheduler | `sha256:8a2bec191fb8c57a44550f49172410aa76905cf53dc51b9a7334c075e67cd761` |
| Frontend | `sha256:faba3823977db497da51a390ca518c7127f2151ba3a45e9008476473006015fc` |
| PostgreSQL, unchanged | `sha256:ba023b77f84f85def321997ce68bf869bb0674e1bc71c674db2b0b0035dbfc8e` |
| Current repository tools | `sha256:68c98ecd57186b0a5ec07af2a2901513b0ed494273dae7967c076c703728c993` |

All 110 table inventories and original asset bytes matched before and after the
installation. Settings, mounts, network, security options and both persistent
volumes were unchanged. PostgreSQL was not restarted; the schema remains
`u3u3u3u3u3u3`. The existing verified recovery copy was reused, with SHA-256
`97d4c7ac27a19e69b15d97a84320f3b038d7fb260b8a9e69ec81b5c4fa60a31a`.
No new database dump, synthetic normal-app dataset or acceptance point was created.

## Storage and privacy

The bounded cleanup removed nine obsolete or intermediate image identities and
72 build-cache records. Docker image layers plus unshared cache fell from
6,329,734,735 to 2,959,186,062 bytes, releasing 3,370,548,673 bytes at this checkpoint.
An additional 483,524,608 allocated filesystem bytes were released from generated
frontend files and the allowlisted temporary build context. The host refused
directory removal inside the generated frontend trees; their files were removed
and the remaining empty directory shells measured zero allocated bytes.

At this publication checkpoint, five containers and five images include the
temporary GitHub publication session and its old tools image. Their release
condition is final documentation publication and sign-out. The local final-cleanup
receipt records their removal and final storage totals; the normal application
needs four containers and three runtime images, plus one current tools image.
No database volume or essential recovery material is a cleanup target.

Compact local installation, UI and cleanup receipts live under
`output/review-financial-integrity-20261115/`. Exact removed IDs and paths remain
there. Screenshots stay local because they contain research context. Raw review
reports, machine configuration, credentials and normal research data were not
published. Commits and merge commits use the GitHub noreply identity; repository
visibility was not changed and main remains the default branch.

## Next boundary

Twenty bounded review repairs are installed; 19 primary findings remain
unimplemented. Continue with A3-9 return-method alignment, then R5 source intake
and R6 saved-editor/export integrity. Populated legacy conversion and restore
remain held, and incomplete opening histories still block transaction correction.
The ledger retains these limits rather than treating a green build as completion.
