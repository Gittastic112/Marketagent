# Repository navigation and measured cleanup

October 18, 2026. The user requested efficient traversal, smaller context loads,
duplicate/dead-asset review and RAM/disk reduction. This is maintenance of accepted
M01/M02, not a new milestone or completion of the remaining financial reviews.

## Instructions and layout

The refined policy is in [AGENTS.md](../../../../AGENTS.md): start with the compact
JSON map, discover filenames in the owning directory, query the matching detailed
map row, then inspect actual callers and tests. Preserve framework route/package
boundaries. Delete only identified generated material after measuring and checking
tracking and usage. Untracked, old or large does not by itself mean disposable.

The existing layout stays: backend/app owns routes/contracts/services/persistence;
backend/tests owns its behavioral tests; frontend/app owns Next.js routes;
frontend/components and lib own UI/data access; frontend/e2e owns browser workflows;
scripts owns operations and docs owns current references. Adding src directories
or flattening App Router segments would change imports/routes without proven savings.
Compatibility facades and distinct parser contracts remain intentional.

AGENTS.md is 155 lines and its JSON map resolves 22 existing paths. The detailed
code map remains the sole domain index. A financial-review lookup returns 547 bytes
instead of reading the entire 28,038-byte map; this is a byte comparison, not a
measured LLM-token or latency claim.

.gitignore now covers all local virtual-environment variants, caches, coverage,
logs, system files and generated output. Protected environment names are excluded;
the existing example template remains versioned. .rgignore additionally excludes
archived bodies, raw source corpus, locks and the large decision register from
broad searches. Exact-path reads remain available when required and authorized.
These search exclusions do not remove or untrack those source/receipt files.
Both Docker contexts exclude nested environment-file names; frontend exclusions
also cover local environments and generated caches. Isolated backend test commands
now explicitly select /dev/null as the Compose environment file.

## Audit and removal

The initial metadata inventory found 3.128 GB of project files, excluding protected
environment paths and without following symlinks. Major categories: output 1.670 GB,
Git objects/metadata 831 MB, frontend dependencies 419 MB and backups 79 MB.
No generated dependency/cache directory was tracked. The obsolete tracked
repo_map.txt was an 83,276-byte generated path listing and is removed/ignored.

Thirty-three verified generated paths were removed: six Python environments
containing only pip 26.1.1, Python/test/package caches, two desktop metadata files
and frontend TypeScript incremental state. The removal receipt records 6,129 files
and 77,304,943 logical bytes, plus the separate obsolete map. No application package
or test dependency declaration changed. Frontend node_modules remains because
local Node processes may use it; full process inspection was restricted. Installed
files are disk usage, not a measurement of active RAM.

Docker initially reported 87 images / 24.70 GB, 18 volumes / 3.125 GB and 135 build
cache records / 8.068 GB. Conservative age/space filters reclaimed zero. Cache
inventory then identified 50 unused, unshared records. Removing only those IDs
reclaimed approximately 3.581 GB; the post-prune snapshot retains 85 shared cache
records / 4.487 GB. Later verification can create small new build-cache records.
The [Docker filter reference](https://docs.docker.com/reference/cli/docker/buildx/prune/)
supports explicit cache ID selection. This is daemon-reported reclamation, not a
claim that the macOS sparse disk image shrank by the same amount immediately.
All image identities, all volume names and all four running container IDs compare
equal before/after. No image, volume, backup, source report, failed browser trace,
review receipt or user dataset was removed. No normal runtime restart was required.
Docker categories share layers and must not be added into a purported disk total.

One idle sample before cleanup totaled about 505 MiB across the four normal
containers, with 0.37% CPU on the one-core scale. No RAM reduction is claimed.
This excludes Docker VM overhead and is not a future resource guarantee.

## Duplication and validation

A bounded AST comparison found no identical backend application function bodies
of at least eight lines with the same arguments. This does not rule out semantic
or smaller duplication. Caller inspection confirms both workbook parsers are used:
generic upload parsing and strict typed/versioned dataset ingestion have different
contracts. pdfplumber extracts text/coordinates; pypdfium2 renders previews;
openpyxl/xlrd support distinct workbook formats; pandas performs tabular parsing.
The runtime/test requirement split and frontend manifest each retain active roles.
No dependency or utility was removed merely because its name overlapped another.

Verification: 19 documentation/Compose tests passed, 35 ignore behavior probes
passed and 22 navigation paths resolved. Source/fixture/receipt paths remain visible
to Git. The shared index is unchanged. The final documentation checker passes
79 active Markdown files, 760 local links and context budgets. With the same post-cleanup files and protected
paths excluded, the old ignore rules expose 9,422 paths versus 1,143 with the new
rules; later evidence files can change those counts. No new fixture database,
provider call, application build or browser run was needed for these file-only
changes. Earlier application/browser evidence remains separately dated.

Initial GitHub validation passed browser, recovery and both security jobs, but
the frontend source guard still expected the example environment file in its
Docker context. The guard now requires recursive environment exclusions in both
contexts without an environment-file exception. Frontend patterns use Docker's
[recursive wildcard](https://docs.docker.com/build/concepts/context/#matching).
All 302 frontend tests pass locally. Two tiny scratch builds verify that Docker
excludes 26 non-secret environment filename probes at multiple depths while
retaining ordinary source files. These checks create no database or runtime image
and never copy actual environment files. Publication includes 14 distinct paths
across the cleanup and this correction; the PR owns final CI results.

Local evidence: output/cleanup-20261018 contains inventories, exact removal and
cache-ID manifests, before/after image/volume/container lists, failed/zero-result
prune logs, verification results and recipes. The [tracker](../../../roadmaps/completion-tracker.md)
retains 20 acceptance points. GitHub publication follows these local checks; the
existing PR records the published head and its own validation results.
