# Research workflow guide

Sign in to the local app. A fresh installation can be empty. Add the company and sources you want to study, or open a company that already has records. [First-time setup](local-development.md#start-and-sign-in)

## Start on Today

Choose a portfolio and select **Show portfolio**. The four summary cards show its dated snapshot value, alerts to review, tracked companies and thesis notes. The Daily Intelligence Brief and active alerts come next. **Continue your research** shows up to six items for the selected filter. Open a company for its full history.

A sample portfolio represents hypothetical holdings, even when its prices come from original market records. Open **Portfolio basis & assumptions** for context. Expand **Source activity** for recent processing failures or open **Data Health** for the detailed record.

Use the top-bar search button or **Cmd/Ctrl+K** to find a company or stored evidence. The full search page is available from the sidebar.

## Inspect a price move and pin a thesis note

1. Open **Companies**, select the company and find **Price history** on its overview. Check the provider, symbol, currency, adjustment basis and date of the last stored close. If multiple series exist, **Price series** switches between them.
2. Choose **1M**, **3M**, **6M** or **All**. Select a point on the chart, choose a marked date in **Key moments**, or use **Inspect date** and **Open point details** with the keyboard.
3. A diamond marks a rise or fall of at least 5% from the preceding comparable stored close. A circle marks dated source material. A square marks one of your notes. **What happened around this close?** links to stored documents and events. Material from the preceding close has its own date. Check the publication time where available. Splits and distributions can move an unadjusted close. A nearby filing alone cannot establish the cause.
4. To record your interpretation, choose **Attach to thesis**, enter **Note on this close** and select **Pin to thesis**. If the company has no thesis yet, follow the link to create one and return to the chart.
5. Open the thesis and find **Pinned price notes**. Each entry keeps the closing price, date, provider and basis you saw when saving. Its link opens the private note beside the current stored close for that date. After a correction, the note keeps the price you originally saw. The corrected chart point receives a marker only when a note is attached to that observation.

If the app finds no dated source, the reason remains unverified. A missing or conflicting close can also leave the percentage unavailable. **All** displays up to 365 stored dates for the selected series. [Price comparison and source matching](reference/workflows.md#company-price-history-and-thesis-pins)

## Review a filing and valuation

1. Open the company’s **Financials** tab and select **Financial review plan**. Choose the relevant model track. An optional latest year selects a three-year checklist.
2. Open the linked filing, page or candidate. Check period, currency, scale and accounting scope. Keep unresolved components open. Promotion is an explicit review action. [Selected-company financial gaps](limitations.md#selected-company-review-follow-up)
3. Review a draft in the valuation workspace. Inspect missing inputs and any assumption or estimate before accepting it. A new model uses its creation review gate. For an existing model, preview the proposed change, review the calculation and save a version. Version history retains the saved basis. Selecting a historical date in Financials alone does not change the model.

## Use the brief and private research

Open **Daily Brief** to inspect source-linked events and the coverage window. **Refresh stored evidence** creates a deterministic brief. Expand **Add or browse private research sources** for private text or PDF intake. **Local Brief Schedule** controls optional scheduling.

An optional external AI scan requires its disclosed scope and your permission. Inspect exact citations, check numeric or period flags and record your rationale before approving an output. Editing citation evidence resets approval and retains the earlier receipt.

## Use Research Lab

Open **Advanced → Research Lab**. Choose an operation and inspect its configuration and input basis. Allocation, simulation and return reports use the return series supplied to that run. Reference peer discovery proposes candidates for review. Saved research runs can be reopened and exported. A provider entitlement or optional dependency may be required for some operations. [Adapter and Research Lab guide](adapters/README.md#start-in-the-application)

## Review portfolio and macro results

In **Portfolio**, check holdings, cash flows, quote dates, FX and benchmark coverage for the chosen period. The price/FX importer shows a preview before applying the exact reviewed file. Missing values can make a result partial or unavailable.

When the eligible price predates a recorded split or bonus, the app withholds the position value until a compatible price is available. A benchmark comparison uses a single identified series for its boundary and cash-flow dates.

In **Macro Workbench**, supply chronological periods and consistent currency, scale and factor directions. Enter zero only when the input is actually zero. Calculations use the explicit inputs. Covered segment or scenario contributions can be partial. [Feature register](roadmaps/feature-register.md) · [Known limitations](limitations.md)
