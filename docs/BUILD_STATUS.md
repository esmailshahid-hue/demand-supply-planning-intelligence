# Build status

Updated: **16 September 2026**. Completed scope: **Pass 1 only**.

**Pass 1 exit gate: met locally.** The seeded sample travels through the live Python API into the built React UI; historical forecast evaluation passes invariant tests; a production-style single-service startup and HTTP deployment smoke test pass. Docker/Linux and public-host deployment are not verified and are explicitly outstanding. No infrastructure was provisioned. This is not the full MVP release gate.

## Repository inspection

Read `docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md` in full before implementation. The repository contained only that plan and the existing two-line README. No applicable `AGENTS.md`, previous `BUILD_STATUS.md`, application code or dependencies were present. The original build specification is unchanged; the README now documents the implemented application.

## Implemented

- React 19 / TypeScript / Vite frontend and FastAPI / Pydantic Python service. One production process serves both built assets and the calculation API. No accounts, database or additional deployment.
- Canonical schema version 1.0.0 and engine version 0.1.0. Typed contracts cover all 15 normalized tables and forecast request/result/error records. Frontend types are generated from OpenAPI; the UI contains no forecasting calculations.
- Fixed seed 97 and fixed as-of 2026-09-14. Ten-SKU fixture: **15,160 history rows**; full 60-SKU sample: **99,160 history rows**, one DC/four stores/12 suppliers. Both have a 420-day history envelope; the new product starts ten days before as-of. The full sample also has zero-demand and intermittent series.
- Synthetic latent demand is generated before availability/sales. Runtime inputs contain no future truth or expected case labels. Offline CLI writes these to separate files. The ten required case families are represented by operational inputs; they do not produce hard-coded recommendations.
- Cross-row validation for references, duplicate keys, date envelopes, usable stock, snapshots, received PO semantics, pack conversions, shared-capacity units, explicit empty transaction declarations, scoped event overlaps and funding coverage. Separate grouped warnings expose missing, censored and not-yet-available history. Full physical/funding feasibility belongs to Pass 2.
- Seasonal naive, four-week same-weekday mean and 40/30/20/10 recency-weighted mean, with explicit missing-weekday/short-history/launch/no-evidence fallback behavior. Censored training estimates use earlier uncensored values and remain separate from observations.
- Disjoint rolling-origin evaluation at 7/28/protection-period horizons, held-out final check, four-complete-window eligibility, 5% improvement and non-worsening absolute quantity-bias selection guard. Zero-denominator percentages remain unavailable. Pooled metrics operate on units, not averages of percentages.
- Dated known-event/quantity-replacement application in the calculation layer, retaining original/revised quantities and reason; no interactive override or scenario workflow. Forecast versioning uses run IDs and input hashes. Protection buffer evidence includes sample count and an honest days-of-demand fallback.
- Functional Demand Review shows selected method/reason, baseline comparison, bias, evaluation coverage, observed/forecast chart, provisional tail, daily details, origin records, final check and dataset warnings. Data and Assumptions explains actual inputs. Plan Review and Scenarios explicitly show unavailable states; upload/template/export buttons are disabled.
- Reusable visual tokens/styles, desktop/mobile layouts, labeled controls, keyboard skip link, loading/error/retry states and live recalculation. No fabricated plan metrics or recommendations.
- Bounded API, one concurrent forecast per process, cooperative engine budget, sanitized schema errors and no raw-row/access logging. Only server-owned synthetic input data is cached; user results are not cached or persisted.
- Production startup script, non-root multi-stage Dockerfile, health endpoint/check, dependency locks/pins, smoke tools and GitHub verification workflow. SciPy/HiGHS is installed and smoke-tested solely for Pass 2 compatibility.

## Executed verification and actual results

Environment: macOS arm64, Python **3.14.4**, Node **25.6.1**, npm **11.9.0**. Runtime package versions are pinned in `requirements.txt`; development pins in `requirements-dev.txt`; frontend resolved versions in `frontend/package-lock.json`.

