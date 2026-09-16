# Demand and Supply Planning Intelligence

## Build specification and implementation prompts

Version: 1.1, 16 September 2026  
Owner: Esmail Arshad  
Status: Ready for implementation; application not yet built  
Recommended repository location: `docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md`

This Markdown file is the working specification for the first public MVP. It refines the earlier Word plan into implementation requirements, acceptance checks and six reusable prompts. Where scope differs, this file defines the MVP; the Word document remains background rationale. The changes are explicit below.

## 1. Delivery decision

Build in **six ordered passes: five implementation passes and one audit and release pass**. Allow one or two focused correction passes if verification exposes defects. This is an engineering estimate, not a guarantee that exactly six model calls will finish the application.

Do not attempt the complete product as one undifferentiated generation. Its difficult parts are forecast evaluation, shared stock allocation, date handling and financial reconciliation. These need inspectable results before the interface can be trusted.

A single kickoff instruction can authorize an agent to work through all six passes sequentially. The user does not need to approve routine progress between them. Alternatively, use the six prompts in section 15 in separate coding sessions. The stages and gates remain the same in either mode.

Keep one repository and one calculation implementation. Every screen, scenario and export must use the same engine results. Maintain `docs/BUILD_STATUS.md` during implementation so a new session can resume without reconstructing decisions from chat.

### What has been narrowed from the Word plan

| Area | First public MVP |
|---|---|
| Navigation | Four primary screens; purchasing and allocation appear within the plan workspace. |
| Imports | One documented XLSX template; a second CSV ZIP importer is deferred. |
| Forecasts | Three transparent weekday methods with historical evaluation. Additional statistical methods are deferred. |
| Scenarios | Demand uplift, supplier delay/capacity loss, purchase budget and payment ceiling. Lane closures and alternate commercial terms are deferred. |
| Action review | Accept, reject or edit quantity; rerun the complete plan. Rich approval routing and multi-user history are deferred. |
| Persistence | Session state plus a portable plan snapshot and action export. Accounts and a database are deferred. |
| Execution reconciliation | Stable external IDs and duplicate detection in fresh uploads. A dedicated plan-adherence dashboard is deferred. |
| AI | Defer narration until after the MVP is released and useful without it. |
| Hosting | Prefer one service serving the built frontend and calculation API. Avoid adding a second deployment unless the existing environment makes that easier. |

Joint allocation, forecast evaluation, funding constraints, scenario comparisons and independent feasibility checks remain required.

## 2. Product and audience

**Operating question:** What should we buy, move or defer over the next four weeks, given expected demand, available stock, supplier constraints and limited purchasing funds?

Primary user: a demand/supply planner reviewing the next week's actions. Secondary viewers: a commercial lead and a finance reviewer.

Ninja is the primary operating reference. Sary/SILQ and Nana are secondary adaptation targets. Treat this as an independent Saudi retail planning example. Do not claim that any target company lacks these capabilities or supplied data. Wholesale adaptations require changes to demand grain and replenishment responsibilities; changing logos is insufficient.

The portfolio should demonstrate planning and inventory judgment alongside the logistics skills shown in Freight Fulfillment Intelligence. Freight corresponds to direction 4 in the opportunity map. This project expands direction 6.

### What a connection should see in a three-minute demo

1. A demand forecast with a visible reason for selection and an honest evaluation record.
2. A store shortage resolved through a dated transfer or purchase without overallocating shared stock.
3. A tighter budget or supplier delay changing the recommended plan and projected service.
4. The quantities, payment dates and remaining shortages behind that decision.
5. A reviewed plan exported for action.

The outcome is a credible discussion with a planning leader. Enterprise integrations and a large feature count are not prerequisites for that discussion.

## 3. Fixed initial operating scope

