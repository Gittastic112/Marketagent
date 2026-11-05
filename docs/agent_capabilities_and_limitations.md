# Agent Capabilities and Limitations

**Updated:** 2026-11-04 (independent briefing, consent and release-runner completion).
Product validation dates remain in Current State.

October 11 M06 source introduces versioned canonical FCFF sensitivities with
saved funding/terminal assumptions and per-cell unavailability. Legacy grids are
visibly unverified; normal saved models are not recalculated. The 22-workflow
isolated browser proof uses Mock Data and does not close genuine valuation review.
[Method and evidence](archive/checkpoints/2026/m06-sensitivity-2026-10-11.md).

This document is the practical trust boundary for the product. It intentionally
summarizes capabilities instead of duplicating route-by-route implementation.

## Confirmed Scope and Input Checklist

October 17 scope revision: the user explicitly chose a local research/demo first
release using the existing data, with Mac settings and off-device backup deferred.
Genuine portfolio history/multi-currency proof is outside this release; existing
examples stay labeled Mock Data or User Assumption. Public financial sources keep
their provenance and review gates. No new disposable fixture datasets, database
reset or fabricated activity is authorized. Delegated review permits supported,
recorded decisions and retained public benchmark intake; it does not certify all
existing records. The
[tracker](roadmaps/completion-tracker.md#scope-revision-approved-october-17-2026)
owns the revised acceptance profile and retains the original check IDs.

Confirmed by the user on September 21: personal research only, US and India,
USD portfolio base currency, five large companies per market, daily closes
acceptable with a preference for the latest available price. The user reported
existing SEC/Gemini integrations and no other subscriptions. The supplied SEC
contact identity is configured locally and official SEC requests succeeded.
The user accepts a Google Sheets quote delay of up to 20 minutes. Gemini's key
now works with locally configured gemini-3.5-flash-lite. September 22 verification
also scanned Apple's public FY2025 PDF through the private-source workflow. Only
the source text/date, public company identity and field names were transmitted,
not stored holdings, thesis notes or valuation values. Results remain unreviewed.

Interpretation of "top five": market capitalization, not an investment ranking.
The September 21 selection snapshot is NVIDIA (NVDA), Apple (AAPL), Alphabet
(GOOG, one share class only), Microsoft (MSFT), Amazon (AMZN); Reliance Industries
(NSE:RELIANCE), HDFC Bank (NSE:HDFCBANK), Bharti Airtel (NSE:BHARTIARTL), ICICI Bank
(NSE:ICICIBANK), State Bank of India (NSE:SBIN). Selection sources:
[US ranking](https://companiesmarketcap.com/usa/largest-companies-in-the-usa-by-market-cap/)
and [India ranking](https://companiesmarketcap.com/india/largest-companies-in-india-by-market-cap/).
The initial ten-company import added 205 sourced price records from successful
30-day-window imports (195 completed daily prices and 10 latest quotes).
Subsequent AAPL/GOOGL imports added longer history, and GOOGL Class A was added
separately from GOOG Class C for the requested portfolio. The two pre-existing
companies remain. This does not certify
company financials or maintain the ranking automatically. Do not substitute Indian banks' US ADRs
for their NSE shares. Preserve company reporting currencies, normally INR for
these Indian companies; USD portfolio reporting requires dated, sourced FX.

October 11 initially found only AAPL, PLTR and NVDA, with no stored CIKs. M04
verified the agreed identities against official SEC/NSE records and added nine
missing securities in Processing Run 19, filling only absent AAPL/NVDA fields.
All 11 scoped securities now have distinct catalog identities; PLTR is preserved.
GOOG/GOOGL retain their separate classes and common issuer. Runs 5-18 pass genuine
SEC/FRED/Gemini and 11-security price connectivity. Later runs 20-40 add 667
unreviewed SEC candidates, 196 FRED observations and 2,739 quote/history rows.
GOOGL's failed first price intake remains audited; retry 40 succeeded. The September imports remain historical;
the October 12 normal rollout includes this behavior. [M04 evidence](archive/checkpoints/2026/m04-ingestion-2026-10-11.md).

The October 11 [M05 inventory](archive/checkpoints/2026/m05-financial-evidence-2026-10-11.md)
records required annual sources and its dated coverage for all 11 securities:
667 unreviewed SEC candidates and no normalized histories or confirmed industry
mappings. Those counts are historical. The [October 13 source preparation](archive/checkpoints/2026/m05-source-review-preparation-2026-10-13.md)
provides ten company batches, three target years per issuer, independently selected
report rows and explicit accounting exceptions. Agent-prepared references are not
human-reviewed answer keys. The [October 17 follow-up](archive/checkpoints/2026/release-readiness-2026-10-17.md)
resolves the eight selected Airtel/SBI parser gaps. The October 18 delegated HDFC
review applies 56 unit corrections and promotes 64 selected source occurrences
into two normal historical periods. The later US review approves and applies 355
of 402 selected candidates into 18 periods across six securities. 47 selected
gaps and 265 older candidates remain unpromoted. The later [India review](archive/checkpoints/2026/india-financial-review-2026-10-18.md)
adds Reliance, Airtel, ICICI and SBI: 456 facts, 492 source revisions and 12 periods,
with 164 older comparative entries held. The [latest HDFC application](archive/checkpoints/2026/hdfc-latest-history-2026-10-22.md)
adds FY2026 and bonus-adjusted FY2025 comparatives. The normal database now has 33
periods, 929 facts, 1,003 revisions and 336 normalized values across 11 securities after the October 24 additions.
FY2024 stays pre-bonus; one FY2025 EPS exception, broader notes, merger comparability,
model bridges and weighted mappings remain explicit.
Certification v3 checks retained hashes, units, annual XBRL periods
and bounded PDF locators; these checks do not approve numeric interpretation,
bank model suitability or class-specific shares. Historical AAPL/APSEZ proof is
not proof of this normal database's current coverage.

| Needed | Current decision and remaining action |
|---|---|
| US company statements | Official SEC companyfacts populate latest-completed-annual draft suggestions with exact candidate/source/period/unit provenance, including additional cash-flow, payout, tax, equity and debt-component tags. Revisions append candidates without overwriting reviewed evidence. GOOG/GOOGL use separate security-linked snapshots for their shared issuer. All suggestions still require review; no normalized facts or saved models are auto-approved. Standard-tag coverage is not complete-statement certification. No paid SEC API key is required. [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) |
| India company statements | Official issuer reports retain exact statement/share-note locators. Parser v6 additionally separates explicit current/noncurrent investments while preserving bank investment labels. HDFC now adds FY2026/bonus-adjusted FY2025; FY2024 stays pre-bonus. Full notes, merger comparability, valuation bridges and automatic exchange discovery remain incomplete. Ambiguous fonts/columns stay rejected |
| Benchmark assumptions | Six January 5, 2026 versions per market now supply US/India priors with exact provenance. Seven provisional revenue mixes and four single-industry comparisons are recorded under delegation. Reliance net external-revenue weights remain unavailable. Multi-industry growth, ROE/ROC, financing totals and automatic beta/WACC are withheld without proper bases; sales/capital uses implied-capital aggregation. India WACC D10/D11 remain Global weighted averages, not verified country-specific risk. Missing/adjusted columns and small samples remain limitations; priors do not approve company forecasts |
| FRED and valuation automation | The supplied key passed real DGS10/NFCI imports September 22. Stored DGS10 percent values become a reviewed USD risk-free proxy with exact observation/date links; INR retains currency-matched benchmark methods. Weekday 07:00 New York refresh is configured, but its source worker is stopped with restart disabled. An owner can cancel a queued request without losing its audit; Apple run 42 was cancelled during verification. SEC/FRED/price steps are draft-only, with edits preserved; no external AI or saved-model recalculation. Daily Brief scheduling runs separately |
| Latest prices | `yfinance_personal` remains explicitly selected for personal use. October 11 probes and 365-day quote/history intake pass for all 11 scoped securities; one GOOGL failure and its successful retry remain separately audited. History excludes the current market-local date in America/New_York or Asia/Kolkata, including after close. This is a conservative prior-date policy, without an exchange holiday calendar or certified final-close status. Quote timestamps/delay remain unknown, older rows are not reclassified, and the October 12 normal rollout includes this behavior. [Provider usage notice](https://ranaroussi.github.io/yfinance/) |
| Google Sheets alternative | User accepts the up-to-20-minute quote delay. No bridge implemented or Sheet created; the functioning personal Yahoo adapter remains selected. GOOGLEFINANCE does not support most international exchanges; its historical values cannot be accessed through Sheets API or Apps Script. Never publish holdings to make a quote bridge work. [Google documentation](https://support.google.com/docs/answer/3093281?hl=en) |
| Additional API accounts | No paid account is needed for the verified personal-price/SEC/manual-source workflow. SEC contact and Gemini key are configured locally. The configured gemini-3.5-flash-lite passes real public-PDF triage with exact quote checks and pending review. Keys use headers, not URLs. Scanning a private upload sends its disclosed text to the provider; it does not send stored portfolio/model values. This does not certify interpretation quality or future quota. Paid real-time entitlements/coverage are separate choices. FMP is a stub. Never paste keys into chat |
| Assumed portfolio | The September 22 reference portfolio had 200 AAPL and 200 GOOGL shares purchased at January 2, 2024 unadjusted closes, rounded to USD cents: 185.64 and 138.17. Confirmed User Assumptions: initial deposit 64,762.00 USD, zero fees, no later trades, dividends excluded. Source price IDs, funding/trade notes and Processing Runs retain the basis. Two complete snapshots and period calculations were verified; this is a price-return model, not broker-verified executions or actual total return. This is historical reference evidence. The October normal database instead contains a labeled Mock Data portfolio; do not treat this row as its current holdings |
| Starbucks documents | Optional useful validation case. The offered files are not yet supplied in this exchange; SEC can be used without waiting for them. Do not label a fixture as Starbucks evidence |
| Review authority | Remaining research/demo financial, industry, model and interpretation choices may be reviewed under user delegation, with sources, rationale and affected records in the decision log. This is not independent human certification or a license for redistribution, prohibited scraping or professional use |

## What the Product Can Do

| Capability | State | Evidence boundary |
|---|---|---|
| Track companies and market identity | Built | Shared authenticated company catalog, setup workflow, aliases, source capabilities; not private company ownership |
| Store and inspect source documents | Built | Raw documents, sections, PDF assets, exact locators where available |
| Ingest SEC filings and RSS | Built when configured | SEC annual facts also have an opt-in source worker; filing discovery/RSS scheduling and provider constraints remain |
| Upload India filing PDFs | Built | Automated NSE/BSE discovery is incomplete |
| Extract and review financial candidates | Built | Review is required before promotion |
| Evaluate local text extraction | Built, narrow scope | Owner-scoped persisted reports compare an exact stored-text hash to a separately reviewed complete reference. Numeric/unit/period/locator failures remain visible; no PDF/XBRL/AI or forecast certification |
| Normalize and reconcile financial histories | Built for covered metrics | Broad issuer/layout certification remains incomplete |
| Extract events and deterministic scores | Built | Rule-based extraction can miss nuance |
| Review alerts and thesis impact | Built | Historical evidence precision varies |
| Track portfolios, transactions, cash, and prices | Built | No broker sync; provider freshness varies |
| Run multi-stage valuation workflows | Built | Output quality depends on reviewed assumptions and source definitions |
| Run reviewed-peer relative valuation | Built | Owner-scoped reviewed sets, normalized member and target-company revision evidence, exact diagnostic-warning acknowledgement receipts, retry-safe exact-hash v2 CSV round-trip with legacy support, provenance, median aggregation, and deterministic peer and target-relative warnings exist; facts are still supplied and reviewed by the user |
| Audit peer review receipt health | Built | Bounded owner-scoped Data Health pages report receipt state, evidence conflicts, and method coverage; direct links open the specific peer set in a standalone review workspace without requiring a DCF |
| Use Damodaran benchmark priors | Built for 24 active typed sources | 17 other mirrors have no typed rows; some loaded contracts also cover only part of their workbook. Every applied prior still requires review |
| Run research sessions and AI assistance | Partial | Exact-source review and approval gates exist; generated claims are not automatically factual |
| Search stored evidence | Built for registered corpus types | Documents/events/narratives and owned research/approved AI are covered; semantic truth and every possible source type are not implied |
| Generate a daily brief | Built with opt-in local scheduling | Deterministic scheduled generation exists; autonomous external AI and complete provider coverage do not |

## What Still Requires the User

The user reconfirmed on October 17 that no off-device backup destination or genuine
trade records are available, then explicitly chose research/demo v1. Do not request
real activity or deferred Mac/backup setup again as first-release prerequisites.
October 12 fixes local backup finalization, verifies complete format-3 normal
backups, rehearses recovery and installs the integrated normal runtime. No broad
macOS filesystem permission change is needed. Old partial folders remain
incomplete and preserved. Local folders and Mock Data tests cannot prove encrypted
off-device recovery, actual portfolio history, financial review or user acceptance.
The [dated follow-up](archive/checkpoints/2026/m03-m09-runtime-followup-2026-10-12.md) records the evidence.

### Ordered operator handoff

November 5 UTC: the user explicitly approved clearing all 12 US/Indian companies
and linked research, including the eleven historical scenarios, portfolio contents
and saved briefs. The guarded removal is complete; the portfolio account, settings,
shared sources, global references, original files and backups remain. The dated
company-specific review below describes historical evidence retained in backups
and source receipts, not active company rows. Do not repopulate it automatically.

November 4: finish independently actionable work, reconcile documentation and complete GitHub work. The user delegated
remaining research/demo choices and requested a retrospective record. The
[decision log](roadmaps/review-decisions.md) owns exact choices, sources and effects;
its register distinguishes five explicit Apple approvals and the eleven-scenario
approval from delegated agent review. PR3 and the disclosure follow-up PR4 are merged.
Do not ask for each financial/model decision again. Delegation supplies authority,
not missing facts, independent human certification or unperformed acceptance tests.
M05-AAPL-04A US/USD/FCFF is explicitly approved. M05-MAPPING-16 supersedes only
Apple's provisional mapping, retaining proxy alternatives and withholding invalid
ratio blends. Twelve audited January 2026 US/India versions are now loaded
in the normal database. The benchmark intakes did not change company financials or
saved valuations. The later HDFC review applies 64 selected source entries to two
March 31 periods, with 56 unit corrections, 60 distinct facts and eight normalized
values. Its [checkpoint](archive/checkpoints/2026/hdfc-reviewed-normalization-2026-10-18.md)
records separate runtime/browser proof. The later [US/AI review](archive/checkpoints/2026/us-financial-and-ai-review-2026-10-18.md)
applies 355 selected US facts and records semantic judgments. India Runs 106-121
apply the later four-company selection, with exact decisions and 16 financial/PDF
browser views. Broader financial/model gates remain open.
The personal-research US/India market scope and USD example reporting remain in force. Deferred
items below are retained for later use, not questions to repeat now. No subscription,
broker login or secret value in chat is required.

| Order / open checks | What the operator supplies or does | What the agent handles |
|---|---|---|
| 1. M03-04: Mac protection, deferred | Later: System Settings > Network > Firewall: turn on. Privacy & Security > FileVault: verify on or enable, retaining the recovery method outside this Mac. Confirm status only. Review General > Sharing and Users & Groups for unused remote access and unexpected administrator access; preserve a working administrator/recovery route | Retain the deferred status; no host-setting change now. Localhost bindings/auth remain in scope. Do not infer encryption from hardware |
| 2. M03-07 and recovery part of M03-04, deferred | Later: identify an encrypted external drive or private off-device destination for a separately encrypted archive, with its mounted folder/service and a recoverable key kept separately. Another folder on this Mac is insufficient | Preserve existing backups. When the user resumes this work, agree a safe separate restore target under the no-new-datasets constraint; never replace normal data. Record actual retrieval/restore proof and maintenance cadence |
| 3. M03-04: database credentials verified November 2 | Operator completed the private database-role/client change. No values were supplied in chat. Keep pgAdmin disabled until separately configured | The [verification](archive/checkpoints/2026/local-credential-rotation-2026-11-02.md) proves fresh authentication, old/wrong-password rejection, existing local sign-in, preserved images/volume/local ports and all 109 tables/assets. App-login/provider credentials are unchanged. Do not repeat this completed step. Retained old containers need current settings and schema review before reuse |
| 4. M05-03/04/05: financial review | The user approved all eleven named historical research scenarios on November 3; delegated source review remains authorized | [November 4 application](../data/reviews/disclosure-followup-20261104.json) retains 16 new official originals and 11 inactive dated notes. SBI Life/General/Funds/Card and Yes Bank closing award counts, ICICI AMC parent-share overlap, retail intragroup financing and selected Airtel ownership scopes are verified. Microsoft FAQ now succeeds, but its current wording does not establish a historical preferred balance. Complete claim valuation/settlement bridges, HDFC comparable pro-forma history and Reliance net external-revenue allocation remain unavailable. Preserve HDFC's EPS exception, Alphabet's USD1m lease exception and source-specific India treatments |
| 5. M06-04/07: valuation basis | The selected historical scenarios and discretionary reserves were explicitly approved; company-fact completeness and actual-use acceptance were not | All eleven models were independently reconciled and later removed from the active database by the approved November 5 cleanup; backups and source receipts remain. November 4 supplied no supported numerical replacement. Parent/child shares, future capacity, trust transfers, carrying proxies and discretionary reserves retain separate scope. Missing actual ESPP quantities, NCI balances and current award/claim values remain unknown. Alphabet's expense-based reserve has unquantified NCI/forecast overlap; Airtel's put-covered share population and corresponding NCI allocation remain incomplete. Microsoft preferred zero remains uncertain. Approved direct-rate and bank input handling in the software remains unchanged |
| 6. M07-05/06: demo check verified; genuine activity outside v1 | No records needed for research/demo v1. A later real-portfolio release needs a redacted ledger/export, opening/ending balances, dated activity/currencies, history start and benchmark; never broker passwords | October 18 verifies the existing examples against 64 independent arithmetic checks and six normal browser views. Partial risk, legacy/provisional returns and missing DCF/benchmark coverage remain. Genuine-activity and real multi-currency proof stay unperformed, not passed |
| 7. M08-04: interpretation review, verified October 18 | No additional review input is required for this selected set; the user can revisit decision M08-AI-REVIEW-20261018 | Six actual responses and four existing adversarial fixtures now have delegated semantic judgments. Four constrained summaries are accepted, unsupported regional-to-company directions are rejected, and the blocked response stays blocked. Original human fields remain blank. This selected set does not establish statistical accuracy or future injection resistance |

The [November browser audit](archive/checkpoints/2026/valuation-review-and-browser-audit-2026-11-02.md)
repairs observed code/UI defects using existing data. M09 acceptance still depends on preceding in-scope gates. Five
actual business days of research/demo use and final acceptance belong to M10. Its technical
preparation is now authorized. The user requested no more disposable datasets:
routine checks use existing data without resets or fabricated activity, and
the newly prepared populated-backup rehearsal stays unrun. The usage record
remains at zero days, confirmed by the user before the agent audit; agent tests do not count as actual user use. A gate closes
on recorded evidence, not a general "looks good."

Independent preparation is retained locally in
`output/milestones/operator-review-20261013/review-packet.html` and its hashed JSON
manifest. That October 13 inventory had 667 unreviewed candidates and no
normalized histories or confirmed industry mappings for the 11 securities.
The packet selects 402 stored SEC annual candidates for target years and includes
seven **Mock Data** AI cases with proposed, unapproved labels. Candidate rows are
not independent reference answers; the packet cannot authorize promotion and
must be refreshed after source/candidate changes. No provider call, normal write
or human approval occurred in that earlier preparation. That packet is superseded
for financial source review by
`output/milestones/m05/review-batches-20261013/review-packet.html`; its Mock Data AI
label review remains separate. Actual provider responses are now prepared in
`output/milestones/m08/interpretation-review-20261017/review-packet.html`. Five
responses pass source/format checks; one is blocked because comparison labels are
absent from its exact quote. The October 18 sidecar review rejects unsupported
regional-to-company valuation mappings and records the other delegated judgments.
All original human verdicts remain blank. The financial packet retains official originals and
source hashes, report/candidate comparisons, earlier comparative versions and
blank per-company decisions. That preparation rechecked versions read-only and did
not change normal financial values. Acquisition Processing Runs 47-88 were added,
so this follow-up is not an unchanged-database claim. Source rows/derived totals
remain agent-prepared, not a complete approved reference. Mac settings and the
backup destination are deferred by the user; independent M05 work continues.

The legacy `scripts/evaluate_financial_extraction.py` entry point previously
compared reference values with themselves. Its repository version now exits
unavailable and directs users to the actual Evaluation Lab; one regression test
first failed on the stub, then all 57 repository checks passed. This is a host
tooling correction, not a new normal-runtime rollout. Do not run inherited copies
of the retired command in older images or use its historical scores as evidence.

## What Is Not Product-Ready

| Gap | Consequence |
|---|---|
| Public deployment security | Keep the app on localhost |
| Local-only runtime boundary | Normal and E2E Compose bind published ports to 127.0.0.1, protected by regression checks. September 30 rollout verifies non-root backend/workers/frontend, dropped capabilities, no-new-privileges, memory/process limits and local port bindings. This does not establish public-deployment security or fully audit host forwarding rules |
| Backup verification scope | October 12 format 3 adds an atomic manifest-bound COMPLETE marker without directory rename. Missing/corrupt/linked markers block restore before writes; payload/checksum flushing is not a full power-loss guarantee. Verified format 2 stays readable. Evidence comes from a restored completed dump, covering every table fingerprint and both PDF stores during concurrent writes. The normal Compose backup command and a 109-table disposable restore pass. Same-disk folders are not encrypted off-device recovery; no destination/key-recovery plan exists |
| Disposable verification cleanup | October 17 removes this pass's six stopped temporary test registrations and two networks after the user requests no more disposable datasets. Future routine checks use existing data; remote CI remains isolated. Only four normal services run, around 618 MiB across three samples with low CPU in two and a brief 31.33% one-core-scale spike in the third. Unused build cache older than 24 hours reclaimed 2.567GB; the Mac reports 27Gi available. Images/cache share layers, so category sizes are not additive. Backups, rollback images, persistent volumes and failed evidence remain preserved. |
| Production India provider coverage | India workflows remain manual/partial |
| Broker integration | Portfolio activity must be entered/imported manually |
| Real-time data | Do not infer trading-grade freshness |
| Automated market-regime feeds | Manual/provider input workflow exists, but automated module coverage is not configured |
| Fully automatic statements | Draft suggestions are automated, not source approval. Standard annual US-GAAP tags cannot fill every issuer's custom disclosures, consolidated/class-specific shares, option value, cross-holdings, complete working-capital/debt cash flows or special-case forecasts. Missing values remain unavailable or explicitly marked placeholders, not inferred zero facts |
| Draft unit/model review | Explicit source scales now convert to full currency amounts/shares with conversion provenance. Unknown units and currency mismatches withhold suggestions; no inferred FX or source-fact rewrite. Growth forecasts, positive lease treatment and model-specific bank/distress inputs require review. November selected reviews persist exact source-packet references; missing awards/dilution remain null. Review-only saves preserve scenario/horizon/method. Version checks and working controls do not establish complete company valuation evidence |
| Forecast calendar basis | Calculations and APIs use relative periods. Calendar years are null without a fiscal anchor; legacy stored integers are withheld on reads without rewriting amounts. The nullable-column migration preserves all rows. Old integer-only images are incompatible with new null rows; do not force a downgrade |
| M05 real-report extraction and reconciliation | Selected histories and accounting notes remain separate from complete valuation inputs. The [October 24 review](archive/checkpoints/2026/m05-m06-ui-and-financing-2026-10-24.md) verifies financing/cash/lease definitions and adds 23 sourced NVIDIA/Alphabet/Microsoft borrowing facts. Alphabet's USD1m lease discrepancy, six face-value totals and NVIDIA's unsupported FY2024 commercial-paper zero remain unresolved. Historical carrying amounts do not establish current market debt. Recurring parent earnings, current awards, merger comparability, bank distributable capital, valuation-date bridges and Reliance net external-revenue weights remain open. Failed audits and source packets are retained |
| Historical normalization and repeated evidence | New normalization requires explicit inputs, matching units and valid denominators; it does not repair old saved outputs automatically. The HDFC run retains every source occurrence; four redundant canonical projections created by that run were removed with exact reversible receipts. Earlier occurrence revision-number metadata remains as recorded. New promotion sequences repeated occurrences, supersedes all old active occurrences and blocks conflicting values. October 22 repairs only two old FY2025 active flags, with values and revision numbers retained. Normalized provenance now requires the current revision and matching promoted source; ambiguity is unavailable. Normalization/currency checks and comparable-metric reconciliation do not certify complete valuation inputs |
| FRED revisions | New dates import automatically; changed values for already stored dates are flagged `FRED_OBSERVATION_REVISION_REQUIRES_REVIEW`, not silently rewritten. Full vintage/revision storage remains open. DGS10 is a reviewed USD methodology proxy, not a universally appropriate discount rate |
| Scheduled source refresh | One attempt per local weekday after 07:00, no missed-date backfill or automatic failure retry. Explicit retry is available. Queue status is persisted, but there is no dedicated heartbeat/notification transport; inspect the draft or Data Health when a job stays queued. Configuration remains local `.env`, not a general schedule editor |
| SEC scale and component scope | Full-currency/full-share candidates never fill gaps in an existing reviewed million-scale annual basis. Legacy v2 long-term-only debt candidates are excluded from automatic drafts and receive a scope warning on refresh; prior reviewed historical facts are not rewritten. Current/noncurrent component sums require matching source bases/units and explicit review. Missing total borrowing coverage, lease treatment and issuer/class share reconciliation remain analyst work |
| SEC download resource bounds | Companyfacts uses a fixed official HTTPS host, public DNS pinning, no redirects, a 32 MiB response limit, 20-second I/O timeout and a 60-second elapsed check between chunks. Current and legacy HTTP intake share the bounded candidate-review workflow; the old fetch import delegates to it. Oversized/invalid/wrong-issuer payloads fail before candidates. DNS/connection and in-flight reads are not a strict 60-second cancellation guarantee. Installed in the October 12 normal rollout. |
| Adjusted industry margins | Unadjusted EBIT and EBITDA are no longer mislabeled as lease/R&D-adjusted operating margins. The typed margin contract does not expose those adjusted source columns; adjusted-prior fields remain unavailable until separately mapped and tested |
| Evaluation scope and reference quality | The financial text executor now runs and stores scores, but its existing extractor misses units. Missing units count as errors, even when the number matches. Reference completeness/correctness and genuine/mock classification are reviewer assertions. Other evaluation domains and forecast calibration remain incomplete; historical unowned runs are preserved but not exposed to arbitrary users |
| Fully cited AI research | Event interpretation retains bounded schema, source/model/prompt/input provenance, explicit disclosure and prohibited-language checks. Actual Gemini transport is tested with mocked HTTP. Narrative estimates are typed/bounded before successful audit, preserve zeros and never change saved assumptions automatically. Saved valuation basis survives review/evaluation updates. These checks do not certify economic meaning, live-provider availability or human interpretation quality |
| Private source triage scope | Text/PDF inbox produces exact-quote-checked AI suggestions for 14 valuation fields. M08 source adds bounded as-generated private context to manual/scheduled deterministic briefs, with separate reviewed and pending queues. It does not certify materiality, infer numeric forecast edits, approve facts, rewrite models or add private sources to global search. Original source editing remains absent; the October 12 normal rollout includes the supported workflow |
| Private source lifecycle | Archive/restore is owner-scoped, version-checked and reversible. Active sources are the default; archived originals and findings remain inspectable. Duplicate imports do not restore them. Running scans block archiving for two minutes; expired attempts can be abandoned, and late success/failure cannot overwrite a newer state. Archiving neither deletes nor approves evidence. No bulk archive, permanent deletion, full organization-event history or storage-space reclamation is provided |
| Multi-source comparison | Comparison v2 remains bounded to 50 active sources, with exact passages and immutable analyst receipts. Quoted period/currency/economic-scope labels are same, unknown or incompatible; labels do not establish economic equivalence or semantic contradiction. Old v1 receipts remain readable but stale. Whole-company hashes conservatively invalidate reviews after any bounded evidence change. Literal-copy detection is not paraphrase detection or independent corroboration |
| Private brief snapshot coverage | M08 source includes at most ten active-source companies, twenty distinct contents and thirty decisions, with disclosed exclusions. Current receipts plus approved AI can enter reviewed context; pending/stale/incompatible/truncated evidence stays separate. Foreign, future, rejected, archived and Mock Data sources are excluded. Saved briefs remain as generated, not continuously revalidated. Six SQL queries per one-company snapshot, at most 42 for ten companies; no original PDF/text bodies or external AI calls. Human interpretation-quality evaluation remains open. A recorded official Apple source passes the dashboard-to-evidence-to-thesis-to-saved-input morning browser chain, with synthetic holdings/forecasts clearly separated. That browser chain does not persist a new brief; separate due-cycle tests verify one audited immutable snapshot. Neither closes genuine portfolio or financial acceptance |
| Public brief coverage and dashboard provenance | November 4 source adds versioned eligible/included/excluded counts, windows and cap reasons: generated briefs select at most 50 events, ten failed runs and twenty derived actions; dashboard previews ten events and failures from its twenty recent runs. Explicit source metadata fixes dashboard parity without loading document bodies. Unknown historical coverage remains unknown, not backfilled. Counts cover stored records and actions derived from included inputs, not complete provider ingestion or independently verified claims. Manual refresh and scheduled assembly are deterministic; broad semantic quality remains separate |
| Private source retrieval | Owner-scoped, case-insensitive literal phrase search covers titles and stored source text, with company, format and scan-state filters. Cursor pages expose older sources beyond the default 20 without loading original bodies into list responses. PDFs cover only their extracted pages; AI findings are not search text. Scan completion is not human approval. This is not semantic search, OCR, a full-text index or large-corpus performance certification |
| Research PDF coverage | 12 MB, 20 selected pages and 60,000 extracted characters per source; larger reports need selected pages. Source code now isolates extraction/previews in CPU/memory/time-limited Linux child processes. No OCR, chart interpretation, malware disarm or visual financial-table reconciliation. See the M03 security checkpoint for validation and rollout scope |
| Company business descriptions | Cards show bounded parser-selected annual Item 1 excerpts, with source dates/links, not live curated profiles. AAPL and GOOGL annual sections were imported on September 22; broader company/India coverage remains incomplete |
| AAPL demonstration scope | September 22 non-saving Quick Valuation run uses FY2025 reported inputs and explicit assistant-selected estimates. It is not an approved current valuation: no fiscal roll-forward, accounting normalization, market-debt/option analysis or forecast review. The result does not establish trusted portfolio DCF coverage |
| Complete frontend parity | Stored quotes retain currency, timestamp, provider and unknown delay and say Available. Failed transport differs from empty/stale coverage. Financial panels retain units/period/review limits; empty reconciliation is neutral. Retained forms preserve failed edits, mobile controls fit their cards, and the normal installed workflow checks pass. Source facts and unmounted legacy callers still require separate proof |
| Genuine-input portfolio proof | October 18 verifies the existing three-holding/22-snapshot examples under the revised demo scope; no portfolio record changed. 64 independent value/risk/return checks and six browser views pass. This does not certify actual activity. Genuine-input readiness remains blocked for missing real activity, foreign exposure/dated FX, benchmark and trusted DCF evidence, outside this first release. Do not invent inputs to clear it |
| Historical holdings reconstruction | M07 source replays dated recorded buys/sales, funding, cash fees/taxes/dividends and explicit split/bonus activity, with purchase-date FX and current balance reconciliation. Missing opening balances, negative cash, oversells, ambiguous identities, unsupported adjustments or more than 20,000 rows prevent complete history. Same-day order is record ID, not verified execution/settlement time. Recorded activity is not broker verification; the October 12 normal rollout includes this behavior. See the [M07 checkpoint](archive/checkpoints/2026/m07-portfolio-replay-2026-10-11.md) |
| Issuer versus security identity | Company.cik remains unique, conflating issuer and listed security. A tested explicit regulatory_id fallback now imports GOOG/GOOGL shared-issuer SEC evidence into distinct security-linked snapshots; their prices remain separate. A dedicated issuer/security model and class-share reconciliation are still needed; issuer weighted-average shares are not automatically class-specific shares |
| Ownership audit scope | Price-divergence reads/deduplication/impacts use the requesting owner. Event-driven valuation alerts derive the model owner and validate company/change-log relationships. Portfolio calculations derive DCF/thesis/alert context from the persisted portfolio owner and reject mismatched explicit callers. Regression tests cover these paths; this is not full multi-user security certification or a rewrite of historical alerts |
| Risk comparison freshness | Prices older than five calendar days withhold current DCF gaps in both portfolio consumers. Saved cash-flow currency and finite quality/value are required; missing currency cannot fall back to today's company metadata. Risk matches both return interval endpoints and cannot bridge missing interior FX. Incomplete alignment and stale FX remain partial. Independent covariance/marginal/component references pass, but annualization still assumes 252 periods without exchange-calendar certification. Mock identity stays visible. No genuine-input or economic-model review is implied |
| Historical portfolio basis | New snapshots retain replay method, activity/hash and FX provenance; legacy/manual snapshots remain replay-unverified. Later corrections make dependent reads provisional without rewriting history. October 18 verifies existing period TWR and since-first-cash-flow annualized MWR while retaining those warnings. Risk is fixed-weight price return: two current mixed-adjustment histories remain excluded, and historical unmatched intervals preserve partial status. This does not certify source authenticity or realized total return |
| Automated comparable-company data | Peer values and sources must be entered manually; no licensed provider verifies or refreshes them |
| Legacy CSV receipt boundary | Imports created before migration `n5n5n5n5n5n5` have no provable original-file receipt; the first retry of such an old file can create one additional tracked Draft, after which exact retries are idempotent |
| Legacy peer review receipts | Reviews created before migration `o6o6o6o6o6o6` have no diagnostic acknowledgement receipt and cannot drive relative valuation until the current warnings are explicitly re-acknowledged; the normal database contained no peer sets when this migration was applied |
| Diagnostic receipt semantics | A current receipt proves that the displayed deterministic warning categories were acknowledged for one diagnostic snapshot; it does not prove the underlying facts, economic comparability, source correctness, or reviewer diligence, and time-sensitive freshness changes can require re-acknowledgement |
| Receipt-health timing | Data Health recomputes receipt status when the page is requested; it is not a background monitor and cannot automatically re-acknowledge a stale or missing receipt |
| Receipt audit scope | Each response checks at most 100 sets (UI: 50) and reports page-local counts plus the total owned count. Cursor pages are live reads, not one immutable snapshot. Refresh from the first page after changes; a current receipt alone does not establish method coverage or valid company financial inputs |
| Relative valuation numeric contract | Finite input validation and overflow guards prevent invalid numeric responses, but do not validate currency/unit consistency or source accuracy. Supplied cash/debt must be nonnegative and supplied shares positive; losses remain valid inputs but may leave a multiple method unavailable |
| Relative valuation refresh boundary | Superseded browser requests cannot restore old options, results, or errors. Refresh failures clear usable peer evidence and block calculation until retry succeeds. Requests are logically invalidated, not transport-aborted; remote edits still require refresh and are independently checked by the backend when calculating |
| Saved relative-input evidence | Zero preservation, book equity mapping, server-derived EBIT, owned input reads, exact-hash calculation, and input disclosure are implemented. These values are still saved User Assumptions, not verified company actuals. EBITDA remains unavailable because the saved depreciation field does not establish complete D&A; unsaved form edits are excluded |
| Saved relative-input units and bridge | Users must confirm consistent currency and monetary/share scales plus the simplified enterprise value minus debt plus cash bridge. That confirmation is not independent verification. Nonzero leases, cross-holdings, minority interests, preferred stock, and employee options are disclosed as omitted adjustments, not included in this bridge; the direct custom-financial API remains available under its existing contract |
| DCF implied-pricing evidence | New calculations and historical API reads use saved net income for P/E, saved book equity for P/B, and explicit revenue/margin for sales and EBIT ratios. EBITDA is unavailable without complete D&A evidence. Ratios are Calculations from User Assumptions, not verified earnings or market multiples; currency, scale and source accuracy still require review |
| Historical DCF storage | Reconciled reads replace legacy pricing ratios and structured pricing warnings in responses only. They do not rewrite stored outputs, rerun the DCF, or recalculate its historical quality score. Untyped legacy string warnings cannot safely be classified and remain preserved. Contextless output reads hide ratios |
| Saved output-card evidence | Headline, supplementary and multi-method values now share stale/invalid/critical, identity, currency and finite-value display gates. Saved prices are User Assumptions, not live Market Facts. Stored diagnostic scores remain historical and are never synthesized in the browser. These UI gates do not independently verify sources or replace backend enforcement in other consumers |
| Scenario evidence | Scenarios retain the owned model type and zero assumptions, reject stale/invalid saved inputs, and expose per-scenario diagnostics, saved currency and backend price gaps. Deterministic shocks are not probabilities or forecasts; missing optional assumptions can still trigger existing engine defaults. Requests are logically invalidated, not transport-aborted |
| Reverse DCF evidence | Source requires explicit positive comparison price, valid saved inputs/currency/diagnostics and actual convergence, without price-100 or one-share fallbacks. FCFF/distressed dispatch and result identity checks are implemented; financial-services reverse analysis is unsupported. Bounded bisection does not prove uniqueness or find every possible root. Prices/shares remain User Assumptions; request cancellation is logical, not transport abortion. Focused FCFF browser convergence, unreachable-target and delayed-response checks pass with Mock Data, not genuine-input certification |
| Saved-input version preservation | Both UI callers send the saved basis ID/time; the server merges omitted fields, preserves explicit clears/zeros and rejects outdated bases. Common book equity and saved horizon controls are implemented. Actual advanced-form resaves and five competing PostgreSQL writer pairs pass on disposable fixtures, including visible stale-form rejection. Prior versions remain intact; full API creations without a basis retain legacy behavior. The legacy form caller has source/test coverage, not separate mounted-browser proof |
| Core DCF zero/default semantics | Core FCFF forecasts, terminal values, sensitivity inputs/centers and related diagnostics now distinguish explicit zero from missing values. Zero shares and sales-to-capital remain invalid and diagnosed; a zero projection horizon is rejected. Existing missing-value presets remain, including the internal one-share fallback when shares are absent, which must remain blocked by diagnostics/display gates. Existing saved outputs are not rewritten or recalculated by this code change |
| FCFE/DDM method boundary | New calculations use explicit cost of equity, growth and positive shares, never WACC or missing-value presets. FCFE needs all six cash-flow components, including explicit zeros. Missing, invalid, nonfinite, negative-cash-flow or non-convergent inputs make that supplementary estimate unavailable with watch diagnostics, not a blocked core FCFF value. These are single-stage stable-growth estimates from current cash flow, not multi-stage forecasts or proof of sustainable payouts. A zero dividend estimate assumes zero dividends continue; it does not imply the company has no economic value |
| FCFE/DDM historical and consumer boundary | Existing saved supplementary values and historical scores are not recalculated or rewritten; resave to apply corrected math. Scenario operating-growth/margin and WACC shocks do not automatically change the explicit equity cash-flow/rate inputs. Currency, monetary scale, sustainable period, dilution and source correctness remain user-reviewed. Older unmounted dcf-form.tsx still has truthiness/dollar formatting; the advanced workspace uses shared zero-aware output cards and currency-aware payout labels |
| Payout completeness | Net cash returned is unavailable without finite explicit dividends, buybacks and issuance inputs. Comparisons no longer substitute missing components or assert actual funding, stock-compensation causation or value destruction. This is calculation-level protection, not comprehensive nonfinite validation across every legacy write contract |
| Financial-services model boundary | New excess-return calculations require explicit finite positive book equity/shares, finite net income/target ROE/cost of equity/growth and a 1-30 year horizon. Explicit zeros survive, nonconvergent/overflowing results are unavailable with blocking diagnostics, and enterprise value is not fabricated. This is a simplified linear ROE fade with constant book-equity growth, not a regulatory-capital/payout forecast. The workspace and scenario display validate equity inputs without requiring irrelevant FCFF fields; the saved projection view labels equity meanings. Persisted legacy projection field names remain unchanged |
| Distressed model boundary | New calculations require explicit probability, nonnegative common-equity recovery and positive shares. Gaps and the bridge include the final probability-weighted equity, including lease/cross-holding adjustments. Recovery currency/scale and treatment after senior claims remain user assertions; this batch does not introduce an independent recovery-review receipt. Base forecasts/terminal amounts remain conditional on survival, not an adjusted-value decomposition. Unadjusted supplementary FCFE/DDM and FCFF sensitivity tables are unavailable rather than displayed as distressed estimates |
| Specialized historical/UI boundary | Historical outputs, diagnostics and sensitivities are not recalculated on read; save a new version to apply repairs. The advanced form no longer presets ROE/failure/recovery or missing operating growth/tax/reinvestment inputs, and recovery explicitly means total common equity after senior claims in the saved currency/scale. Financial-services scenarios shock equity inputs; FCFF/distressed operating shocks retain existing meanings. Saved projections show relative Year 1 onward. The nullable-calendar migration is delivered: new periods store null and reads withhold legacy unanchored calendar years without rewriting historical rows. The fixed-2024 defect is resolved; reviewed fiscal-anchor support is not implied |
| Sensitivity method boundary | Canonical FCFF v2 reuses saved forecast/bridge behavior, preserves saved funding and terminal-ROIC overrides, and records per-cell validity and method/input identity. Independent cases cover center equality, zero/missing/negative inputs, shares and nonconvergence. Historical legacy grids stay visibly unverified until a new calculation; unsupported specialized sensitivities remain unavailable |
| Real Options saved-basis boundary | The panel now uses owned, timestamp-checked FCFF inputs/output, saved currency and shares, and backend total-equity integration before per-share conversion. Stale/critical/invalid bases are rejected; zero exclusivity and already-counted value add nothing. Independent-form, delayed-response and failure/retry checks pass with INR Mock Data. Requests are logically invalidated, not transport-aborted; remote edits still require refresh |
| Real Options judgment and persistence | The panel and saved service label this supplemental analysis experimental. All seven eligibility criteria and the incremental common-equity/currency/scale basis require explicit user confirmation, not independent verification. Generic enterprise/project option values cannot automatically be added to equity. Black-Scholes and exclusivity scaling are simplified assumptions. Inputs/results are not persisted, unsaved DCF edits are excluded, and distressed/financial-services integration is unavailable |
| Legacy Real Options compatibility | Direct custom-base calculation and scored-eligibility endpoints remain compatible, with OpenAPI deprecation and explicit experimental source/warnings; they do not enforce the new saved-basis ownership/confirmation contract and are not used by the panel. Their legacy delta omits yield discounting and is not displayed by the new panel. This batch does not certify those legacy outputs |
| Save confirmation lifecycle | Resolved for the mounted advanced workspace: only its versioned form resets after refresh, so the success notice and selected section survive. A disposable browser save persisted the changed payout inputs and retained the confirmation. This does not certify every legacy form caller |
| Host backend test runtime | Local Python environments lack pytest. Use the maintained network-disabled test Compose with disposable SQLite; do not substitute normal database settings. Focused PostgreSQL/browser proof is recorded separately |
| Responsive coverage | October 13 covers all 50 pages plus populated/India/loading states at desktop/mobile widths. Manual review of core/detail screenshots repaired narrow fields, clipped actions, invisible controls, false success/live labels and event-AI width. Final risk cards distinguish TWR period from annualized MWR and use returned dates. Keyboard/table checks and automatic A/AA scans pass; inconclusive contrast stays recorded. This is not full screen-reader or every-possible-state certification |
| Latest browser recovery proof | Missing and stale peer receipts pass browser recovery through Data Health and exact persisted acknowledgement checks. Private-source recovery covers duplicate/archive/restore, retained history, delayed/failed scan retries and stale comparison saves; original bodies stay immutable. The final integrated suite passes after the retained v5 timeout failure. This does not certify genuine peer facts |
| Peer comparability analytics | Market-cap comparisons are now limited to matching stated currencies and expose skipped coverage; other currency, accounting, fiscal-period, growth, margin, freshness, coverage, and dispersion differences are flagged, but the system does not fetch FX for peer normalization, normalize accounting, weight peers, verify facts, or claim a calibrated comparability score |
| Native frontend production build | Tests and TypeScript pass locally, but the recorded host dependency tree lacks the optional macOS ARM SWC binary. Docker remains the supported gate. September 22 final-source builds used verified cached Node 24/dependency images with matching package/lock hashes after Docker Hub metadata timed out; no dependency or authentication shortcuts were introduced |

## Reliability Baseline

For current source/build/browser validation, use [Current State](00-current-state.md).
Do not treat older fixture or reference-source records as verified normal-database
contents. The September 9 architecture refactor did not seed user data. The
September 21 user-authorized setup added the explicitly assumed portfolio and
sourced histories without rewriting existing valuation outputs.

- The preceding valuation task's deployment and focused browser evidence is
  archived in the [output/scenario checkpoint](archive/checkpoints/2026/output-scenario-integrity-checkpoint-2026-09-09.md).
- Exact evidence, ownership, response contracts, valuation math, migrations,
  Damodaran versioning, and representative source workflows have targeted tests.
- All active page entry points have isolated browser coverage; current state/control and normal-runtime proof retain the exact boundaries in the checkpoint.
- A passing build does not prove live providers, credentials, or source freshness.

## AI Boundary

AI may summarize, propose, compare, and draft. It must not silently create trusted
facts, overwrite reviewed assumptions, or issue buy/sell recommendations. Store
provider/model, prompt version, source links, generation time, limitations,
confidence, and review status. Private portfolio or thesis data must not leave
the local boundary without an explicit feature and disclosure. Schema validation
proves bounded shape/numeric admissibility, not economic meaning. Feature-specific
event-title/description and narrative/saved-assumption transfers remain disclosed;
provider confidence and exact citations are not human approval.

External AI requires both feature-specific acknowledgement and a current persisted
owner/provider/action grant. Settings records append-only grant/refusal/revocation
history, exact disclosure scope and optimistic revisions. The executor checks
again immediately before each send; missing, outdated, refused or revoked consent
blocks it. New external outputs link to the precise grant, including failed
dispatched requests. No historical output or migration creates permission.
The ten current Gemini actions disclose their actual data classes, including
research-chat document excerpts. Actual Mock Data generation stays local; dormant
internal AI helpers cannot acquire grants. The separate operator-only connection
probe sends fixed non-private text. Revocation cannot recall transmitted data or
cancel a request already dispatched. Source/citation checks still do not certify
interpretation quality. [Priority 6](roadmaps/product-roadmap.md#priority-6-source-backed-ai-research-review-foundation-delivered-quality-open)
owns later research-quality work; this implementation does not grant any real user access.

## Valuation Boundary

The deterministic engines are serious, but a mathematically correct model can
still be economically wrong. Review starting financials, accounting adjustments,
growth, margins, reinvestment, WACC, terminal assumptions, equity bridge,
currency, diluted shares, and source comparability. Industry data is a prior,
not a company fact.

Reviewed peer sets are a controlled user assertion, not independently verified
market data. Each member requires source metadata and every method requires at
least three positive included observations. Review makes the selected evidence
eligible for calculation; it does not prove economic comparability, consistent
accounting, aligned fiscal periods, or source accuracy.
Review eligibility now also requires a stored SHA-256 receipt for the exact
diagnostic snapshot and warning-code inventory displayed to the reviewer. A stale
hash or incomplete warning set cannot be accepted. Editing or restoring a set
clears the receipt, and time-sensitive diagnostic changes make the prior receipt
stale until the current warnings are re-acknowledged. Immutable revisions retain
the receipt that applied at each review.
Optional comparability facts produce deterministic warnings only. CSV preview
never writes, exact-hash apply creates Draft evidence, and export preserves the
stored sources.
An optional target-company profile now carries its own source, date, claim type,
and comparability facts. It is versioned and storage-audited separately from peer
members. CSV v2 round-trips that profile, requires identical target columns on
each peer row, and visibly accepts legacy member-only files. Missing target facts
remain a warning, not an excuse to infer them.

Peer CSV parsing is bounded to 1 MB of UTF-8 content and 50 peer rows. Malformed
quotes, inconsistent row widths, NUL bytes, non-finite numeric cells, and invalid
create metadata block apply. Numeric error messages do not echo uploaded cells.
Conflicting normalized/JSON evidence blocks export. Browser file reads enforce
size and encoding checks and clear stale previews before new requests.
Exact-file apply is idempotent within one owner and target company. Reuse does
not reactivate an archived set or reset later edits, and the UI identifies the
existing version returned. Hash identity covers the UTF-8 request content; a
client that changes line endings or other bytes has created a different import.

Peer market-cap dispersion is calculated separately for each stated currency.
Target market cap is compared only with peers using the target currency. Missing,
invalid, and cross-currency amounts are excluded with explicit identifiers and
counts. This prevents raw cross-currency comparisons but is not FX normalization:
the application does not translate market caps to a common as-of currency, prove
that source timestamps align, or independently verify the supplied amounts.

The January 2026 benchmark workbooks seed risk-free rates, ERP, beta, cost of
debt, capital weights, WACC, tax, growth, and financing-policy context with
version/hash/cell provenance. They do not contain company starting financials,
bridge values, shares, market price, or payout facts. The September 22 source
pipeline adds SEC annual draft suggestions and original-date stored quotes while
keeping all financial candidates unapproved. Drafts now have source suggestions,
but trusted financial facts still require matching sources, review and normalization.
Forecast growth, target margins, terminal growth/returns, distress probability,
recovery and employee-option value are judgments or separate evidence, not values
that can honestly be filled by a macro API or an industry workbook.

## Data Boundary

- Audited AAPL FY2022-FY2025 and APSEZ FY2023-FY2025 reference histories cover
  representative real-source extraction paths, not the normal database's contents
  or certification of the newly imported five-company review queue.
- Manual prices and explicit personal-use Yahoo data must remain labeled.
- Damodaran generic workbook inventory is not the same as typed application support.
- Historical source rows without provable versions remain excluded from active reads.

## Security Boundary

Company and source catalogs are shared authenticated data, not private tenant
records. The September 30 security review covers code, dependencies, request and
outbound boundaries, containers, secrets handling, AI/privacy and recovery. It is
not an independent penetration test or host-compromise assessment. Framework
OpenAPI/docs routes remain outside the three-route public APIRoute allowlist.

Fixed in source: known package advisories in the scanned dependency sets,
unused JWT/OAuth libraries, global token-storage writes, permissive proxy headers,
missing same-origin mutation checks, unbounded request bodies, unsafe DNS handling,
RSS/filing download limits, workbook expansion and RSS entity risks. Backend and
workers now use an unprivileged account; web/workers drop Linux capabilities and
set resource limits. Local `.env` permissions are 0600; new backups use umask 077.
The [security checkpoint](archive/checkpoints/2026/security-and-comparison-reviews-2026-09-30.md)
records verification and scope. No clean scanner result proves absence of bugs.

| Priority / area | Remaining limitation and safe next action |
|---|---|
| High: host and local administration | October 17: firewall reports disabled; FileVault status could not be determined (the status tool could not identify the volume). This host work remains deferred for research/demo v1. Later operator steps: System Settings > Network > Firewall > On; Privacy & Security > FileVault, verify or enable with a privately retained recovery method. See [Apple firewall guidance](https://support.apple.com/guide/mac-help/mh11783/mac) and [FileVault guidance](https://support.apple.com/guide/mac-help/mh11785/mac). Docker sharing/account privacy remain uncertified. November 2 verifies coordinated PostgreSQL credential rotation; optional pgAdmin stays stopped until separately configured. Published ports remain localhost-only |
| High: recovery and confidentiality | Local restore rehearsal protects against migration loss, not stolen disks or simultaneous device/backup loss. Dumps contain private documents, AI evidence and portfolio data and are not application-encrypted. Arrange encrypted off-device backups and a restore drill; keep environment/key recovery separate |
| High before public use | No public release: production identity/MFA, broader authorization testing, TLS, strict CORS/CSRF design, persistent per-user/operation throttles, security logging/alerting, least-privilege DB roles and explicit OpenAPI exposure decisions are still needed. Current login limits are per-process; backend defaults are per-path/IP and browser requests share the proxy IP |
| Medium: untrusted parsers and availability | M03 source isolates four PDF operations in Linux children with CPU, address-space, output, wall-time and concurrency limits and sanitized errors. This is not an arbitrary-code/filesystem sandbox, malware scanner or comprehensive hostile-parser/load certification. A malicious local account can still exhaust disk/resources. Installed in the October 12 normal rollout. |
| Medium: outbound clients | SEC metadata/companyfacts share the DNS-pinned RSS/filing transport. FRED/Alpha Vantage/Gemini bound responses and reject redirects/proxies/compression; query keys stay out of HTTPX URL logs. M04 bounds yfinance in disposable Linux children with no app secrets or proxy environment, but does not independently allowlist every SDK endpoint or sandbox filesystem/native-code access. Fixed-host clients rely on verified TLS and normal DNS. Strict rejection/pinning can reduce availability; failures stay explicit. Installed in the October 12 normal rollout. |
| Medium: browser policy and secrets | Basic CSP/frame/type/referrer protections are enabled, not a nonce-based strict script policy. Secret scanning is heuristic over the working tree, not a full-history or credential-revocation audit. Provider keys were not printed or rotated. Database credentials were privately rotated by the operator and verified without emitting values; protected-file contents/current permissions were not inspected. Legacy global OAuth storage is disabled, not a broker integration |
| Medium: supply chain | Hash-locked backend transitives, pinned image/CI references and signed dated OS updates remain. The [October 28 rollout](archive/checkpoints/2026/locked-build-and-local-rollout-2026-10-28.md) fixes the two OpenSSL package findings and passes that dated available HIGH/CRITICAL-fix gate for all three supported images. PR2, PR3 and [PR4](https://github.com/Gittastic112/Marketagent/pull/4) are merged; PR4 has five passing remote jobs. The [November 4 completion checkpoint](archive/checkpoints/2026/independent-completion-2026-11-04.md) owns the subsequent release evidence. Unfixed findings remain, including PostgreSQL libxml2 CVE-2026-6653 (scanner critical, Debian minor/no-DSA) and the frontend zlib/MiniZip flag (Debian's built binary unaffected). Neither is suppressed. Optional stopped pgAdmin and host Docker require a separate upgrade assessment; scanners cannot establish exploitability or completeness |
| AI and research integrity | Provider output and source text remain untrusted. Automated Evaluation v3 reports citation/policy checks, not semantic truth. A separate October 18 delegated review judges six saved actual responses and four adversarial fixtures, rejecting unsupported mappings and all four misleading fixture interpretations despite valid citations. Human fields stay unchanged. This is a selected review set, not statistical accuracy or future live-provider injection-resistance proof. Explicit scans disclose source transmission; ordinary review/browser reads make no provider call |

Local credential authentication and owner scoping reduce accidental cross-user
access, but they do not make the application safe for the public internet. Public
deployment requires production identity, authorization review, HTTPS, CSRF and
CORS hardening, rate limits, secret management, backups, privacy controls, and
audit logging.

## Architecture Follow-ups

Documentation audit boundary: current references and archive navigation were
reconciled with source and static checks. Historical archive bodies retain their
original dated claims and may have obsolete links. External financial sources,
provider licensing/freshness and every browser state were not re-certified.

| Area | Remaining boundary and next safe increment |
|---|---|
| Backend contracts | M02 and subsequent domain schemas preserve public facade identity while keeping HTTP/ORM out of pure contracts. The prior static public inventory recorded 279 paths, 513 schemas and 373 operations before the November 4 consent routes. Legacy integer-version private brief snapshots remain opaque and labeled; current format validation stays strict. Manual frontend contracts still require drift checks; source counts do not replace workflow verification |
| Large workflow owners | M02 separates eight server-action domains, Data Health request/presentation ownership, peer review, benchmark parsing and assumption autofill; portfolio detail retains separate request-owning views. Future extraction needs an actual workflow boundary and behavioral proof, not a file-size target. Source integrity checks alone cannot prove form behavior |
| October 25 structure cleanup | [Continuation evidence](archive/checkpoints/2026/cleanup-rollout-continuation-2026-10-25.md) verifies 41 relocations and restores both axe 4.13.0 archives with exact integrity. October 28 completes supported Docker builds and rollout after the user's network update. Host Git/Python remain unavailable or restricted; six required host packages still differ from the lockfile, including Next.js 16.2.11 versus 16.4.1. Use the verified Docker environment. All 16 verified empty original directories remain after denied removal; no alternate route bypasses that denial. Separate PostgreSQL integration checks are not rerun under the no-new-datasets scope. Protected files, Git index, databases, backups, rollback images and source evidence remain preserved |
| October 28 release preflight and rollout | [Isolation repair](archive/checkpoints/2026/release-preflight-isolation-2026-10-28.md) removes automatic private-settings reads, defaults direct Playwright to port 13000 and preserves explicit test credentials and occupied projects. The [resumed rollout](archive/checkpoints/2026/locked-build-and-local-rollout-2026-10-28.md) verifies all 98 required/eight installed optional packages, 1,766 backend/320 frontend/61 repository tests, TypeScript, contracts, application audits, signed OS builds and 14 normal browser views. All 109 table fingerprints match through verification; runtime settings, original PostgreSQL and worker states are preserved. A fresh backup passes hash/archive listing, not a new restore drill. Thirty-one rollback copies remain outside the six-service project. Subsequent financial scenario review, credential rotation and PR3/PR4 publication are complete. Actual-use/final acceptance and missing issuer facts remain open |
| Read-path performance | Common reads avoid automatic relationship cascades; SQL windows bound latest-price/run loading. Both portfolio lists now allow at most four concurrent valuation requests per page, and management removes unused analytics calls. This repairs observed connection-pool exhaustion and passes repeated browser checks with 43 portfolios plus a 33-input concurrency test. It is not a global request throttle, cross-user cache or large-dataset/concurrent-user capacity certification. Historical-risk series and large benchmark views remain heavier work |
| Provider placement | Both price routes share one audited atomic ingestion service. Health now selects latest runs per normalized status and aggregates historical counts in SQL, without materializing full run histories. Adapter/factory/persistence files still span services/market_data and providers; keep the factory authoritative until a tested domain move removes that split |
| Type synchronization | Frontend contracts still mirror backend types manually. Generated contracts need an approved handling strategy for aliases, envelopes and response-only reconciliation before replacing them |
| Frontend test depth | Source-integrity checks remain alongside rendered/component tests and real browser save/retry/navigation/race checks. The October 13 state/control matrix records supported active workflows; future form edits need behavioral verification, and unmounted legacy components are not implicitly certified |
| Current UI and empty universe | November 5 separates source notes from unavailable/freshness states, explains selected brief inputs, scopes optional diagnostics and keeps failed company requests recoverable. Direct Daily Brief links no longer prefetch its potentially generating GET. Mobile company-setup steps gain keyboard scrolling. Ordinary source facts, dates, Mock Data and financial gaps remain explicit. The approved company cleanup removes data, not these financial/research limitations; empty onboarding must not seed replacements |
| November research-model completion | Eleven explicitly approved historical scenarios are saved with retained narrative/source evidence, and 82 normal desktop/mobile views pass. Direct-rate and bank promotion repairs preserve required financial gates. PR2, PR3 and PR4 are merged; the November 4 completion checkpoint records the next integration pass. Native Node remains absent: the official download returns a network-allowlist 403 even with escalation. Native removal of the first empty helper folder still returns EPERM; zero directories/files/bytes removed. All 32 retained helper files are unchanged by this attempt; one differs from its historical move hash and is preserved |
| Legacy request conventions | The compatibility facade intentionally retains data-only, metadata and default-client envelope behaviors, including distinct error handling. Do not silently switch consumers between them |
| Scratch and historical files | M02 preserves 18 unused one-off scripts in the ignored retired/local directory with an inventory; it does not publish their contents. Unclassified local configuration, generated maps, caches and plans remain preserved. Use the code map and maintained scripts, not historical recipes as current workflow instructions |
| Dependency hygiene | [October 21-22 repairs](archive/checkpoints/2026/dependency-and-pdf-evidence-2026-10-21.md) install Pillow 13.0.0/certifi 2026.10.19 and Next.js 16.4.1. October 28 locks and signed OS snapshots remain unchanged. [November 4 source gates](archive/checkpoints/2026/independent-completion-2026-11-04.md) pass remote dependency/container scans and AMD64 builds. Local R2 ARM64 images remain installed with identical application source; a fresh frontend build of the package-retry policy fails twice on the fixed libpcre2-8-0 package's upstream HTTP504. No partial build replaces the verified runtime. Host-tree drift and unfixed OS findings remain separately recorded; dated scans cannot guarantee future safety |
| Restore coordination | Restore stops running/restarting Daily Brief and source-refresh workers along with the web app, then resumes only those previously active workers after content verification/migration. Failure leaves writers stopped. Regression tests cover disabled workers, equal-count corruption, interrupted/invalid backups and exact scratch cleanup. No destructive normal restore was run. Other writers/admin sessions must be quiesced for replacement; ordinary backup does not require a quiet window |
| Backup format compatibility | Format 3 adds an atomic completion marker to completed-dump content and both-store verification. Verified format-2 folders remain supported. Historical format 1 is count-only and requires opt-in; it cannot earn stronger proof retroactively. Partial and unfinalized folders stay unavailable for restore |
| Parallel test isolation | Browser/release runners now allocate unique projects, reject existing containers/networks/volumes and enable cleanup only after their own creation begins. The release unit-test project is separate. Recovery retains its unique owned tmpfs project. Default ports and shared image tags still need coordinated lanes; unique project names are not host-port or build-cache isolation |
| Documentation audit environment | October 5: system Git/Python required unavailable Apple developer tools; bundled Git was blocked, the project Python shared library was sandbox-blocked, and the Node REPL could not start. Shell ownership and fallback documentation checks ran. Two protected environment-example link targets were excluded. Full Git status, Python documentation/skill checks and product/runtime validation remain unverified for that session; previous product results retain their original dates |
| October 10 toolchain and rollout | Portable tools avoid unavailable host Git/Python. October 13 installs verified workflow images after a complete backup and preserves all 109 fingerprints through normal browser checks. Old registrations survive until final acceptance; failure restores them and resumes only previously active services. Daily Brief runs; source refresh and pgAdmin stay disabled. Rollback images, backups, volumes and the dirty checkout/index remain preserved |
| Browser reliability scope | The [October 24 follow-up](archive/checkpoints/2026/m05-m06-ui-and-financing-2026-10-24.md) passes 36 fresh normal-data views across 1440/390px after the narrow permission update. All 109 table/source-asset fingerprints remain unchanged by each pass; no backend writes, browser errors or accessibility violations occur. Checks cover 11 valuation screens, mix editor/cancel/drafting states and selected financial views. This is bounded UI evidence, not full financial acceptance or load certification. Source 6e2a6f8b also passes 64 remote fixture workflows; no timing/accessibility gate was weakened |
| Current normal data and resources | October 22 after verification: four normal containers sampled 1,258.11 MiB working set and 0.77% combined CPU, excluding VM overhead. Zero restarts and localhost-only published ports. Docker reports 25.88GB images, 3.339GB volumes and 4.487GB build cache; shared accounting is not additive. Host free space is about 26GiB. Ten rollback registrations are separate from the six-service project with files/logs/images retained. Removing only the new successful builder stage recovers 849,703,505 layer bytes. Backups, volumes and failed evidence remain. This is a dated observation, not a permanent resource guarantee or monitoring service |
| Runtime evidence boundary | Current State and checkpoint image/source fingerprints own runtime identity; inherited container source-commit labels are historical. Earlier read-side catalog/discovery/regime changes and later identical rollout/browser fingerprints are separate evidence. Architecture/import refactors do not authorize reseeding, source promotion or rewriting saved models |

## Future scope after release acceptance

1. Use the eleven approved historical research scenarios within their stated limits. Complete issuer-claim evidence remains separate future work; record actual research/demo use. Agent checks do not substitute for actual use.
2. Add compliant provider adapters where licensing and stored-record provenance allow them.
3. Add licensed comparable-company adapters before attempting deeper peer normalization or calibration.
4. Broaden issuer/layout coverage beyond the existing reviewed universe and improve official India providers; the older AAPL/APSEZ reference certification retains its narrower dated scope.
5. Turn separate modules into one daily evidence-to-decision workflow.
6. Improve automatic exact-passage selection while retaining review gates.

The former 2,450-line audit is preserved at
[`archive/assessments/agent_capabilities_and_limitations.md`](archive/assessments/agent_capabilities_and_limitations.md).
