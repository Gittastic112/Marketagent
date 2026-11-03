# Security hardening and evidence-linked analyst reviews

Review date: September 30, 2026, New York. Tool timestamps extend into October 1 UTC.
This is a code/dependency/local-runtime assessment, not an independent penetration
test, security certification or authorization to deploy publicly. The existing
dirty worktree was preserved. No provider keys or research records were printed,
rotated, approved or transmitted to an AI service.

## Audit coverage and changes

| Area | Finding and implemented response |
|---|---|
| Dependencies | Initial pip-audit output contained 67 advisory records across ten installed packages, including advisory aliases, not 67 proven exploits. npm reported four affected packages. Updated FastAPI/Starlette, multipart, cryptography, settings/dotenv and test tooling; removed unused python-jose/Authlib and their unused crypto dependency path. Next resolves to 16.3.8; sharp to 0.35.4; affected transitives refreshed. Both final package audits report no known vulnerabilities on this date |
| Authentication and sessions | Existing signed 60-second server identity and private ownership checks retained. Login uses constant-time hashed comparisons and bounded attempts. The browser proxy validates configured Host and mutation Origin, ignores forwarded-host assertions, forwards a small header allowlist and refuses upstream redirects. Missing/foreign origins return 403 |
| Authorization and tokens | Every documented application operation plus hidden compatibility routes retains authentication, except the explicit health/readiness allowlist. Private review routes resolve owner/company scope. Generic global token writes now return a safe 503; the normal token table was empty and preserved. Settings no longer claims secure token storage is active |
| Network and SSRF | Public URL validation checks all IPv4/IPv6 answers, rejects non-public destinations and fails closed on DNS errors. RSS/filing-text downloads pin the socket destination while verifying the original TLS name; redirects/proxies/compressed bodies are rejected and time/byte limits apply. A real public HTTPS test page succeeded with verified TLS. This does not cover every fixed-provider HTTP client |
| Uploads and availability | Global 42 MiB body cap and 30-second intake deadline, bounded upload reads, XLSX expansion preflight, defused RSS XML and CSV formula-prefix escaping. Request throttling is tested against included routes. The framework upgrade required fixing both inventory traversal and the older rate middleware's lazy-router blind spot |
| Browser and privacy | Private/no-store, no-referrer, nosniff and basic frame/CSP policies added. Validation responses omit raw input/context. React text rendering, source escaping, upload ownership and AI transmission/review boundaries inspected. No new external AI request or financial write was needed |
| Containers and recovery | Application/workers run non-root, drop capabilities, prevent privilege escalation and bound memory/processes. Reference data mounts read-only; published ports stay 127.0.0.1. Local environment file changed from 0644 to 0600; new backups use umask 077. Normal database credentials, volumes and global Docker settings were not altered |
| Ongoing checks | CI audits frontend lockfile and backend requirements. Existing secret, documentation, localhost and backup guards retained. Backend transitives and OS images are not comprehensively locked/scanned |

Primary advisory context: multipart's
[official advisories](https://github.com/Kludex/python-multipart/security/advisories)
and [Starlette form limits](https://github.com/Kludex/starlette/security/advisories/GHSA-82w8-qh3p-5jfq)
justify parser/framework upgrades. Next's
[image-generation advisory](https://github.com/vercel/next.js/security/advisories/GHSA-vcvr-r3jv-pc5j)
and [AVIF advisory](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4),
plus [sharp's native parser advisory](https://github.com/lovell/sharp/security/advisories/GHSA-rgj7-g3m4-5g8c),
justify patched builds. Scanner severity is not proof that affected code was
reachable here; custom next/og and AVIF workflows were not observed.

Bandit inspected roughly 42,000 backend application lines. Initial results were
zero high, three medium and ten low findings. Two medium urllib warnings concern
the fixed HTTPS FRED origin, which already has a 5 MB JSON cap; redirect policy
still deserves review. The RSS XML finding was addressed with defusedxml. Low
assert/exception-flow findings were inspected, not represented as exploitable
vulnerabilities or suppressed to manufacture a clean result.

Prioritized residual work lives in the
[single ledger](../../../agent_capabilities_and_limitations.md#security-boundary):
host checks, local admin credentials, encrypted off-device recovery, parser
isolation, remaining HTTP clients, supply-chain gaps and public-use gates.

## Completed research workstream

The comparison workspace saves one of four analyst dispositions with a rationale
and explicit evidence-review confirmation. Each receipt retains the selected
group's exact passages, provenance, coverage, evidence hash and review version.
Records are append-only, owner/company/field/Mock Data scoped, with bounded
history and a receipt page. Competing versions or changed evidence return 409.

The hash covers the whole bounded company comparison and deliberately excludes
read time and previous decisions. Source/lifecycle/AI-review changes can make
receipts historical immediately after saving; a receipt is not permanent truth.
A new table, brief_comparison_reviews, is the only schema addition at head
s1s1s1s1s1s1. No source approval, semantic conflict certification, valuation edit,
provider fetch or scheduled-brief integration is implied.

## Verification

- Backend: 1,294 passed; five upstream deprecation warnings.
- Frontend: 234 passed; TypeScript and standalone production build passed.
- Static: 23 repository tests, secret scan and 11 project-skill checks passed.
- API: 279 documented paths, 505 schemas, 381 inventoried application operations,
  including compatibility routes hidden from OpenAPI.
- Five PostgreSQL competing-save pairs each returned 201/409, adding one version
  per pair; the original receipt was unchanged.
- Browser: fake credentials and explicitly labeled Mock Data in a dedicated
  tmpfs database. Confirmation-gated save, visible stale-version and changed-
  evidence conflicts, refresh recovery and original-history navigation passed.
- Desktop 1440px and mobile 390px layouts captured; mobile has no page overflow.
- A simulated lost save response blocked resubmission until a successful refresh;
  the refreshed form became usable again without inventing a saved decision.
- Receipt navigation retained original passages/rationale after source archiving,
  displayed historical evidence status and preserved the Mock Data boundary.
- Fresh backup 20261001T015318Z-market-intelligence is 8,444,244 bytes; SHA-256
  95054ae2eb58e4313a076408562af291c24ddd91e974e900a8088dbdfa8203f9.
  Restored copy matched all 108 original r9 table fingerprints. Rehearsed and
  normal s1 upgrades matched all 107 pre-existing data tables and added one empty
  review table. Normal readiness is ready; AAPL retains five pending non-mock
  findings across five inputs. No normal analyst decision was seeded.
- Runtime inspection verifies non-root application/workers, capability drops,
  no-new-privileges, resource bounds and localhost port bindings. Frontend sign-in
  returns 200; unauthenticated data proxy returns 401. All six prior normal
  services are running again. The named disposable stack and its restore copy
  were removed; backup, screenshots and fingerprint evidence were retained.

Artifacts: ignored output/playwright/security-review-2026-09-30/. No normal
analyst decision was invented to demonstrate the feature.
