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

Every solver incumbent and benchmark is independently replayed. An invalid candidate cannot be displayed as feasible. An incomplete candidate is compared against the feasible benchmark using staged service shortfalls, weekly buffer deficits and spending (this fallback comparison does not claim the final holding-cost optimum); a better benchmark may be returned as a labeled fallback. If neither is feasible, a valid no-new-action projection can be used; otherwise the result is `invalid_plan`. A fallback has no optimality claim. No hard constraint is relaxed to improve coverage.

## Independent stock and cash replay

`simulation/replay.py` imports no optimizer code or solver variables. It reconstructs actions from normalized inputs and recommendation records, checking identifiers, supplier/lane eligibility, packs/minimums, calendars, shared capacities, receiving peaks, funding and conservation. A corrupt action is reported, never silently fixed.

Opening usable stock is on-hand minus blocked and reserved once. Already dispatched transfers are in transit, not deducted from the opening snapshot again; confirmed transfers dispatch once. Received POs add no stock but can have unpaid installments. Existing transfers' unpaid charges must be in Payables; new grouped fees apply once per lane and dispatch day. Adding units to an already-confirmed dispatch group does not charge its fee again. SupplierCapacity means remaining availability for new orders, so existing POs are not subtracted a second time.

Donor protection applies only when dispatching: maximum cumulative next-seven-day forecast less confirmed receipts on their actual dates, plus the store buffer. Speculative new receipts cannot justify depleting a donor. Lookahead after day 56 repeats the final forecast week. Shortages are lost sales and never backlogged. Later round trips are exposed for ledger inspection; the UI makes no claim of a uniquely necessary transfer.

Supply prices are required at SAR-cent precision. Line values and deposits use decimal half-up cents; balance equals full line value minus deposit. Both installments consume their actual due weeks, including when they fall in the same week. Existing unpaid obligations consume payment capacity, not the remaining authority for new purchase commitments. Existing breaches are input failures with the affected week.

Inventory investment carries acquisition value at weighted-average cost on internal movements and includes blocked/reserved stock. Revenue exposure is unmet visible units × declared net selling price, not proven lost revenue. No tax, revenue receipts, receivables or accounting cash-flow forecast is implied. Day-56 excess compares usable stock against the next seven days plus store buffers, repeating the final forecast week; DC coverage uses net store need without a second buffer.

## API and interface

Plan Review renders Python totals, purchase actions, shared allocations, cash weeks, class/store targets, individual SKU/store shortages and reason-coded exceptions. Expandable evidence provides source/destination daily stock, payment dates, forecast versions, solver stages and assumptions. Only the proposed plan carries the full daily ledger; comparisons retain policy actions, service, cash and totals. The full normalized input dataset is never echoed.

Loading clears the prior result; changing the planning dataset or recalculating updates the whole result from one API response. Aborted requests cannot overwrite newer UI state. Server calculation continues after a browser abort; the shared process semaphore returns 429 with retry guidance while it finishes. This is per-process admission control, not distributed scheduling. No plan is persisted or released to suppliers.

Scenarios, reviewed edits/locks, workbook workflows, exports and hosted release audit remain later passes. Existing confirmed transactions are fixed input actions; there is no Pass 4 user lock workflow yet.