| Setting | Default |
|---|---|
| Geography | Fictional Riyadh metro retail network; SAR; Asia/Riyadh dates |
| Network | One DC and four stores; suppliers deliver to the DC |
| SKU scope | 60 ambient packaged SKUs; no expiry, substitutions or fresh-food modeling |
| Suppliers | 12; approved SKU offers with dated availability |
| Demand history | 420 days, excluding unranged or closed periods appropriately |
| Visible decision window | 28 days |
| Model horizon | 56 days; days 29–56 are a separately labeled provisional tail |
| Release review | Next seven days are actionable; later actions remain planned |
| Supplier lead time | Up to 14 days; order and receiving calendars apply |
| Internal transit | One or two days; no instantaneous transfers |
| Payment schedule | At least 90 days or the last modeled due date, whichever is later |
| Products and orders | Base units for stock; integer case quantities for purchase and movement |
| Demand treatment | Daily expected demand; unserved demand is lost, not carried forward |
| Service policy | Illustrative class A/B/C fill targets of 98/95/90 percent |

Start implementation on a 10-SKU fixture. Expand to the full sample only after the model reconciles. Reducing sample size after a measured runtime failure is acceptable; dropping shared allocation or funding checks is not.

No new purchase may arrive after the modeled inventory horizon. Inputs outside the supported timing envelope must be rejected or handled through an explicitly extended horizon. The interface must never silently shorten a lead time.

## 4. Architecture and development method

Use React and TypeScript for the interface and a Python service for forecasting, inventory simulation and constrained planning. Use the repository's established stack where it fits. For a new repository, keep the frontend build simple and expose a small calculation API.

The proposed solver is SciPy's mixed-integer interface to HiGHS. It supports integer decisions and reports statuses and solution gaps. These are useful for case quantities, conditional order minimums and shared funding limits. Validate the formulation and runtime in pass 2 before depending on it throughout the UI. [SciPy documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)

Prefer a single containerized service that serves the compiled frontend and Python API. This avoids separate frontend/backend deployment configuration for the MVP. Confirm the actual available hosting environment during pass 1, and verify compatibility with the solver. Do not choose a paid host or create infrastructure merely because it appears in an example.

Suggested logical modules, adjusted to the repository's conventions:

- `contracts`: request, dataset, result and error schemas; generated frontend types where practical.
- `data`: parsers, validation, sample generation and small fixtures.
- `forecasting`: candidates, rolling evaluation, eligibility and overrides.
- `simulation`: independent daily stock and cash replay.
- `planning`: benchmark policy and constrained joint model.
- `scenarios`: immutable changes and comparable evaluations.
- `exports`: reviewed action workbook and portable snapshot.
- `ui`: four screens using returned results, with no duplicate business calculations.

Keep calculation requests bounded. Validate upload size and supported dimensions before solving. Limit concurrent solves and apply an overall runtime budget across all objective stages. Measure cold and warm runs. Default target: a full sample plan in 30 seconds or less on the selected host; this is a target to verify, not an existing performance claim.

### Data handling

The calculation service receives normalized operational data. The browser-only privacy wording from Freight Fulfillment Intelligence does not apply. Disclose server processing before upload calculation. Avoid raw-row logs, isolate concurrent sessions and remove temporary uploads after processing. Verify actual host retention before making retention claims.

Cache or bundle a generated sample result for quick first load if useful. Mark it as a sample snapshot, retain its data/engine version and provide live recalculation. Never return that snapshot as the result of a different scenario or uploaded dataset.

## 5. Data contract and validation

Use one workbook with separate, named sheets and explicit primary keys. Do not place two incompatible row types in a sheet.

