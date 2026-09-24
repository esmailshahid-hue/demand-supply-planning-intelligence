# Sample v3: ex-ante calibration record

The full sample is the healthier network demonstration; the ten-SKU fixture remains the unchanged severe funding-stress calculation. Neither is an operational recommendation.

## Frozen before withheld evaluation

Full input SHA-256: `bdc81b2b648bce19e4f0d33fe94c880f78daeaf8a4d2e10976a769d83dc28fcf`.

Rules selected using origin-visible inputs and modeled replay only:

- Opening inventory: fourteen days of trailing 56-day uncensored, open, non-event observed sales, rounded up to ten units. Exclude observations unavailable at the origin midnight. DC rate is the sum of its stores. Preserve original SKU001 imbalance, SKU004 supplier-shortage stock and SKU008 late-inbound stock.
- Full commitment/payment authority: SAR 140,000 per week for the opening fortnight, SAR 220,000 thereafter; transfer allowance remains SAR 1,200.
- Monday/Thursday dispatch opportunities with 3,500 units per DC lane per opportunity: unchanged 7,000-unit weekly capacity. DC packs are 300 units; store-to-store packs remain ten. This retains the existing 28-day protection envelope, including the fourteen-day supplier path.
- Supplier MOQ is 600 units, divisible by existing ten/twelve-unit cases and equal to unchanged daily SKU capacity. SKU004's initial fourteen-day zero capacity, supplier shared limits, lead times, prices, payment dates, offer validity and confirmed obligations remain unchanged.

A preliminary modeled candidate with small supplier lots produced 1,457 purchase lines and a 5.56 MB complete response; it was rejected before any withheld evaluation. A weekly-only lane calendar exceeded the existing protection envelope and was rejected without relaxing that check. The frozen candidate produces 174 purchase lines and 559 movements, 86.16% modeled visible fill versus 49.28% no action, and approximately 4.050 MB complete / 1.192 MB compact responses. Shortages occur in 133 of 240 modeled series instead of 235; lane capacity, supplier availability and commitment minima still restrict actions. More consolidation would require a planning-policy change and is deferred.

No forecast selection, optimizer, benchmark or independent-replay implementation changed. Complete forecast-quantity hashes are unchanged for both sizes. Fixture calculation hash is unchanged. Full hashes were deliberately refreshed; tests pin the new input, all actions/calculations and unchanged observed history and oracle truth. The offline truth never enters `Dataset` or API responses.

The final evaluation uses the existing four weekly releases and observed-stock execution guard. A no-new-action comparator is added to the same simulator, with the same starting inventory, confirmed inbound, obligations and truth. It does not change the proposed/benchmark evaluation definition. No inputs were adjusted after inspecting that final evaluation.

## Frozen-input withheld result

Full: **85.7451%** fill (89,469 / 104,343 units), **14,874 unmet**, versus **48.2744%** no action. The 37.47-point benefit comes from more appropriate synthetic stock, funding and lot assumptions, not a better algorithm; proposed and benchmark releases remain identical. Initial stock is 99,485 units versus v2's 38,975, and the modeled policy commits SAR 892,200 versus v2's SAR 186,336. Higher inventory and authority are real assumptions, not free improvements.

Concrete binding evidence in the initial plan: thirty DC lane/date groups use 3,300 of 3,500 units, leaving less than the next permitted 300-unit pack. The week of 28 September commits SAR 219,000 of 220,000, leaving less than the cheapest 600-unit supplier lot. SKU004 cannot dispatch new supplier stock until 28 September because its first fourteen capacity dates are zero. These are unchanged hard constraints applied to calibrated data, not just labels on a healthy unconstrained plan.

144 of 240 series have some realized shortage, versus 133 with modeled visible shortages; this is reduced but not a handful of isolated products. **8,883 units (59.7%) of realized unmet demand occur in week three**, as initial store cover runs out and scheduled replenishment/lane lots constrain service. Weekly fill is 97.36%, 95.67%, 65.77%, 84.09%. SKU008's late-inbound stores and SKU004's supplier-shortage stores remain prominent shortage cases. The full policy releases 94 purchases and 271 executed movements over four weeks (distinct from the initial 56-day plan's 174 / 559).

Two store-to-store movements are cancelled by the unchanged observed-stock/origin-reserve guard: `T-SKU006-S2-S1-0` on 28 September and `T-SKU017-S2-S1-3` on 8 October. They are disclosed execution deviations, not silently feasible dispatches. Every origin plan independently replays; all executed stock/value/cash conservation and dated funding checks pass. Full realized commitments / payments in the four weeks / future payables are SAR 474,600 / 239,220 / 239,500, with SAR 720 movement expense and exact reconciliation including SAR 3,400 existing obligations.

Fixture remains 48.0418% fill, 9,154 unmet, versus 19.6674% no action; zero cancellations. Same forecast-quantity hashes and separately held truth as v2. Detailed run evidence is in [BUILD_STATUS.md](BUILD_STATUS.md). Remaining fragmentation and conservative allocation are deferred planning-policy limitations, not reopened in this data correction.
