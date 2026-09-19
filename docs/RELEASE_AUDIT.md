# Pass 6 release evidence — 19–20 September 2026

Reviewed baseline: `599554c3ad4e44c47b0461eff3fac921318ea606`, initially clean. [GitHub Actions 35461717511](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35461717511), job `105946650205`, completed successfully on Ubuntu 24.04.5: 168 backend tests, 26 browser tests, solver, reproducible contracts, production build, Docker build/start, forecast/planning/scenario smokes, container profiling and private workflow smoke. **Pass 5 is closed for that commit.** These results do not certify the new Pass 6 worktree.

The canonical [public sample application](https://demand-supply-planning-intelligence.vercel.app) was independently verified through Vercel deployment metadata: project `prj_9wUSzLP3zKbvVinWCeNvmyDelVh5`, deployment `dpl_FDjfTcpkSijxKDgpnJRHf5owkojH`, production alias, `iad1`, commit `599554c`. The second `-hahy` project was not treated as canonical. No push, merge, deployment or project-setting change was performed.

## Verdict and release boundaries

- Pass 5: **closed**, based on successful exact-commit CI above.
- Pass 6: local audit and focused correction implemented; **release gate blocked** by hosted full-sample latency, hosted private storage and unverified corrected-commit CI/deployment.
- Public sample demo: working forecast, planning and scenarios verified; **not release-ready against the retained 10-second planning gate**. Full-sample HTTP took 17.022 / 14.929 seconds. Do not market it as meeting that limit.
- Full hosted own-data workflow: **blocked**. The server reports storage disabled, and no private hosted adapter exists. Local upload/review/accept/export/reopen passed; that is a different environment.

## Calculation trace

Reproduce against the single-worker production process:

```sh
.venv/bin/python -m scripts.release_trace --url http://127.0.0.1:8012 --output artifacts/pass6-local-trace.json
.venv/bin/python -m scripts.release_trace --url https://demand-supply-planning-intelligence.vercel.app --output artifacts/pass6-hosted-trace.json
```

The trace uses real HTTP results, checks action/cash arithmetic, and checks the accepted XLSX and portable snapshot locally. Hosted storage absence is explicitly reported; review is not attempted there. Full raw results and request timings remain in the ignored `artifacts/pass6-*` files. The scripts fail nonzero on request, malformed-response or reconciliation errors.

**Forecast:** fixture SKU001/S1, planning date 2026-09-14. The unchanged engine filters observations by strict availability before the Riyadh midnight origin; previous censor estimates never become scored actuals. Eight earlier disjoint selection origins precede the held-out period; 7 complete windows and 223/224 scored days are available. Seasonal-naive quantity MAE is 10.4285714; selected recency-weighted MAE is 7.4761905. API improvement remains 28.3105023%; displayed MAEs 10.4 / 7.5 produce the displayed 28%. Selected pooled bias is +0.1666667 units / +0.0079139%, displayed `<0.1%`. The held-out final check has 27/28 known days, so complete-period quantity MAE remains unavailable; selected pooled WAPE is 16.2681%, versus baseline 23.9130%. It does not select the method. The refitted visible forecast is 281.0666667 units, displayed 281.1. Trace: `forecasting/engine.py` → `ForecastResult` → `Demand.tsx` / `Evaluation.tsx`; API-backed browser assertions cover product/store changes and recalculation.

**Purchase:** `P-OFFER008-0`, 130 units SKU008 at SAR 11, total **SAR 1,430**. OFFER008 is valid 2025-07-21 through 2026-11-08, case 10, MOQ 20, supplier minimum SAR 500, every-day order/dispatch calendars, 14-day lead time. Order and dispatch 14 September; receipt at DC on 28 September. The S3 evidence target is the earliest reachable store shortage on 2 October; it is a demand context, not a dedicated purchase destination. DC inventory is pooled and every allocation is independently replayed. No purchase-to-store reservation is fabricated.

**Store transfer:** `T-SKU001-S2-S1-0`, 10 units. On 14 September S2 opens with 320, receives zero, serves 12, dispatches 10 and closes at **298**, above its origin-known next-seven-day reserve of **84**. Two-day lane transit places the 10-unit receipt at S1 on 16 September. S1 opens with 68.6, receives 10, serves 8.7 and closes at 69.9. The `S2-S1-2026-09-14` fee group has one **SAR 20** payment regardless of SKU count. Transfer changes stock location and adds a movement expense; it creates no purchase commitment.

**Cash:** the purchase above deposits **SAR 715 on 14 September**, with **SAR 715 balance on 28 October**, 30 days after receipt. Week 14 September has SAR 1,430 commitments against 1,500 authority, leaving 70. Payments are 715 deposit + 680 grouped movement fees = **1,395**, leaving **2,605** against the 4,000 ceiling; transfer headroom is 120 against an 800 allowance. Whole-plan commitments **91,606**, payments **97,746**, movement expense **2,740**, and opening unpaid obligations **3,400** reconcile: 91,606 + 2,740 + 3,400 = 97,746. Payment headroom is an allowance, not a bank-balance forecast. Day-56 inventory value **18,303.42** is a separate stock measure; projected visible fill **52.7191%** and unmet **7,567.4417 units** are separate service measures.

**Scenario:** increase first-week commitment allowance from 1,500 to 2,000 and payment ceiling from 4,000 to 4,500. Original and frozen actions/outcomes are identical and feasible. The validated replan has +50 visible fulfilled units, −50 visible unmet units, +0.312397 percentage points fill, −50 total commitments, −30 total payments, +20 movement expense and −540.74 ending inventory value, but **+4.8667 tail unmet units**. All deltas equal authoritative after-minus-before fields. Increased authority changes action timing; it is not proof of commercial savings. The separate combined promotion/disruption/commitment smoke retains unavailable metrics/deltas for infeasible frozen actions. Same changed-assumption hashes are required for frozen and replanned policies.

**Review/export:** change the 130-unit purchase to **120 units**. Decision marks the old plan stale; regeneration creates a distinct replacement reference and independently validated result; acceptance is possible only after the current result loads and remaining shortfalls are acknowledged. Accepted line value is **SAR 1,320**, identical in API, portable snapshot and PurchaseActions XLSX. Revised total commitments **91,496**, payments **97,696**, movement expense **2,800**, ending inventory value **18,257.82** and projected unmet **7,577.4417** match exported Summary values. Existing workbook floats are lossless decimal text; the trace parses that documented representation instead of treating text as a numeric-cell defect. Action identities and canonical provenance survive regeneration/export; reopening is read-only and a new draft requires explicit regeneration. No order is executed.

## Offline weekly policy evaluation

This missing build-plan evidence is now implemented in `scripts/policy_replay.py`, outside the runtime application. Reproduce both datasets:

```sh
.venv/bin/python -m scripts.policy_replay --size fixture --output artifacts/pass6-policy-fixture.json
.venv/bin/python -m scripts.policy_replay --size full --output artifacts/pass6-policy-full.json
```

Dataset IDs `sample-v1-fixture-97` and `sample-v1-full-97`; seed 97. Four weekly origins **14, 21, 28 September and 5 October 2026** evaluate **14 September–11 October**, entirely in the generator's withheld future period. Each origin retains the 56-day model, 28-day visible window and seven-day release window. Both policies start with the same runtime input snapshot. After each release, each policy carries its own realized stock, transit, confirmed orders, received IDs and outstanding installments into the next origin. Only realized *sales* become observations with next-day 01:00 Riyadh availability; unmet oracle demand is never inserted into forecast history. A stockout remains censored, distinct from a known zero.

The evaluator fixes three extra funding weeks **before** evaluation at the last declared caps (15,000 commitment / 18,000 payment / 800 transfer), solely to cover later origins' 90-day payment ledgers. Existing dates, offers, supplier capacity and all forecasts remain unchanged. No future labels select a method, buffer or action. No tuning on this period was performed. Generated truth hash, input hashes, actions, cash headrooms and weekly results are saved for reproduction.

Complete origin policies first pass the separate production feasibility replay. The realized execution simulator then receives withheld demand: receipt → serve → dispatch → close. It conserves on-hand plus transit and checks receiving space and dated cash. If observed stock cannot support a new transfer while preserving the **origin forecast** donor reserve, the whole transfer is cancelled and reported; it never consults tomorrow's truth to choose the dispatch. No cancellations occurred in these measured samples. The simulator is an evaluation assumption, not an order execution system.

| 28-day realized measure | Fixture, each policy | Full sample, each policy |
|---|---:|---:|
| True demand, units | 17,618 | 104,343 |
| Fulfilled units | 8,464 | 41,626 |
| Unmet units | 9,154 | 62,717 |
| Unit fill | 48.0418% | 39.8934% |
| Average daily closing network inventory incl. transit, units | 1,858.4643 | 9,211.8571 |
| New purchase commitments, SAR | 32,612 | 32,550 |
| Payments within evaluation dates, SAR | 19,146 | 19,275 |
| Movement expense, included in payments, SAR | 1,640 | 1,800 |
| Remaining installments after evaluation, SAR | 18,506 | 18,475 |
| Dated funding, stock conservation, independent origin replay | Passed | Passed |

**Proposed and benchmark releases are identical at every origin.** Both datasets were run twice; complete JSON reports matched byte-for-byte, including actions, input hashes, cash and explanations of execution deviations. There is no measured proposed-policy advantage. Funding feasibility coexists with substantial unmet demand, especially in the full sample. Paid-plus-outstanding reconciles to new commitments + movement fees + initial SAR 3,400 obligations. Inventory is reported in base units, not as a cash saving. The four-week ending boundary does not erase remaining payables or penalize/credit future service.

Five regression tests cover hand-calculated realized service/inventory, censored-history carry-forward, future-truth isolation, deposit/balance/received-ID carry-forward, whole-line transfer cancellation and missing-oracle failure. These complement the existing independent replay, leakage, solver and review tests; no production calculation engine or contract changed.

## Hosted and local runtime evidence

First/repeat below means first/repeat in the audit process. It does **not** establish a fresh Vercel instance or cold import. All planning responses passed independent replay, financial checks, exact action/summary/explanation repeat comparison and the 4,500,000-byte limit. All were honestly labeled `feasible_fallback`; the fixture challenger kept two seconds and the full challenger stayed unattempted.

| Environment | Fixture first / repeat, HTTP s | Full first / repeat, HTTP s | Largest response, bytes |
|---|---:|---:|---:|
| Local macOS, production port 8012 | 2.739 / 2.549 | 3.273 / 3.255 | 3,753,044 |
| Exact baseline CI, Ubuntu Docker | 3.534 / 3.560 | 9.179 / 9.268 | 3,753,043 |
| Hosted canonical Vercel | 8.230 / 5.473 | **17.022 / 14.929 — FAIL 10 s gate** | 3,753,044 |

Hosted engine times: fixture 3,998.0 / 4,096.9 ms; full 11,775.5 / 11,949.9 ms. The full challenger used zero seconds, so its solve cannot explain the overrun. The exact-commit container profile isolates full first/repeat forecast work at **6.188 / 6.273 s**, benchmark at **2.172 / 2.149 s**, independent replay at **0.280 / 0.275 s**, explanation at **0.090 / 0.090 s**, serialization at **0.023 / 0.023 s**; first input creation adds **2.496 s**. The complete cold container route is **11.648 s** despite passing warm HTTP smoke. Local profile likewise shows forecasts dominate, but cannot substitute for hosted per-stage profiling. No runtime gate, solver budget, sample size or objective was changed. Target-host phase/memory measurement and a focused forecast-preparation performance correction remain required; neither cache entire plans nor reopen exact-optimizer research.

Hosted forecast first/repeat: fixture **0.687 / 0.636 s**, full **5.244 / 1.135 s**. Live selected results, held-out coverage and 56-day quantities passed. Hosted combined scenario first/repeat: fixture **6.793 / 6.363 s** on the completed serial run; full **20.283 / 18.141 s**, largest comparison **921,568 bytes**. Full scoped detail **12.395 s / 113,556 bytes**; full future-path delay comparison **27.489 s / 1,035,200 bytes**. All serial scenario gates passed below 30 seconds and 4.5 MB. The separate funding/payment-ceiling trace passed at **6.137 s / 348,988 bytes** with the exact deltas above.

An overlapping hosted calculation received explicit HTTP 429; the initial scenario script failed nonzero. A serial rerun passed. This is evidence of the documented single-instance busy gate, not an invisible retry or relaxed assertion. Vercel runtime-error lookup returned no error clusters in the selected one-hour range; that does not prove zero errors outside that range or establish memory consumption.

Browser inspection verified canonical initial load, relative same-domain session/catalog/forecast/planning/capture/detail requests, real purchase evidence, and 390px mobile Plan Review with all four navigation controls in bounds and no page overflow. Captured screenshots are real browser output, not mockups. Agent-browser sessions later lost their page (`about:blank`); these were not counted as passing checks. The final single-session `scripts/hosted_browser.mjs` run **passed** desktop demand/plan, full forecast product/store/recalculate, actual store-transfer evidence, mobile combined scenario controls, baseline reset, mobile/desktop Data navigation, disabled uploads and blank-template download. All observed API responses were same-domain HTTP 200; page/console errors were empty. Harness setup errors were corrected to use accessible combobox roles and funding-date identities before the successful run. This is actual hosted browser evidence for 599554c, not local UI evidence for the new correction.

## Hosted own-data prerequisite

Actual hosted `GET /api/workflow/session`: **enabled false**, driver disabled. Only `LocalStorage` exists in `backend/app/data/storage.py`; `configuration()` deliberately rejects it on Vercel. The existing `Storage`, `ObjectReference` and `UploadAuthorization` types are provider-neutral preparation, not a completed adapter. No authorized private provider/resource/access was found or provisioned.

Implementation still required: select an authorized private object store; add narrowly scoped upload authorization and verified upload finalization; bind opaque references to server-verified session owner/type/size/content/hash/expiry; store review revisions with atomic replacement semantics across instances; implement private download transport for large accepted files; implement deletion, expiry and abandoned-upload cleanup. Extend the existing storage conformance tests against that real provider, including cross-session rejection, expired/unknown refs, content and archive limits, unsuccessful uploads and concurrent revision races. Only then change the fail-closed configuration and verify full hosted import → plan/scenarios → edit/regenerate → accept → download → reopen/new-draft. The current protocol and bounded implementation checklist are retained; choosing and fabricating an unconfigured provider would not resolve this gate. Browser Dataset JSON, public URLs and serverless temp files are prohibited substitutes.

Local synthetic own-data smoke passed fixture/full parsing, deliberately wrong browser size labels, authoritative provenance, regenerated evidence, final acceptance, financial reconciliation, deterministic snapshot bytes, unique external IDs, portable read-only reopen and session deletion. Fixture upload/plan/regenerate/accept/export: **1.397 / 2.762 / 2.777 / 0.854 / 0.113 s**. Full: **10.797 / 5.790 / 6.169 / 6.810 / 0.863 s**; full XLSX **125,251 bytes**, portable **932,865 compressed / 21,292,412 expanded bytes**. These are local file operations. No local Docker executable exists; Docker workflow evidence belongs only to baseline CI.

## Three-minute demo and portfolio copy

Use the fixture for a short public sample demonstration, disclosing the outstanding runtime gate. Use the local production application for review/export.

1. **0:00–0:35:** Demand Review, SKU001/S1. Show live recalculation, 281.1 expected units, 10.4 → 7.5 MAE and 28% displayed improvement. Open the held-out check: only 27/28 known days; future truth is unavailable to the planner.
2. **0:35–1:15:** Plan Review. Show the validated fallback label and 52.7% projected fill, then the 130-unit SKU008 purchase. Trace SAR 715 deposit and 715 later balance. Show the SKU001 S2→S1 transfer and its single grouped fee. Explain that funding-feasible does not mean every service target is met.
3. **1:15–2:00:** Scenarios. Raise first-week commitment/payment allowances to 2,000/4,500. Original preserves the old assumptions, frozen keeps exact actions, replan uses the same changed allowances. Show +50 visible served units alongside slightly worse tail unmet demand. Do not describe this synthetic comparison as customer savings.
4. **2:00–3:00, locally:** Edit SKU008 from 130 to 120. Show stale state and disabled acceptance/export; regenerate, acknowledge shortfalls and accept. Download XLSX and snapshot, reopen read-only, and identify the explicit new-draft path. No order is sent. On the public host, show the disabled own-data explanation instead of claiming this final step works there.

Portfolio copy: “Built an independent retail planning MVP for one DC and four stores, combining evaluated weekday forecasts, constrained purchasing and allocation, dated cash commitments, disruption scenarios and an auditable local review/export workflow. The full synthetic sample covers 60 SKUs and 240 store series. Every proposed plan is independently replayed for stock and funding feasibility. Four-week withheld-demand evaluation found identical proposed and benchmark releases, with 39.9% simulated full-sample fill under tight funding—evidence of an explicit cash/service trade-off, not a claimed optimization gain. Public sample APIs have been exercised; hosted latency and private own-data storage remain release dependencies.”

Disclosures: synthetic Saudi retail inputs, SAR conventions and Riyadh business dates; simulated/forecast service, no customer deployment, executed orders, proven commercial savings or global optimality. Four-week evaluation, one seed and one synthetic setting do not establish generalization. The full live challenger is skipped; a validated fallback can equal the benchmark and retain shortages. Temporary local sessions are not accounts or durable history; accepted files must be downloaded before expiry/reset/restart. Hosted memory and genuine cold starts remain unverified. Scope stays frozen: no new dashboards, scenario types, AI narration, integrations or history system.