| Command / check | Actual result |
|---|---|
| `python3 -m venv .venv` and dependency installation | Succeeded. The first sandboxed pip attempt could not access the network; an approved network-enabled retry installed dependencies. `npm install --cache /private/tmp/planning-npm-cache` succeeded with zero reported vulnerabilities. |
| `.venv/bin/python -m pytest -q` | **35 passed**; last complete run **4.50 s**. Two upstream deprecation warnings: Starlette's httpx TestClient adapter and an AnyIO portal alias. No test failures. |
| `.venv/bin/python -m scripts.export_contracts` then `npm --prefix frontend run generate:types` | Succeeded; generated `frontend/src/contracts.generated.ts` from the real API schema. |
| `npm --prefix frontend run build` | TypeScript check and production Vite build passed. Final bundle: **243.49 kB JS / 75.86 kB gzip**, **10.94 kB CSS / 3.27 kB gzip**; Vite build **375 ms**. An initial wrong-working-directory command and an empty CSS import failed, were corrected, and subsequent builds passed. |
| `./scripts/start.sh` | Built app started successfully on **127.0.0.1:8000**, one Uvicorn worker, frontend and API on the same port. Local socket binding required the execution environment's approved sandbox escalation. |
| `.venv/bin/python -m scripts.smoke` | **Passed**: health, built index, fixture/full live forecasts, 56-day horizon, quantities and evaluation records. Latest measurements below. |
| `CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e` | **4 passed in 2.4 s** against the final build. Checks captured API data versus displayed quantities/run ID, new run IDs on recalculation, held-out panel, four-screen navigation, unavailable controls, launch/zero-demand cases, mobile keyboard/no-page-overflow and API failure/retry. One earlier exact-label test locator timed out; changing it to the actual accessible combobox role resolved it. |
| `agent-browser` isolated session | Page loaded; meaningful controls/content; desktop and 390px mobile screenshots inspected; no page or console errors reported. Screenshots were local verification artifacts, not mockups. |
| `.venv/bin/python -m scripts.solver_smoke` | **Passed** independent integer problem: expected `x=2`, objective 2, HiGHS status 0. First optimizer import **31.154 s**; repeat process **0.449 s**. Integer solve **0.000–0.006 s**. This is not a planning benchmark. |
| `python -m scripts.generate_sample --size fixture/full --output artifacts/fixture/full` (using `.venv/bin/python`) | Both completed; runtime, oracle and label files written separately. Runtime JSON round-tripped through Pydantic and validation with no errors. |
| `.venv/bin/python -m pip check` | **No broken requirements found.** |
| `.venv/bin/python -m compileall -q backend scripts` | Passed. |
| `git diff --check` | Passed for tracked edits. New files were separately inspected; no credentials or operational uploads were added. |
| Docker build/run | **Not executed:** Docker is not installed. |
| GitHub Actions / hosted test | **Not executed:** workflow prepared, no remote run or public deployment performed. |

Latest production HTTP measurements after process restart (single selected SKU-store, not a network planning solve):

| Dataset | First request, including generation/validation | Warm request | Engine portion |
|---|---:|---:|---:|
| Fixture | 0.135 s | 0.021 s | 19.6–20.6 ms |
| Full sample | 0.820 s | 0.091 s | 89.5–92.1 ms |

Reference sample result for SKU001 / Al Olaya: recency-weighted weekday mean, **281.0667 expected units over 28 days**, **28.3105%** improvement in complete-window quantity MAE over seasonal naive, **223/224** scored selection observations and **7/8** complete 28-day windows. Display rounds these quantities. These are synthetic forecast results, not operational savings claims.

The model tests explicitly cover hand-computed weekday weights and renormalization, future/late-report leakage, holdout isolation, prior-only censor estimates and exclusion, missing versus valid zeros, zero denominators, launch and unavailable forecasts, short observed-history fallback, known/future event handling, closed/unranged days, exact 5% selection threshold and bias guard, the four-window rule, pooled WAPE, runtime budget failure, validation blocks, reproducibility, truth separation and real API behavior.

## Important decisions and limits

Details and formulas: [FORECASTING.md](FORECASTING.md). Hosting assessment and supporting official sources: [DEPLOYMENT.md](DEPLOYMENT.md).

