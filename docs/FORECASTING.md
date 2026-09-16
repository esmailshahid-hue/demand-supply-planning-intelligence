# Pass 1 forecasting and contract decisions

The build plan remains authoritative. This document records concrete choices where it leaves implementation detail open.

## Time and eligible evidence

`Settings.as_of` is the **first forecast date**, at midnight Asia/Riyadh. An observation may train an origin only if its business date and timezone-aware `available_at` both precede that origin. No revision history is inferred: the supplied row is assumed immutable as of its availability timestamp; revised historical observations will need explicit vintage support if introduced later.

Open, ranged, stock-available sales—including zero—are observed evidence. Closed/unranged days are excluded. Null sales, unknown availability and absent records stay unknown. A reported stockout makes sales a lower bound. The sample reports daily sales at 01:00 the next day; the last historical day is therefore not yet known at as-of midnight. The sample final check honestly has 27/28 observations, and its quantity MAE is unavailable. This also excludes the final day of the most recent selection window from selection evidence. Delayed reporting is a separate warning.

## Three ordinary weekday candidates

All multi-step candidates use a fixed origin: predictions never become synthetic training observations.

- Seasonal naive: most recent eligible same weekday within the four prior calendar occurrences. Repeat its weekly pattern for the forecast horizon.
- Four-week same-weekday mean: average eligible values in those four calendar occurrences.
- Recency-weighted mean: weights 0.4, 0.3, 0.2, 0.1 on those occurrences. Missing entries retain their calendar position; the remaining weights are renormalized.

A censored training observation may be estimated from strictly earlier uncensored ordinary observations of the same weekday in the prior 28 days, with observed sales as a lower bound. Later observations and previous estimates cannot feed that estimate. Estimates are separately returned in recent history and **never scored as actual demand**. The implementation does not impute missing observations.

Known event days are excluded from the ordinary training pool. Exclusion uses event knowledge at the forecast origin. Future events unknown at that origin are not applied. Supported scoped events are multiplicative uplift or replacement quantities, with reason, dates and known-at timestamp. They apply once after the baseline; the result retains original baseline and revised quantity per date. Overlapping rules affecting the same SKU-store-day are rejected. Interactive overrides and scenario workflows are deferred.

## Selection and final check

The final 28 historical days are a held-out final check. The preceding history supplies up to **eight disjoint 28-day selection windows**, spaced 28 days apart. Each origin has at least 28 calendar days of earlier history. There is no selection-window overlap and no selection/final-period overlap.

Selection labels must be available before the holdout origin, not merely before the present as-of. At least four complete 28-day selection windows are required. For Pass 1, “complete” conservatively means all 28 dates are uncensored, observed and forecastable. Closed/unranged dates do not count as demand evidence; a window containing them contributes partial observed metrics but not complete-window selection quantities. A routinely closed store may therefore remain provisional. This stricter coverage policy is disclosed rather than filling closed or unknown days with scored zeros.

Select a challenger only if mean absolute total-quantity error improves by **at least 5%** and absolute mean signed quantity bias does not worsen, on the **same complete origins** as the baseline. If several qualify, choose the smallest quantity MAE, then stable method order (weekday mean before weighted mean). A zero-error baseline is retained. The threshold is a product default, not a significance test.

The held-out result is computed for all three candidates for inspection; it cannot change the selected method or empirical buffer evidence. Refit the selected method on eligible history available at current as-of for the actual future forecast.

## Metrics

For each origin and each of 7, 28 and configured protection-period days (14 by default):

- Daily absolute error: sum of `abs(forecast - observed)` over eligible scored days.
- Pooled WAPE: that absolute error divided by summed observed units, times 100. `pool_metrics` also supports pooling across series. Never average series percentages.
- Signed bias: sum of `forecast - observed`, in units and as a percentage of observed units. Positive means overforecasting.
- Quantity MAE: mean `abs(sum(forecast) - sum(observed))` across **complete** windows only.
- Quantity bias: mean signed total-quantity error across those complete windows; this is the selection bias guard.
- Counts: valid daily observations, excluded counts by reason, possible observations, total and complete windows.

Percentage metrics return `null` when the actual-demand denominator is zero. Absolute metrics return `null` if no observations can be scored. There is no fabricated launch accuracy. Partial-window sums explicitly represent scored dates only, not a full-period demand total.

## Fallbacks and buffers

Missing weekday evidence falls back to the uncensored ordinary mean over the prior 28 calendar days. Every fallback is labeled per future date. With fewer than 28 eligible uncensored observations, a declared launch estimate takes precedence if known before origin; otherwise use available observations provisionally. No estimate plus no recent evidence returns `null` and an unavailable forecast, not invented zero demand. Closed/unranged future days have planned demand zero, excluded from historical scoring.

All-zero observed series keep a zero ordinary forecast and unavailable percentages. Intermittent series have no positive-demand floor and are explicitly described. Days 29–56 are always marked a provisional tail.

Buffer evidence uses complete selection-period cumulative underforecast errors for the selected method at the protection horizon. Four samples are required for a linearly interpolated empirical percentile (default 90). Otherwise use a labeled days-of-demand buffer (default three days). Return sample count, percentile and method. This is not a fill guarantee. Pass 2 must use actual protection periods and avoid duplicate DC buffers.

## Data/API contract

The Pydantic schema defines all 15 normalized input tables, with separate transaction row types. Numeric prices/costs are **SAR per base unit**, quantities are base units, and packs are positive integer conversions. `declared_empty` is required for empty transaction tables. Unknown capacity is never unlimited. Funded input requires 90-day weekly funding coverage (or the last declared payable date, if later); unfunded exploration is explicitly labeled. Full stock/cash feasibility checks belong to Pass 2.

Reservation semantics: reserved units are commitments outside the supplied forecast, deducted once in usable stock; the demand history is not reduced again. Received-but-unpaid POs have zero remaining stock receipts and linked unpaid installments. Stable external IDs distinguish orders, movements and installments.

Limits: 60 products, one DC/up to four stores, 240 assortments, 420 history days, 100,800 observation rows, 12 suppliers, 56 forecast days, and a 32 MiB request body. Additional transaction list limits are in OpenAPI. JSON requests use schema version 1.0.0 and reject extra fields, including truth and expected labels. The public UI only calculates selected sample series; normalized-data POST is an engineering API, not the deferred workbook workflow.

Endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Readiness and engine/schema versions |
| `GET /api/sample?size=fixture|full` | Sample catalog and validation warnings |
| `POST /api/forecast/sample` | Live sample calculation; `{size, sku, location_id}` |
| `POST /api/forecast` | Validated normalized `{dataset, sku, location_id}` |
| `GET /openapi.json`, `/docs` | Shared schemas and API reference |

Errors have a code, message and grouped issues; validation responses omit raw input values. Every calculation has a new run ID and hash of the normalized input's ordered serialization. The hash is stable for identical serialized inputs, not order-independent canonicalization. No user result is cached. Only server-owned synthetic input datasets and their validation issues are cached, and calculations do not mutate them. A single process admits one forecast calculation at a time and returns 429 for contention. The forecast engine checks a cooperative 30-second budget between origins; this is not a preemptive OS-level request timeout. Pass 2 must enforce its overall solver-stage budget separately.
