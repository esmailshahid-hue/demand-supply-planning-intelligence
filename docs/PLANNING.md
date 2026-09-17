# Pass 2 planning calculations

The Python planning API evaluates the complete input network. `POST /api/plan/sample` accepts `{"size":"fixture"}` or `{"size":"full"}`; `POST /api/plan` accepts the normalized `dataset`. The UI uses only the small sample selector request. No normalized history or withheld synthetic truth is returned to the browser. Result schemas live in `backend/app/planning/contracts.py`; TypeScript is generated from OpenAPI.

## Forecast boundary and horizons

`planning/inputs.py` calls the unchanged Pass 1 forecast evaluator for each ranged SKU/store. It partitions historical rows by series to avoid repeatedly hashing all 99,160 full-sample rows, while retaining other normalized input tables, dates, events and settings. Each trace contains the forecast run, series-projection hash, selected method, status and buffer evidence; the plan hashes the complete input dataset separately. These hashes therefore intentionally differ from an independently requested whole-dataset forecast hash.

Protection days are the greater of the declared floor and review period plus calendar-adjusted supplier/DC/store replenishment path, using the conservative longest eligible path. Periods beyond supported 28-day forecast evidence are rejected explicitly. Existing forecast selection, cutoff, censored/missing data handling and event logic are unchanged. Fractional expected units remain fractional; purchases and movements are integer packs.

The model covers 56 days. Days 1–28 are the visible review, 1–7 release candidates, 8–28 planned actions, and 29–56 provisional demand/actions. No new receipt can arrive outside the model. Payments are checked through at least day 90 and every known later obligation. Missing funding, capacity or stock snapshots is not treated as zero or unlimited. Unsupported/incomplete inputs return `invalid_inputs`, with no executable recommendation.

## Joint model and fallback

`planning/optimizer.py` builds a SciPy/HiGHS mixed-integer model across every SKU, location and day. Purchase cases and movement packs are integer decisions; binary activation enforces conditional line MOQ, supplier/order-date grouped minimum value, grouped lane/day fees and conditional donor reserves. Stock and fulfillment balances impose receipt → local service → dispatch → close. Fulfillment is exactly the minimum of available stock and demand, so the solver cannot withhold demand to protect another objective.

Hard constraints cover offer validity/order/dispatch calendars, lead times and receiving days; dated supplier SKU availability plus shared units/volume; shared lane capacity; receiving peak volume including blocked/reserved stock; purchase commitments, deposit/balance payment ceilings and movement allowances by week. Opposing same-SKU movements on the same day are forbidden, including confirmed movements.

Objectives run sequentially: visible-window must-stock, A, B and C class/store target shortfalls; the same priorities in the provisional tail; weekly store-buffer deficits; commitment, grouped movement and daily holding cost; stable action-rank ties. Each completed optimum is preserved before the next stage. All stages share the remaining overall 30-second target budget, including forecast, benchmark and model construction, with two seconds reserved for independent replay and serialization. This is cooperative termination, not a hard process kill. A timed-out stage stops lower stages and is never called optimal.

The constrained order-up-to benchmark uses identical forecasts, buffers and declared limits, allocates by earliest shortage then must-stock/class and stable SKU/store ordering, and purchases case-rounded requirements from the cheapest eligible source that can meet the next shortage when one exists. Later arrivals cover only later demand. It conservatively reserves receiving space without borrowing future consumption and requires a single line to cover the supplier minimum; the joint model can combine lines. This can make the benchmark conservative. It remains an honest, reproducible comparison rather than a target company's current process.

The live joint optimizer is a best-effort challenger with a **2.0-second sub-budget**, including construction and cold import, bounded by the existing 30-second request deadline minus two seconds for final replay and serialization. Forecasts, deterministic benchmark and benchmark replay run before the challenger. The exact optimizer, zero relative-gap setting, hard constraints, objectives and small-model tests are unchanged.

A joint plan is selected only when the exact sequence of required stages completes with optimal status and zero reported gap (or no gap for a non-MIP stage), and independent replay passes. Otherwise the deterministic benchmark is selected after independent replay, provided its eight-component lexicographic service score is no worse than no new actions. That score sums class/store target shortfalls for visible must-stock/A/B/C then tail must-stock/A/B/C, using pooled units and rounding each component to five decimals as before. No timing-dependent incomplete incumbent is selected. If the benchmark fails validation or worsens that service score, the existing safe no-new-action/invalid-plan path remains available; that path does not satisfy the sample action gate.

### Product acceptance decision — 17 September 2026

The user deliberately retired exact default-fixture completion as an MVP prerequisite. Earlier profiles spent approximately 28 seconds in the first stage and returned the same deterministic benchmark. The live workflow now requires useful independently feasible actions, reproducibility, honest fallback disclosures, reconciled funding, responses below 4,500,000 bytes and end-to-end sample HTTP latency below 10 seconds. The old fixture gate remains historical evidence only.

“Joint staged plan” means all required stages completed and replay passed. “Validated constrained plan” remains API status `feasible_fallback`: the deterministic constrained planner produced it and replay checked it; it is not globally optimal. The evidence area retains the actual interrupted stage and an explicit `independent_fallback:benchmark` stage. Existing shortage explanations remain visible.

