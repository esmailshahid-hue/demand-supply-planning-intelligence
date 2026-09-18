# Workbook, review and portable files (Pass 4)

This workflow uses the existing `Dataset` and the same forecast, planning, scenario and independent replay implementations as bundled samples. It creates planning files, not orders or transfers. There are no accounts, database or persistent server history.

## Templates and field conventions

Download blank and populated fixture XLSX files in Data and Assumptions. Generate larger files locally:

```sh
.venv/bin/python -m scripts.workbook --size blank --output artifacts/blank.xlsx
.venv/bin/python -m scripts.workbook --size fixture --output artifacts/fixture.xlsx
.venv/bin/python -m scripts.workbook --size full --output artifacts/full.xlsx
```

The fixture/full commands parse their output and assert lossless equality with the generated Dataset. Neither offline future truth nor validation labels enter the workbook. `Instructions` lists every contract field, required/default/nullable status, type, enum and bounds; `Examples` contains non-importable illustrations. These sheets are never interpreted as operational rows. Every named column must be present once. Retain explicit defaults in non-nullable cells; blank is allowed only for nullable values. Header order may change, names may not. Dates are ISO `YYYY-MM-DD`; availability/known-at timestamps include a timezone offset. Weekday lists use JSON integers, Monday 0 through Sunday 6. Other lists/maps also use JSON. Booleans are Excel TRUE/FALSE. Missing observations are blank sales with their availability flags; valid zero sales are numeric zero.

All quantities use base units, never cases. Products use `base_unit=unit`; case and lane packs constrain multiples. All monetary values are SAR; costs and prices are per base unit. Volume uses one consistently chosen volume unit across products and location capacity. Decimal values in generated inputs/exports are literal decimal text to preserve round-trip precision rather than Excel's truncated numeric representation. No formulas are evaluated or accepted in operational inputs.

| Sheet | Key | Meaning and principal fields | Maximum rows |
|---|---|---|---:|
| Products | sku | name/category, case_size, volume_per_unit, cost/net_price_per_base_unit, active_from/to | 60 |
| Locations | location_id | dc/store, storage_volume, open_weekdays; one DC and up to four stores | 5 |
| Assortment | sku/location_id | ranged_from/to, service_class, must_stock; optional documented launch_daily_units/launch_known_at/launch_reason | 240 |
| DemandHistory | sku/location_id/day | sales_units, is_open, stock_available, available_at, optional event_id; censored estimates are never known actuals | 100,800 |
| Inventory | sku/location_id | single Settings as_of; on_hand, blocked, reserved, book_unit_cost | 300 |
| OpenOrders | external_id | sku/supplier/destination, remaining_units, order/dispatch/arrival dates, confirmed/dispatched/received, cost_per_base_unit | 5,000 |
| OpenTransfers | external_id | sku/source/destination, remaining_units, dispatch/arrival dates and status | 5,000 |
| SupplierOffers | offer_id | supplier/sku, validity, price_per_base_unit, case_size/MOQ, 1–14-day lead time, order/dispatch calendars, deposit_fraction, balance_days_after_receipt | 720 |
| Suppliers | supplier_id | name, minimum_order_value; optional shared_daily_capacity with explicit base_units/volume unit | 12 |
| SupplierCapacity | supplier_id/sku/dispatch_date | available_units remaining for NEW orders, shared_limit_reference where applicable | 40,320 |
| TransferLanes | source/destination | transit_days 1 or 2, dispatch calendar, capacity_units, grouped_dispatch_fee, pack_units, allowed_skus | 20 |
| Payables | external_id | linked_external_id, due_date, unpaid amount; existing obligations only | 10,000 |
| Budgets | week_start | Monday; new_commitment_cap, payment_ceiling, transfer_budget | 30 |
| Events | event_id | sku/category/store scope, scope_id, dates, uplift/replacement, value, reason, known_at | 100 |
| Settings | key | metadata plus every Settings contract field | 18 |

All 15 sheets are required, including empty ones. `Settings.declared_empty` is a JSON list using Dataset field names, for example `["open_orders","open_transfers","payables"]`. Declare a transaction sheet only when intentionally empty; a missing sheet or undeclared empty transaction sheet blocks import. Empty Events is allowed. Settings includes schema version, dataset ID, synthetic label, as-of date, history (up to 420 days), timezone/currency, fixed 28-day visible/56-day planning/7-day release and review periods, class targets, fallback buffer, holding rate and shortage rule. Inspect the generated Instructions for exact supported constants and defaults.

Reservations are commitments outside this demand forecast: usable stock = on-hand − blocked − reserved, deducted once. Negative usable stock is invalid. Capacity is remaining dated supply for new orders; zero is explicit and missing is unknown. Commitment limits authorize new orders; payment ceilings also cover existing unpaid obligations. Transfer budgets constrain grouped movement fees separately. Budgets must cover the complete obligation window, including balances beyond the 56-day stock horizon. A received transaction has zero remaining inbound quantity and is already included in the new inventory snapshot. Include a Payables row only for a still-unpaid obligation; receipt does not regenerate payments.

## Validation, transport and privacy

Limits: 16 MiB XLSX, 160 MiB expanded ZIP, 120 MiB per entry, 100 ZIP entries, 250:1 expansion ratio, 8 MiB shared strings, 1 MiB styles, 4,000 characters per cell, 40 columns and 170,000 operational rows plus at most 10,000 optional reconciliation rows. Per-sheet bounds above also apply. Password protection, malformed ZIP/XML, macros, external relationships, embedded objects, XLS/XLSM, formulas/errors, unknown sheets/fields/IDs, duplicate keys, inconsistent dates/stock/units and missing funding/capacity block import. Errors have sheet, row where attributable, field, severity, stable code and correction guidance. Cross-sheet coverage failures may have no single row. Warnings remain visible and are regenerated by the calculation validator.