| Sheet | Grain and required information |
|---|---|
| `Products` | SKU; base unit, case conversion, volume per unit, cost reference, net price, category, active dates |
| `Locations` | Location; DC/store type, storage volume, calendar |
| `Assortment` | SKU-location; ranged dates, service class, must-stock flag |
| `DemandHistory` | SKU-store-date; sales units, open status, stock availability, event ID, observation availability timestamp |
| `Inventory` | SKU-location-as-of; on-hand, blocked, reserved and book unit cost |
| `OpenOrders` | PO line; external ID, supplier, destination, remaining units, order/dispatch/arrival dates, status and cost |
| `OpenTransfers` | Movement line; external ID, SKU, source, destination, remaining units, dates and status |
| `SupplierOffers` | Supplier-SKU-validity; base-unit price, case size, MOQ, lead time, dispatch calendar, payment terms |
| `Suppliers` | Supplier; minimum order value and any shared capacity rule with its unit |
| `SupplierCapacity` | Supplier-SKU-dispatch date; available quantity and any shared limit reference |
| `TransferLanes` | Source-destination; transit, dispatch calendar, capacity, fees, pack rule and SKU restrictions |
| `Payables` | Unpaid installment; external ID, due date, amount and linked PO/movement ID |
| `Budgets` | Week; available new-order commitment cap, payment ceiling and transfer budget |
| `Events` | Event scope and dates; uplift or replacement, reason and known-at timestamp |
| `Settings` | Named value; as-of date, targets, review period, buffers and holding-rate assumption |

An empty transaction sheet means no records only when the user explicitly declares this. Missing capacity is unknown, not unlimited. Missing funding data permits only a clearly labeled unfunded exploration, not an accepted funded plan.

Block invalid IDs, duplicate keys, incompatible units, negative usable stock, conflicting snapshots, impossible dates and incomplete funding coverage. Validate pack conversions and shared-capacity units. Prices must clearly state whether they are per base unit or per case; normalize once.

Usable stock = on-hand minus blocked minus reserved. Do not subtract a reservation twice through both stock and demand. Describe what reservations mean in the template. Received-but-unpaid POs are cash obligations, not future stock.

Show a separate historical-data quality warning for missing or stockout-censored sales. An available, open product with zero sales is a valid zero. A closed or unranged day is not demand evidence. Unknown observations remain unknown.

## 6. Forecasting requirements

### Candidate methods and selection

Implement seasonal naive, four-week same-weekday mean and recency-weighted same-weekday mean. The latter uses 40/30/20/10 percent weights from most to least recent, renormalized over eligible observations. Preserve explicit fallbacks for missing weekdays.

