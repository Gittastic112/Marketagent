# India remaining-input audit, November 2, 2026

The new [Reliance candidate](historical-completion-candidate.json) can close the
historical share and disclosed-award treatment under the delegated research/demo
scope. It does not amend the two earlier immutable review packets, supply current
market values, or bypass promotion checks. The accompanying
[gap audit](remaining-gap-audit.json) records five verified original hashes,
31 source-locator checks, arithmetic, bank requirements and precise remaining
disclosures. No database, source history, application code or saved model changed.

## Reliance: dated reference candidate ready

Use March 31, 2026 issued ordinary shares of 13,532,472,634 plus all 907,052 disclosed
parent options: **13,533,379,686 shares**. This is an all-conversion estimate, with
no assumed forfeitures or exercise proceeds. It is neither a current denominator
nor annual EPS-weighted diluted shares. Parent options receive no second deduction.

The [issuer-linked Jio statement](https://rilstaticasset.akamaized.net/sites/default/files/2026-05/Jio_Platforms_Limited.pdf)
identifies 8,939,030,830 issued shares and Reliance's 5,937,841,645 holding in note 9,
PDF page 27. Its 10,280,000 outstanding options agree with retained RIL note 28.2.
The retained RIL consolidated summary supplies Jio ordinary book equity of
INR335,977 crore, excluding lower-tier NCI. Apply the disclosed method:

`Jio ordinary book equity × RIL holding fraction × options / (issued + options)`.

The result is INR2,563,605,805 before rounding. The selected **INR2,564 million**
award deduction is a carrying-equity proxy for RIL's incremental loss from Jio
dilution. Keeping aggregate NCI and deducting only RIL's incremental loss is
algebraically equivalent to deducting post-conversion outside ownership and the
full Jio award claim. It does not charge RIL for the portion borne by Jio's existing
outside shareholders. All monetary inputs remain full INR in the patch.

This method covers the award populations disclosed in consolidated note 28.2.
Book equity can differ materially from economic value. It is not an option-pricing
estimate or a claimed upper bound on fair value. The standalone and consolidated
notes disagree on the exercise-period description, so the method uses their
matching dated counts and makes no remaining-life estimate.

The existing 14% INR reference hurdle remains a discretionary scenario choice.
Issuer beta, ERP, cost of equity, cost of debt and capital weights remain rejected.
The current FCFF promotion contract still requests those components, so the
coordinator must resolve the fixed-hurdle method versus component-input contract
before promotion. Missing values must not be disguised as observed risk inputs.

Reliance's net external revenue weights remain unavailable. Gross external sales
minus the segment GST row reconciles numerically to group net revenue, but the
report does not allocate GST between external and intersegment sales. The exact
additional disclosure is an external-net segment table or that tax/elimination
split. Keep the existing Diversified taxonomy comparison.

## Airtel: narrower, identifiable gaps

The retained report supplies 6,093,282,313 fully paid and 1,110,668 partly paid
shares. Subtracting reported treasury shares and adding all parent LTI awards
would produce a **6,095,062,981** parent full-conversion reference estimate. Both
treasury and award counts are rounded to thousands. This candidate is withheld
because it does not resolve subsidiary awards or minority puts. Simply adding the
3,167,000 parent awards to issued shares would count treasury shares twice.

The notes identify Nxtra options, Airtel Africa options and several award classes,
and Indus options. These claims are on different underlying companies. A carrying
conversion approach needs matched subsidiary shares, treasury treatment, award
conversion limits, ownership and attributable equity/earnings. They cannot be
added to Bharti parent shares.

The [Airtel Africa NCI note](https://cdn-webportal.airtelstream.net/website/investor/main/AR2026/reports/30-investments-in-subsidiaries-17304.html)
narrows AMC's aggregate NCI to USD118 million, with a separately identified
lower-tier minority population. The [transaction terms](https://cdn-webportal.airtelstream.net/website/investor/main/AR2026/reports/directors-report-17269.html)
grant puts to TPG and Mastercard, while AMC has additional minority investors.
The required historical bridge is therefore **put-beneficiary-specific NCI within
Bharti consolidation**, including ownership, FX and lower-tier adjustments.
Neither deducting both full NCI and the full put, nor replacing all AMC NCI with
the put, represents the correct claim population.

The [October 29 issuer release](https://www.londonstockexchange.com/en/news/article/AAF/half-year-report/22d9-02-fd-9e-d9-4dd185)
states that the later AMC listing extinguished the put after September 30. This
closes uncertainty about that later event, but cannot remove a March 31 obligation
from a historical reference. The audit also records the differing 48/60-month
descriptions and carrying/fair-value scope across the two issuer reports.

The old Network i2i USD1 billion perpetual issue is separately resolved: note 4(r)
says it was redeemed during FY2025. Generic share-rights language must not
resurrect it as an extra FY2026 claim.

## Banks: parent arithmetic is available; consolidated treatment is incomplete

| Bank | Historical issued shares | All disclosed parent awards convert |
|---|---:|---:|
| HDFC Bank | 15,393,368,328 | 15,659,052,066 |
| ICICI Bank | 7,160,112,569 | 7,315,336,774 |
| SBI | 9,230,617,586 | Not established |

The HDFC group notes disclose awards at Securities, HDB Financial, ERGO, Capital,
Life and AMC. The exact counts and pages are now in the audit. The selected common
book-equity basis also excludes a separately presented employee-award reserve,
which needs reconciliation under an all-conversion approach.

ICICI's Life and General Insurance awards remain separate. Securities' former
awards were cancelled and replaced with parent awards; their explicit zero
outstanding subsidiary balance must not be double counted. SBI's group exercise
figures are completed issuances, not unexercised award counts. Its equal basic and
diluted EPS averages do not establish a zero year-end award population.

The bank engine consumes book equity, net income, target ROE, cost of equity,
terminal growth, horizon, shares and currencies. It **does not deduct the
employee-options field**. Setting that field cannot fix these subsidiary claims.
A complete historical scenario needs consistent pro forma parent equity/income
after subsidiary dilution, or an explicitly reviewed claim-deduction method in
the engine. No complete bank candidate is supplied merely because the parent
share arithmetic can be calculated.

Validation: five Reliance checks, five gap arithmetic checks, 31 locator checks
and five original hash comparisons pass. This was a source/calculation audit,
not a runtime or browser test. Direct raw Jio PDF retrieval was rejected by the
network allowlist; the issuer-linked web read succeeded. The new source has a URL
and precise notes/pages, but no raw-byte hash or ingested-source claim.