- `as_of` is midnight at the start of the first future Riyadh business date. Availability must strictly precede an origin. Daily sample reporting at 01:00 the next day deliberately leaves the most recent historical day unknown. The final check is **27/28 scored days** and has no complete-period quantity MAE; the UI discloses that coverage rather than scoring a late report.
- Up to eight earlier disjoint selection windows; complete-window eligibility conservatively requires all calendar dates to be observed/uncensored/forecastable. Closed-day windows can contribute partial daily evidence but not model selection quantities. Routinely closed series may remain provisional.
- Selection uses mean absolute **total-quantity** error and absolute mean **quantity** bias on identical complete origins. Daily absolute error/WAPE and pooled daily bias are separately shown, including partial coverage. Held-out results never choose a winner. The final forecast refits the selected method with then-available observations.
- Estimates, promotions, launch assumptions and missing observations are explicitly distinguished. No confidence intervals or guaranteed service claims. Buffer evidence does not yet feed a purchase/allocation model.
- API contracts normalize money to SAR per base unit and stock to base units. Case/MOQ integers and dated transaction fields are ready for Pass 2, but the Pass 1 validation result is **not a feasible-plan certificate**. Unknown capacity cannot be interpreted as unlimited in Pass 2.
- Forecasts calculate one selected SKU-store at a time. Full-network forecasts/planning are not yet a batch endpoint. The 30-second overall full-plan performance target remains unmeasured.
- The 30-second forecast budget is cooperative, checked between origins, not an OS hard timeout. Single-process concurrency limits do not become distributed limits if replicas are added.
- Hashes use ordered normalized serialization; reordered equivalent input tables can produce a different hash. There is no historical revision/vintage contract or persistent plan state yet.
- Connected Vercel access was checked read-only: Hobby team available. The **17.5 MB** full normalized sample exceeds Vercel Functions' documented **4.5 MB** payload limit. Default remains a single-container skeleton; choose an authorized container-capable host or explicitly resolve that transport mismatch. No paid host selected.
- Docker/Linux, hosted memory/runtime/retention and a genuine cold target-host solver start are outstanding. The first local SciPy import exceeded 30 seconds; no full-plan performance claim is made. None of these prevents local Pass 2 formulation work.

## Exact starting point for Pass 2

Read the build plan, this file and the forecasting/deployment notes. **Reuse this app and its existing contracts. Do not rebuild the frontend or replace the forecast engine.**

1. Begin with `backend/app/contracts.py`, `data/sample.py`, `data/validation.py` and `forecasting/engine.py`. Forecast outputs have 56 dated quantities, visible/tail flags and protection evidence. Resolve the actual SKU-store protection periods and capacity-coverage validation before funded planning. Do not silently use missing forecast quantities or unknown limits.
2. Create `backend/app/simulation/` for an **independent** daily stock/transit/cash replay. First implement the specification's one-SKU/seven-day hand fixture and assert its exact three alternatives: no action **50 unmet / 65 ending stock / 0 commitment / 0 cash**; transfer **0 / 15 / 0 / 20**; buy-and-move **10 / 65 / 400 / 220**, plus **200 payable later**. This hand fixture has not been implemented in Pass 1.
3. Create `backend/app/planning/` for the no-new-action projection, constrained order-up-to benchmark and joint SciPy MILP. Follow receipt/service/dispatch order, shared stock, integer packs, conditional MOQ/MOV, dated capacities/calendars, receiving volume, donor reserve with dated receipts, opposite-lane restrictions, commitment/payment/transfer limits and tail rules. Use one overall stage budget and report incomplete optimality honestly.
4. Independently replay each feasible candidate, including cash installments and existing obligations. Add adversarial tests for second-receiver duplication, donor demand/late receipts, funding timing and solver/lock failures. Never equate solver success with feasibility.
5. Extend result contracts/API and regenerate `frontend/src/contracts.generated.ts`. Replace only the explicitly unavailable Plan Review content in `frontend/src/App.tsx` with a minimal real plan inspection view. Retain live Demand Review and the shared visual styles. Scenario controls, uploads, review/export workflows remain for later passes.
6. Reconcile the hand fixture, run fixture then full sample, measure end-to-end cold/warm runtime and memory, and update this status with Pass 2 evidence. Reuse `scripts/solver_smoke.py`, `scripts/start.sh`, Dockerfile and CI skeleton; verify Linux/hosting before claiming deployment compatibility is complete.