Evaluate using rolling origins and only information available before each origin. The final 28 days are reserved as a final check; earlier windows select the model. Compare 7-day and 28-day quantities and report protection-period error where the history supports it. Rolling-origin evaluation avoids training on future observations. [Forecasting Principles and Practice](https://otexts.com/fpp3/tscv.html)

Require four evaluable 28-day selection windows. If these are unavailable, retain the baseline with provisional status. Choose a challenger only when its mean absolute 28-day error improves by at least 5 percent and its absolute bias does not worsen. Treat that threshold as a product default, not a statistical significance claim. If baseline error is zero, retain it unless a documented tie rule applies.

Report absolute error, pooled WAPE, signed bias, horizon, valid observations and excluded coverage. Positive bias means overforecasting. A zero actual-demand denominator makes percentage metrics unavailable. Do not average SKU percentages into a network WAPE.

### Historical stockouts and events

Keep observed sales and estimated demand separate. Use only prior eligible observations to estimate censored training values. Evaluate observed accuracy on uncensored dates. Never score an estimate as if it were known actual demand.

Exclude known promotion days from ordinary-weekday baseline pools, or remove their uplift only when that factor was known at the forecast origin. Record the choice. Applying future event uplift to an already inflated baseline must not double-count the event.

Apply dated events and explicit overrides after the baseline. Store scope, dates, reason, original and revised quantities. Reject ambiguous overlapping rules. A forecast change invalidates dependent plan versions.

Short-history and new SKUs use a labeled launch estimate or selected analogue. Do not fabricate accuracy statistics. All-zero and intermittent series need conservative, explainable fallbacks.

### Inventory protection

Use cumulative historical underforecast errors over the relevant protection period to estimate a buffer, with a configurable percentile and a disclosed sample count. The initial percentile is 90. It is not a guaranteed fill rate. With insufficient evidence, use an explicitly labeled days-of-demand buffer.

The DC has no retail demand. Aggregate store requirements without counting independent DC sales or duplicate network buffers. Apply the same policy assumptions to the proposed and benchmark plans.

## 7. Inventory and joint purchasing contract

### Daily event order

For each SKU-location-day:

1. Receive arrivals scheduled for that day.
2. Serve local demand from usable stock.
3. Dispatch permitted internal movements from remaining stock.
4. Record closing stock, unserved demand and inventory in transit.

Fulfilled units must equal the lesser of local demand and usable stock before dispatch. Do not allow artificial demand withholding. Stock leaves the donor on dispatch and becomes usable at the receiver only on arrival. Daily buckets cannot prove intraday availability.

Enforce conservation of stock across locations and transit. Respect receiving peak volume before demand reduces inventory. Confirmed future receipts cannot be borrowed early.

### Shared decisions

Solve purchases and movements across the network together. Two stores cannot claim the same DC stock. Multiple orders share supplier availability, lane capacity, budgets and grouped fixed fees.

Purchase units are integer case multiples. Apply line MOQ only when ordered. Apply a supplier minimum order value once per supplier-order date, across its lines. Orders must use approved offers and valid calendars. New direct-to-store supply and unapproved suppliers are outside the MVP.

Internal transfers must protect local demand and the donor reserve. Enforce reserve requirements conditionally when a transfer is dispatched; a store already below reserve must not make a no-transfer plan infeasible.

Calculate a conservative donor reserve from the maximum cumulative net need over the next seven days, plus its buffer. Account for confirmed receipts on their actual dates, not simply total receipts during the week. A late receipt cannot offset an earlier shortage. Exclude speculative replenishment from this reserve calculation. For lookahead past day 56, repeat the final forecast week and label that terminal assumption.

Prevent opposing same-SKU lane movements on the same day and explain any later round trip. Avoid positive-cost movements with no stated planning benefit.

### Objective and solver status

Use documented staged objectives. Minimize unmet service targets by must-stock and A/B/C priorities in the visible window, then in the provisional tail. Preserve attained higher-priority results while solving lower stages. Then minimize weekly buffer deficits within the same hard limits. Finally reduce commitment, movement and holding costs, with stable tie-breaks for unnecessary actions.

Service shortfall is measured by class-store, with SKU detail always visible. Buffer and target shortfalls may remain. Physical and funding limits may not be silently relaxed. This is a service-policy planning model, not a claim to maximize accounting profit.

Every stage must share one overall runtime limit. Report which stages finished and the final feasible status. If a higher-priority stage times out, do not claim full lexicographic optimality. Preserve a validated incumbent or return a clearly labeled fallback.

Before showing any plan as feasible, replay its actions in a separate stock and cash simulator. The simulator must not merely report that the solver returned success. Include minimums, shared limits, timing and locked decisions in validation.

### Benchmark

Build an order-up-to benchmark with the same forecast, buffers, calendars, stock and funding limits. Allocate by earliest shortage and service priority, then place case-rounded purchases from the cheapest eligible on-time source. Use stable ordering and report remaining shortages.

Display both this benchmark and the current projection with no new actions. Do not claim value solely against doing nothing. Do not label the benchmark as a target company's existing process.

## 8. Cash and service contract

| Measure | Meaning |
|---|---|
| Purchase commitments | Full new purchase value by order week; visible and tail amounts separated |
| Scheduled payments | Existing unpaid installments plus new deposits/balances and movement fees, by due week |
| Payment headroom | Ceiling minus payments; an allowance, not a projected bank balance |
| Inventory investment | On-hand plus in-transit inventory at declared acquisition cost |
| Projected unit fill | Fulfilled forecast units / forecast units; aggregate from units |
| Unmet units | Unserved demand by date, SKU, store and class |
| Revenue exposure | Unmet units times assumed net selling price; modeled, not proven lost revenue |
| Contribution exposure | Only where a declared contribution input supports it; not added to revenue exposure |
| Excess | Stock above the stated coverage-plus-buffer policy, with its date and assumption |

Support a deposit at order and a balance due after receipt, up to 30 days for the sample. Count each unpaid obligation once. A received PO can still require payment. A transfer changes the location of inventory value but does not create purchase spend.

Treat commitment caps as remaining authority for new orders; existing unpaid obligations consume payment ceilings. Keep those semantics explicit in the template. Apply transfer fees once per actual grouped dispatch. Existing obligations that already breach a payment ceiling must be shown; no funded acceptance is allowed without an explicit corrected limit.

Do not hide payments beyond day 28. Export through at least day 90 or the final due date. Missing limits in an affected week block funded acceptance. Costs and invoice cash amounts must use documented input conventions; tax and receivables modeling are out of scope.

## 9. Scenarios and review workflow

Required controls:

- Dated demand uplift for a SKU, category or store.
- Selected supplier receipt delay or availability reduction.
- Weekly new-commitment limit.
- Weekly payment ceiling.

Provide three named demo scenarios: promotion, supplier disruption and tighter funds. Permit combinations. Every scenario preserves the original snapshot and lists its changes.

Offer two evaluations: freeze baseline actions under changed assumptions, and replan under those same assumptions. Compare these directly to distinguish the shock from the value of replanning. Keep original baseline outcomes available separately.

Show fill rate, unmet units, commitments, weekly payments, inventory investment and movement expense. For funding changes, show additional service per extra SAR only when the denominator is positive and meaningful. A few evaluated alternatives are not a complete efficient frontier.

Action states: draft, accepted, rejected and stale. Accepting an action locks it in the next solve; rejecting it prohibits the specified candidate; editing quantity creates a reviewed requirement. Rerun dependencies before final plan acceptance. A rejected supplier order must invalidate dependent transfers until replacement supply is validated.

Final acceptance creates a versioned snapshot and an export. It does not send orders. Unsupported service targets can be acknowledged when hard constraints pass. Stale or physically invalid plans cannot receive an accepted export.

On later imports, reconcile external order/movement IDs so a confirmed execution replaces its proposal. Never count both. Advanced historical adherence reporting is deferred.

## 10. Interface and exports

| Screen | Must support |
|---|---|
| Plan Review | Sample loads first; comparison metrics, purchases/movements, unresolved shortages, review state and linked inventory/cash detail |
| Demand Review | Forecast versus observations, evaluation record, censored periods, selected method and dated override |
| Scenarios | Clear controls, run progress, baseline/frozen/replanned outcomes, changed actions and reset |
| Data and Assumptions | Download template, upload, grouped validation messages, limits, defaults and sample reset |

The Plan Review action drawer shows source, destination, SKU, quantity, order/dispatch/arrival dates, cost and payment schedule, forecast version, dependencies and before/after stock. Purchasing and allocation are detail views within this workspace rather than separate primary navigation.

Use a small, coherent visual system established in pass 1. Finish a readable desktop flow first, then responsive summaries and keyboard interaction. Wide tables may scroll deliberately. Show projected versus observed values and uncertainty in text. A user should understand the first screen without reading the specification.

Export one workbook containing purchase actions, movements, unresolved exceptions, payment schedule, metrics and assumptions. Include run ID, as-of date, engine/schema versions, input hash and solver/validator status. Export a portable snapshot sufficient to reopen a reviewed plan. Keep technical metadata in details and files rather than prominent product copy.

## 11. Evidence and release definition

### Hand-calculated fixture

One SKU, seven days, case size 10, no buffers or holding charge:

- Store A starts with 20 units and sells 10 per day.
- Store B starts with 100 units and sells 5 per day.
- A transfer after day 1 arrives at the start of day 3 and costs SAR 20.
- A supplier purchase reaches the DC on day 3 and A on day 4; units cost SAR 10, with half paid at order and half 30 days after DC receipt. DC dispatch costs SAR 20.

| Alternative | Unmet units | Ending network stock | New purchase commitment | Cash paid in seven days |
|---|---:|---:|---:|---:|
| No new action | 50 | 65 | 0 | 0 |
| Transfer 50 from B to A | 0 | 15 | 0 | 20 |
| Buy 40 and move DC to A | 10 | 65 | 400 | 220 |

The third alternative leaves SAR 200 payable later. Assert these quantities independently of solver output. Add a donor-demand increase and a second receiver to expose infeasible transfers and duplicated allocation.

### Full-sample cases

Generate true demand first, then availability and observed sales, using a fixed seed. Keep future truth and expected case labels outside runtime planning inputs.

Required cases: uneven stock, censored history, dated promotion, supplier shortage, tight funding, large MOQ, new product, late inbound, healthy control and day-29 demand. Cases must emerge from inputs and calculations, not scenario-name-specific hard-coded recommendations.

Use meaningful checks for:

- Forecast leakage, zero denominators and incomplete history.
- Stock conservation, receipt timing and daily service before movement.
- Supplier minimums, integer cases, shared supplier/lane limits and receiving volume.
- Funding reconciliation including deposits, unpaid balances and late payments.
- Stale action dependencies, immutable scenario reset and export reconciliation.
- Solver timeout, contradictory locks and insufficient inputs.
- End-of-window effects and donor protection with late receipts.

Run an offline weekly replay on withheld synthetic demand for both proposed and benchmark policies. Expose only information available at each origin. Compare simulated realized service, spending and average inventory. Do not tune on the final evaluation period or promise an improvement the evidence does not show.

Release requires a functioning live recalculation, the upload-to-export workflow, a reconciled hand fixture, passing hard constraints and an honest benchmark comparison. It does not require the proposed policy to outperform the benchmark on every metric. Report the trade-offs.

## 12. Six implementation passes

| Pass | Scope | Exit gate |
|---|---|---|
| 1 | Repository, contracts, fixtures, forecast evaluation, minimal interface and deployment skeleton | One sample travels through a real API into the UI; forecast evaluation and a deployment smoke test work |
| 2 | Benchmark, joint purchasing/allocation, stock replay and payment engine | Hand fixture reconciles; full sample is feasible or honestly reports shortages; runtime measured |
| 3 | Complete sample-data product and scenarios | A connection can review a forecast, inspect an action and rerun a shock through the live engine |
| 4 | User workbook, review/edit dependencies, accepted export and portable snapshot | Sample exported as input can be reuploaded and reproduce results; invalid input and stale exports are blocked |
| 5 | Product finish, responsive behavior, model failure handling and documentation | Demo is clear and usable; all required features are real and feature scope is frozen |
| 6 | Audit, focused corrections, hosted end-to-end verification and demo evidence | Hosted upload, recalculation, scenario, acceptance and export reconcile to the engine; material defects resolved |

Pass 1 is a working foundation, not a large scaffolding exercise. Pass 2 is the main modeling gate. Pass 3 yields the first useful private demo, but the external showcase follows pass 6.

Re-run tests affected by each change. Do not spend entire phases adding tests that mirror simple rendering code. The hard model invariants and end-to-end user workflow deserve verification.

## 13. Session and handoff protocol

Every coding session reads this file, applicable repository instructions and `docs/BUILD_STATUS.md`. It inspects existing work before editing. It does not regenerate the project because a new prompt arrived.

At the end of each pass, update `docs/BUILD_STATUS.md` with:

- Completed pass and exact acceptance evidence.
- Actual test/build commands and their results.
- Relevant measured runtime and environment.
- Contract, model or scope decisions and their reasons.
- Remaining defects and whether they block the next pass.
- Next pass and a short list of files/modules it should use.

Report only checks actually executed. A gate is not complete because the code contains a feature name. Preserve existing user changes, avoid unrelated refactors and never put credentials or uploaded operational rows in commits or logs.

Routine fixes belong inside the current pass. A correction pass is for a specific remaining issue discovered after a gate. Do not add broad feature expansion under the heading of audit.

## 14. One kickoff prompt for an autonomous build

Use this when the repository and execution environment are available and the user has authorized application implementation. This prompt runs a phased build; it does not waive the checkpoints or grant new external-service permissions.

```text
Build Demand and Supply Planning Intelligence using
docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md as the MVP specification.

Read applicable repository instructions and docs/BUILD_STATUS.md if present.
Inspect existing code before choosing or changing the stack. Implement the
six passes in order, validating and recording each exit gate before moving
on. Continue through routine implementation and corrections without asking
me to approve each phase. Resolve routine design choices using the plan.

Keep forecast evaluation, joint feasible purchasing/allocation, funding
constraints and scenario comparisons as mandatory capabilities. Use one
calculation implementation for screens and exports. Do not add deferred
features or substitute static data for a requested live calculation.

Maintain docs/BUILD_STATUS.md so another session can resume. Report actual
tests, measured limitations and material blockers honestly. Respect existing
authorization and access constraints for hosting and external services.
If release access is unavailable, finish and verify everything locally and
identify the exact remaining deployment dependency.

The final outcome is a working, verified MVP suitable for a short demo to
planning leaders at MENA startups, with clear synthetic-data labeling and
a concise case study grounded in the application's actual results.
```

## 15. Six prompts for separate build sessions

Use the following prompts sequentially if working interactively. Keep the same repository and the latest committed build state. Each prompt already includes verification; a seventh generic test prompt is unnecessary.

### Prompt 1 — Working foundation and forecasting

```text
Implement pass 1 of docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md.
Read the complete specification, applicable repository instructions and
docs/BUILD_STATUS.md. Inspect existing code and preserve useful work.

Create the minimum working application and shared contracts. Establish the
single-service deployment skeleton where the environment supports it.
Build the seeded small fixture and full sample generator, validation,
forecast candidates, historical evaluation and provisional fallbacks.
Display a real forecast result and evaluation record through the API in a
minimal coherent interface. Define the four-screen navigation and visual
tokens without building placeholder dashboards.

Test historical leakage, missing/censored observations, short histories and
zero denominators. Verify a local production-style startup and deployment
compatibility. Record hosting access limitations rather than inventing a
successful deployment. Finish the pass 1 gate and update BUILD_STATUS with
results and the exact handoff for pass 2. Do not build deferred features.
```

### Prompt 2 — Feasible purchasing and allocation

```text
Implement pass 2 of docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md.
Read the specification and BUILD_STATUS; use the existing contracts and
forecast results. Do not rebuild the repository or frontend.

Build the no-new-action projection, constrained benchmark policy, joint
purchasing/allocation model and independent daily stock/cash replay.
Enforce case multiples, conditional minimums, dated shared capacity,
receiving volume, donor protection, order commitments and payment limits.
Implement the staged service policy, provisional tail, explicit residual
shortages and honest solver/fallback states.

First reconcile the hand-calculated fixture, then adversarial cases and the
full sample. Measure total runtime across objective stages. Investigate any
invariant failure rather than masking it in the UI. Explain any justified
runtime scope adjustment before recording the changed limit in the spec.
Expose real plan results through the API and a minimal inspection view.
Complete the pass 2 gate and document evidence and remaining limitations.
```

### Prompt 3 — Sample product and scenario decisions

```text
Implement pass 3 of docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md using the validated
engine. Read BUILD_STATUS and do not change model contracts casually.

Build Plan Review, Demand Review and Scenarios for the full sample. Add
linked stock/cash detail, understandable action explanations and visible
unresolved shortages. Implement demand uplift, supplier delay/capacity
loss, commitment limits and payment ceilings. Compare frozen baseline
actions and replanned actions under identical scenario assumptions.

Make the initial experience useful without an upload or a tutorial. Show
progress and honest result status. Verify live recalculation, reset,
baseline immutability and reconciliation between displayed metrics and
the ledger. Do not use hard-coded scenario recommendations. Complete the
first private-demo flow and update BUILD_STATUS with the pass 3 evidence.
```

### Prompt 4 — Own data and reviewed action output

```text
Implement pass 4 of docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md. Preserve the
working sample flow and use its contracts for uploaded data.

Provide the documented XLSX template, parser, validation messages and
server-processing disclosure. Implement accept/reject/quantity-edit
decisions, dependent-plan invalidation, regeneration and final acceptance.
Export the reviewed action workbook and a portable versioned snapshot.
Use external transaction IDs to prevent double-counting confirmed actions
when data is refreshed.

Verify a template round trip, invalid and incomplete files, a rejected
upstream purchase with dependent transfers, an edited quantity, stale
export blocking and exact cash/action reconciliation in the final export.
Complete the pass 4 gate and update BUILD_STATUS. Do not add accounts,
live integrations, another import format or approval-routing software.
```

### Prompt 5 — Product finish and scope freeze

```text
Complete pass 5 of docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md. Read the current
status and resolve remaining in-scope usability and runtime issues.

Finish desktop and mobile behavior, keyboard interaction, readable tables,
clear financial labels, empty/loading/error states and useful scenario
entry points. Exercise solver timeouts, incomplete funding and conflicting
review locks. Add documented limits, calculation explanations and concise
setup/run instructions. Show where sample results are precomputed, if any.

Run the affected model checks and the complete local user flow. Prepare the
short operator-demo sequence using actual results. Freeze feature scope
once the required workflow is coherent. Do not add AI narration, extra
dashboards or integrations. Record pass 5 evidence and remaining release
risks in BUILD_STATUS.
```

### Prompt 6 — Audit and hosted release verification

```text
Perform pass 6 of docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md. Audit the current
implementation against the specification before changing anything.

Trace forecast evaluation, a purchase, a transfer, a cash installment and
a scenario delta from input to displayed result and export. Run withheld
synthetic policy replay and report benchmark trade-offs honestly. Verify
the hand fixture, hard constraints, dependency invalidation and failure
states. Fix material discrepancies with targeted changes and recheck the
affected calculations. Do not redesign or broaden scope.

Use the authorized hosting environment to deploy and verify the real
application end to end: first load, live recalculation, scenario, uploaded
workbook, action review and export. Check CPU/time limits, session isolation
and actual data-handling behavior. If access is unavailable, complete the
local release and state the precise outstanding deployment dependency.

Finish with the verified URL if available, actual verification results,
known limitations, concise portfolio copy and the three-minute demo flow.
Mark the release complete only when its required checks have passed.
```

## 16. Stop conditions and definition of done

The MVP is ready to share after pass 6 when:

- Forecast selection and its limitations can be explained from the displayed evidence.
- Every recommended purchase and movement satisfies independently checked physical and funding constraints.
- All four required scenario controls recompute real results.
- Commitment, scheduled payments and inventory value reconcile separately.
- Both the sample and documented own-data workflow reach reviewed export.
- Remaining shortages, provisional tail decisions and solver limitations are visible.
- A connection can follow the short demo without understanding the implementation.
- Public claims describe an independent synthetic portfolio project and do not imply customer deployment or verified real-world savings.

If a material check fails, use a bounded correction prompt naming the defect, affected contract and required evidence. Do not restart the product or commission another open-ended audit by default.

No universal prompt count or performance guarantee is possible before the code is built and measured. The six-pass structure is the recommended route to a reviewable MVP with controlled scope.
