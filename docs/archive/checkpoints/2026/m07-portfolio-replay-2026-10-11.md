# M07 recorded portfolio replay

October 11, 2026. Source implementation is verified in isolated tests. M07 remains
in progress because genuine activity and the broader reviewed-input gate are absent.

`recorded-portfolio-replay-v1` reconstructs dated positions and cash from recorded
funding, purchases, sales, fees, taxes, dividends and explicit split/bonus records.
It uses average purchase cost including fees, purchase-date FX and proportional
cost removal on partial sales. Fully sold positions can still appear at past dates.
Current holdings and cash must reconcile to the complete recorded ledger. Negative
cash, missing opening positions, ambiguous identities, unsupported adjustments and
more than 20,000 activity rows prevent a complete result. It does not infer trades.

Transactions are ordered by date then record ID. Intraday/settlement ordering is
not recorded. Recorded dividend quantities are cash amounts, not quantity times
price. Split quantities are ratios; bonus quantities are additional shares. Explicit
corporate actions cannot be combined with an adjusted price as if both were needed.
Historical risk remains a fixed-weight price-return calculation, not realized total
return; unsupported action/adjustment histories withhold the aggregate result.

New snapshots retain method, activity IDs/hash, reconciliation IDs, corporate-action
basis and purchase-date FX IDs. Existing snapshots are not migrated or rewritten
on read; explicit capture or edit remains a write.
Legacy/manual snapshots remain replay-unverified. Manual snapshot edits invalidate
claimed replay provenance. Performance, attribution, benchmark and readiness reads
check the recorded activity hash; later corrections make old results provisional.
Current declared positions remain User Assumptions when no replay is requested.

Independent reference cases cover multiple purchase FX dates, partial sales,
deposits/withdrawals, cash fees/taxes/dividends, split/bonus quantities, zero holdings,
future-price/FX/model exclusion, owner isolation, correction invalidation and limits.
One EUR/USD case independently reconciles USD244.133 remaining cost, USD1,521.80
total value and USD240.20 period change with zero residual. Existing TWR/MWR,
benchmark, attribution and risk tests retain their numeric expectations while legacy
fixtures now disclose provisional status instead of claiming verified replay.
An additional independent covariance case uses alternating 10%/20% return series
with 60%/40% ending weights. Annual sample covariance is [[3.36, 6.72], [6.72, 13.44]];
portfolio variance is 6.5856 and volatility is 2.566242389. Marginal risks
1.833030278/3.666060556 and components 1.099818167/1.466424222 match independently
calculated expectations. All thirteen replay tests pass. These deliberately large
Mock Data moves test arithmetic, not expected returns or a recommended portfolio.

The production browser seed now records real fixture transactions and invokes the
same snapshot service as the app, replacing manually prefilled totals. Every row is
isolated Mock Data. The normal database was not seeded or rewritten.

This change necessarily spans replay, valuation/snapshots, performance consumers,
API contracts, UI labels and regression fixtures so historical trust is consistent.
Integrated validation is recorded in the [M09 checkpoint](m09-browser-validation-2026-10-11.md).
The [single ledger](../../../agent_capabilities_and_limitations.md) owns remaining
genuine-input and runtime limitations. No migration or normal rollout occurred.