The two-second choice preserves fast exact completion for hand models while avoiding the measured fruitless 28-second sample solve. Final local HTTP first/repeat was 2.908 / 2.644 seconds for fixture and 6.468 / 6.673 seconds for full; actions, totals and explanations matched exactly, all replay checks passed, and all cash reconciled. Full evidence is recorded in BUILD_STATUS.md. The request deadline remains cooperative, not an OS-enforced kill, and hosted/CI timings require their own verification.

Future scenarios may compare frozen and replanned validated policies when both use identical scenario assumptions and independent validation. This pass adds no scenario functionality. Scenario responses must share or reference ledgers rather than duplicate the full daily ledger: the current full response is approximately 3.75 MB against the 4.5 MB ceiling.

## Independent stock and cash replay

`simulation/replay.py` imports no optimizer code or solver variables. It reconstructs actions from normalized inputs and recommendation records, checking identifiers, supplier/lane eligibility, packs/minimums, calendars, shared capacities, receiving peaks, funding and conservation. A corrupt action is reported, never silently fixed.

Opening usable stock is on-hand minus blocked and reserved once. Already dispatched transfers are in transit, not deducted from the opening snapshot again; confirmed transfers dispatch once. Received POs add no stock but can have unpaid installments. Existing transfers' unpaid charges must be in Payables; new grouped fees apply once per lane and dispatch day. Adding units to an already-confirmed dispatch group does not charge its fee again. SupplierCapacity means remaining availability for new orders, so existing POs are not subtracted a second time.

Donor protection applies only when dispatching: maximum cumulative next-seven-day forecast less confirmed receipts on their actual dates, plus the store buffer. Speculative new receipts cannot justify depleting a donor. Lookahead after day 56 repeats the final forecast week. Shortages are lost sales and never backlogged. Later round trips are exposed for ledger inspection; the UI makes no claim of a uniquely necessary transfer.

Supply prices are required at SAR-cent precision. Line values and deposits use decimal half-up cents; balance equals full line value minus deposit. Both installments consume their actual due weeks, including when they fall in the same week. Existing unpaid obligations consume payment capacity, not the remaining authority for new purchase commitments. Existing breaches are input failures with the affected week.

## Dated shortage explanation evidence

Shortage explanations are derived from `Replay.stock`, not from a horizon-wide scan of theoretically available offers. Each affected SKU/store/date uses its replayed unmet quantity. Candidate supply is considered only if its order validity, order and dispatch calendars, supplier lead time, DC receipt, lane dispatch, transit and store receiving calendar place stock at the store by that shortage date. A later receipt cannot explain demand that was already lost.

Before assigning a purchasing limitation, the explanation checks usable stock on every eligible inbound lane, the source's donor reserve, remaining lane capacity and the exact dispatch/arrival dates. Such a path is evidence of an available alternative requiring reoptimization; it is not automatically labeled as the cause of the shortage. When a timely path passes all tested constraints, the result explicitly states that attribution is uncertain rather than inventing a binding constraint.

Supplier minimum evidence uses the supplier/order-date group. Other planned lines on that supplier and order date contribute first; only the remaining minimum is converted to a case-rounded quantity. `GROUPED_SUPPLIER_MINIMUM` is emitted only when the smaller timely line is otherwise feasible and increasing the group to its qualifying value hits another dated hard limit. An already qualifying, affordable SAR 600 group is therefore not blamed for shortages that occur before its receipt can reach a store.

Financial evidence uses the same half-up cent rules as replay. The candidate line's deposit, balance and any incremental transfer fee are grouped by funding week before comparison. Replayed headroom already includes existing obligations and planned payments once. A SAR 50 deposit and SAR 50 balance in one week require SAR 100 of headroom; they cannot pass against SAR 60 by being checked separately. Installments in separate weeks remain feasible when each week's complete cash requirement fits.

Inventory investment carries acquisition value at weighted-average cost on internal movements and includes blocked/reserved stock. Revenue exposure is unmet visible units × declared net selling price, not proven lost revenue. No tax, revenue receipts, receivables or accounting cash-flow forecast is implied. Day-56 excess compares usable stock against the next seven days plus store buffers, repeating the final forecast week; DC coverage uses net store need without a second buffer.

## API and interface

Plan Review renders Python totals, purchase actions, shared allocations, cash weeks, class/store targets, individual SKU/store shortages and reason-coded exceptions. Expandable evidence provides source/destination daily stock, payment dates, forecast versions, solver stages and assumptions. Only the proposed plan carries the full daily ledger; comparisons retain policy actions, service, cash and totals. The full normalized input dataset is never echoed.

Pass 3 scenario responses must continue sharing or referencing the proposed daily ledger rather than duplicating all SKU/location/day rows for every comparison. The measured full response already uses most of the 4.5 MB Function response allowance.

Loading clears the prior result; changing the planning dataset or recalculating updates the whole result from one API response. Aborted requests cannot overwrite newer UI state. Server calculation continues after a browser abort; the shared process semaphore returns 429 with retry guidance while it finishes. This is per-process admission control, not distributed scheduling. No plan is persisted or released to suppliers.

Scenarios, reviewed edits/locks, workbook workflows, exports and hosted release audit remain later passes. Existing confirmed transactions are fixed input actions; there is no Pass 4 user lock workflow yet.