`openpyxl` read-only parsing follows ZIP/defused-XML preflight. Each parse uses an isolated request directory, closed/deleted on success, validation failure or exception. No raw rows are logged. A forged worksheet dimension cannot hide extra rows. Explicit server-processing consent is required; the browser never sends normalized Dataset JSON.

No authorized hosted object-storage resource was configured. The implementation therefore provides a provider-neutral storage interface, private reference/upload-authorization contracts and a **local temporary-file driver**. Local browser uploads send raw XLSX (not multipart) to `/api/workflow/import`; calculations send only `X-Dataset-Ref`. References are random, bound to an HttpOnly SameSite session capability, purpose checked and non-public. This is session isolation, not account authentication. Local objects expire one hour after creation; sweeps run every 30 seconds, on access, reset and normal exit. Original upload bytes are removed immediately after parsing. Normalized data and draft/accepted records remain temporary. Crash-leftover directories are swept after expiry on a subsequent running process; deletion cannot be promised while the service is stopped. Local limits: 64 MiB/object, 128 MiB/session, 512 MiB/process. One worker is required; a restart discards sessions. Download portable files before leaving.

`VERCEL` always disables local upload/review-file storage. `PLANNING_UPLOAD_STORAGE` accepts the local driver for local service use; unimplemented/unknown choices fail closed. Sample calculations and template downloads remain available. Hosted uploads/accepted files are **blocked**, not verified. A future authorized adapter must provide private direct browser upload, short-lived scoped authorization, small object references, ownership/expiry/size/content verification and deletion/lifecycle tests. The API contracts alone do not implement that adapter. Do not send a full normalized JSON document through a Function or expose storage credentials/public permanent links.

## Review and final acceptance

Action decisions record source run/input hash, scenario version, type, stable business key, original/reviewed quantity, status, timestamp and note. Accept locks exact terms; reject prohibits only that supplier/lane/date candidate; quantity edits are exact, never silently rounded. Every change marks the displayed plan stale. Regeneration rebuilds the full benchmark/joint candidate under those constraints and independently replays stock, arrivals, capacity, calendars, commitments, payments and movement funding. A timeout/error cannot drop locks. The full sample retains its disclosed zero joint sub-budget and validated benchmark fallback; reviewed restrictions can produce an honest conflict even when another feasible solution might exist outside the bounded search.

Pooled stock defines dependencies, not invented purchase-to-transfer ownership. Removing supply may change or invalidate downstream movements; alternative dated stock can support them. Decisions show pending, retained or conflicted disposition. Rejections remain active prohibitions even when no candidate is selected. Detailed plan/scenario evidence is rebuilt from the regenerated actions.

Final acceptance is separate: current input/forecast/scenario versions, every exact lock/prohibition, hard constraints, full independent ledger and export reconciliation must pass. Remaining service/buffer deficits require explicit acknowledgement; acknowledgement never overrides hard failures. Immutable accepted versions retain their own reference. Changing an accepted version requires an explicit new draft and fresh regeneration. Old downloaded snapshots and the old accepted reference remain unchanged until local expiry/reset. No execution is sent.

## Exports and portable snapshots

The reviewed XLSX contains Summary, PurchaseActions, MovementActions, UnresolvedExceptions, PaymentSchedule, WeeklyFunding, ServiceMetrics, ReviewDecisions, Assumptions and Metadata. Values come from accepted engine/replay records, including quantities, purchase commitments, deposit/balance dates/amounts, existing obligations, grouped fees, cash headrooms, shortages, forecast/scenario/input hashes, run/accepted/engine/schema versions, source/synthetic labels and solver stages. Literal text prevents formula injection. Stale, invalid or unaccepted drafts cannot download accepted exports.

The distinct portable `accepted-plan-1` JSON snapshot is gzip compressed (16 MiB compressed / 64 MiB expanded maximum). It contains lossless inputs, the accepted draft, actions, decisions, assumptions, full replay, versions and stable external IDs. Canonical SHA-256 checksums detect corruption; they are **not signatures or authenticated provenance**. Import validates schema/checksums/identifiers and opens read-only without executing or recalculating. Only an explicit new draft can be edited and must pass fresh replay before acceptance. Full snapshots are served locally; hosted file transport remains blocked pending the same private storage adapter.

## External reconciliation without a database

First reopen the accepted portable snapshot. Then import an updated workbook; the browser supplies that snapshot's private reference. An optional `Reconciliation` sheet has exactly `external_id`, `confirmed_units`, `executed_units` (unique IDs, nonnegative integers). Use exported `DSP-…` IDs on matching OpenOrders/OpenTransfers rows. Confirmation alone is not execution: `confirmed_units = executed_units + remaining_units`; only `accepted units − confirmed units` can remain proposed. A received row must be fully executed, zero remaining and represented in Inventory. A dispatched transfer is already out of source stock and remains in transit until its imported arrival. Existing unpaid balances are supplied once via Payables.

Matching business terms, prices, quantities and IDs are checked. Missing execution evidence, duplicate/unknown IDs, changed terms or inconsistent partial quantities block import. Fully confirmed candidates become immutable prohibitions; partial unconfirmed remainders retain exact terms and cannot be increased by later review or restored by clearing a decision. They may be reduced/rejected subject to normal hard constraints. Repeated identical imports produce identical reconciliation. No previous server history is consulted. Updating real-world terms requires explicit new reconciliation evidence, not silently relabeling a proposal.
