# Build status

Updated: **17 September 2026**. Current scope: **Passes 1 and 2**. Earlier Pass 1 evidence is preserved below as historical evidence.

**Pass 1 exit gate: met locally and in Ubuntu CI.** The seeded sample travels through the live Python API into the built React UI; historical forecast evaluation passes invariant tests; production-style single-service startup and HTTP smoke tests pass. GitHub Actions verified the Linux container path for commit `f939b3e`; no public host or Vercel deployment has been verified. No infrastructure was provisioned. This is not the full MVP release gate.

## Pass 2 — purchasing, allocation and cash

Implemented the complete 56-day network planning path through Python and the existing React application. Pass 1 forecasting files and presentation calculations are unchanged. No push, merge, deployment, external provisioning, scenario controls, uploads, exports or persistence was performed.

### Implementation and contracts

- `planning/inputs.py` connects all ranged SKU/store series to the real Pass 1 evaluator, with calendar-adjusted protection evidence and separate full-input/series hashes. Missing stock/capacity, unreachable calendars, excessive protection envelopes, unfunded inputs and existing payment breaches are explicit failures.
- `planning/optimizer.py` builds the joint case/pack MILP with staged visible then tail must-stock/A/B/C class-store shortfalls, weekly buffers, cost and stable action ties. Stages share one runtime budget; lower objectives do not run after a timeout. `planning/benchmark.py` supplies a deterministic constrained order-up-to comparison.
- `simulation/replay.py` independently reconstructs stock, transit, acquisition value, dated supplier/lane capacity, peak receiving volume, donor protection, grouped minimums/fees and SAR-cent cash. It does not import the optimizer or trust its status. Existing unpaid obligations and already-dispatched stock are counted once. Recommendations failing replay cannot be shown as executable.
- New `/api/plan/sample` and `/api/plan` endpoints share the existing process admission limit. Generated contracts expose forecast traces, solver stages, proposed/benchmark/no-action policies, cash, class-store and SKU-store service, structured failures and constraint explanations. Only the proposed policy returns a daily inventory ledger; normalized historical inputs remain server-side.
- Plan Review replaces its placeholder using the current visual styles. It shows purchases, shared allocations, commitment/payment totals, coverage/shortages, comparisons, cash limits, action dates, linked stock/payment/forecast evidence and exceptions. Loading removes stale results; dataset changes/recalculation replace the entire response. Demand Review retains all Pass 1 corrections; Scenarios and workbook actions remain unavailable.
- New production HTTP planning smoke checks are included in the existing CI/container verification path. Docker and Vercel architecture/configuration are preserved; only the new smoke script is copied into Docker.

Detailed formulas, rounding, forecast provenance, benchmark conservatism and fallback policy are in [PLANNING.md](PLANNING.md). No buffer or target is a guaranteed service level. Day-56 excess explicitly repeats the final forecast week and uses net store needs at the DC. Purchasing payments exclude tax, receivables and revenue cash.

### Acceptance evidence

The exact seven-day fixture reconciles independently:

| Policy | Unmet | Ending units | New commitment | Visible payments | Later payment |
|---|---:|---:|---:|---:|---:|
| No new action | 50 | 65 | SAR 0 | SAR 0 | SAR 0 |
| Transfer 50 B→A | 0 | 15 | SAR 0 | SAR 20 | SAR 0 |
| Buy 40 then move | 10 | 65 | SAR 400 | SAR 220 | SAR 200 on day 33 (offset 32) |

| Command / check | Actual result |
|---|---|
| `.venv/bin/python -m pytest -q` | **56 passed in 7.07 s**, including all 35 existing Pass 1 regressions and 21 planning/validator cases. Two unchanged upstream Starlette/AnyIO deprecation warnings. |
| `.venv/bin/python -m scripts.solver_smoke` | SciPy **1.18.1**, import **0.351 s**; HiGHS cold **0.006 s**, warm **<0.001 s**, status 0 and expected integer result 2. |
| `.venv/bin/python -m pip check` | **No broken requirements found.** Pip cache was disabled under sandbox permissions; dependency validation completed. |
| `.venv/bin/python -m compileall -q backend scripts` | Passed. |
| Contract export and `npm --prefix frontend run generate:types` | Passed; TypeScript result schemas generated from current OpenAPI. |
| `npm --prefix frontend run build` | Passed TypeScript and Vite production build: **259.25 kB JS / 79.38 kB gzip**, **11.15 kB CSS / 3.34 kB gzip**. |
| `PORT=8011 CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e` | **8 passed in 2.1 min**. Live fixture calculation, recalculation and full 240-series planning; every displayed purchase value, allocation quantity and weekly cash row matched the API. Also verified stale-result removal, failure/invalid-input states, navigation and existing forecast regressions. |
| `agent-browser` against the built application | Demand/Plan navigation and real Plan Review render passed; no browser errors, blank page, error overlay or desktop horizontal overflow. Screenshot inspected locally. |
| `PORT=8011 ./scripts/start.sh` then `.venv/bin/python -m scripts.smoke --url http://127.0.0.1:8011` | Passed built UI, health and live fixture/full forecast. Fixture **0.138 / 0.021 s**, full **0.809 / 0.090 s** first/repeat. |

Tests cover adequate/zero demand, shared scarce stock, deterministic priority ties, late receipts/day-29 effects, packs versus budgets, grouped supplier minimums, shared supplier/lane limits, receiving space, donor protection with late receipts, blocked/reserved/in-transit and confirmed stock counted once, existing/received-order obligations, separate commitment/payment ceilings, same-week installments, cent rounding, obligations beyond day 90, zero-price supply, corrupt actions/dates/values, opposing lanes, disjoint calendars, solver timeout, input rejection and the unchanged forecast boundary. Early new-test failures were missing required fixture fields and one missing optional buffer lookup; these were corrected and the suite rerun successfully. An initially slow benchmark receiving-space lookup was replaced with indexed dated lookups before final performance checks.

### Final planning performance and exit gate

Final `.venv/bin/python -m scripts.planning_smoke --url http://127.0.0.1:8011` passed against the restarted production service. Measurements include HTTP response delivery and use the full dimensions, with no reduced network or static plan. Host: local macOS arm64, Python 3.14.4, Node v25.6.1. The forecast smoke populated sample caches first; “first” below is the first plan for that dataset in the fresh service, not an isolated Vercel cold invocation.

| Dataset / run | HTTP seconds | Engine milliseconds | Response bytes | Purchases / movements | Result |
|---|---:|---:|---:|---:|---|
| Fixture first | 28.178 | 28,165.8 | 782,412 | 24 / 311 | Feasible fallback |
| Fixture repeat | 28.169 | 28,162.8 | 782,411 | 24 / 311 | Feasible fallback |
| Full first | 28.321 | 28,302.1 | 3,747,783 | 31 / 607 | Feasible fallback |
| Full repeat | 28.343 | 28,323.6 | 3,747,785 | 31 / 607 | Feasible fallback |

All four returned no independent hard-constraint failures. Purchase-line values exactly reconciled to commitments; payments exactly reconciled to payment totals; all weekly funding headrooms were nonnegative. Full sample retains **60 SKUs, one DC, four stores, 12 suppliers, 240 forecasts and 16,800 proposed SKU/location/day stock rows**. The largest observed response is below **4,500,000 bytes** and requests are small selectors. Local response time meets the 30-second target and is below configured Vercel `maxDuration: 60`; this does not verify a Vercel cold start or platform memory usage.

A separate fresh Python process generated the full sample, ran `plan(data)` and serialized the result in **28.720 s** (**28,342.9 ms** inside the engine). `resource.getrusage(RUSAGE_SELF).ru_maxrss` reported **672,497,664 bytes (641.3 MiB)** peak RSS on macOS. It returned the independently checked benchmark fallback after `visible_must_stock` reached its time limit. Visible projected unit fill was **41.10%**, with **59,973.76** visible unmet units and **92,198.78** provisional-tail unmet units. New commitments were **SAR 92,550** and total scheduled payments **SAR 99,050**. These are projected results, not measured achieved service.

Final checks also confirmed generated contracts are reproducible, the root Vercel entrypoint still re-exports the same FastAPI app, `maxDuration` remains 60, and `git diff --check` passed. No backend forecast source or forecast display formula changed.

**Pass 2 exit gate: met locally; ready for review and a subsequent user-controlled commit.** The hand fixture reconciles, the full sample is independently feasible while explicitly reporting shortages, and complete runtime is measured. No scope or runtime target was weakened. New hosted/Ubuntu/container checks remain outstanding and are not claimed as completed gates. The complete six-pass MVP release gate remains unmet.

### Limitations and handoff

The measured sample results are independently feasible fallbacks with substantial visible and provisional-tail shortages. The joint solver did not finish its highest-priority stage within the allotted budget on this machine; neither sample is advertised as lexicographically optimal or better than the constrained benchmark. A small hand model finishes all stages optimally. Benchmark receiving-space reservations and single-line supplier-minimum handling are conservative. Runtime may change with hardware; the shared budget is cooperative, not an OS-enforced deadline.

Docker is not installed locally (`command -v docker` returned no executable). Therefore **Pass 2 Docker build/startup, new Ubuntu CI and Vercel-hosted measurements were not run**. Earlier successful Ubuntu CI for `f939b3e` is Pass 1 evidence only. Hosted cold latency, memory, wheel packaging and response limits still need verification. The future workbook payload/storage gap remains unchanged; no upload transport was introduced.

**Exact starting point for Pass 3:** reuse `planning/engine.py`, `planning/contracts.py`, `simulation/replay.py`, `PlanReview.tsx` and the API-backed planning tests. Implement the specified demand uplift, supplier delay/capacity loss, commitment and payment shocks with frozen-action versus replanned comparisons. Keep both policies under identical scenario assumptions, preserve provenance/independent validation, and then complete the sample-data review experience. Do not replace the forecast/model or start workbook review/export work early. Scenario controls and immutable baseline/reset behavior are not implemented in Pass 2.

## Historical Pass 1 records

## Vercel deployment readiness

Completed on **17 September 2026** without creating a project or deployment.

The first Vercel build of commit `1d251fc` failed before dependency installation because the tool-only `pyproject.toml` caused Vercel to run `uv lock`, while uv requires a PEP 621 `[project]` table. The deployment correction removes that incomplete manifest, adds a recognized root `app.py` that re-exports the existing FastAPI instance, and changes the Function matcher to `app.py`. Vercel can therefore return to the repository's pinned `requirements.txt`; application behavior and dependencies are unchanged.

Deployment-correction checks:

| Command / check | Actual result |
|---|---|
| Root entrypoint/config assertion | Passed: `app.app` is the same FastAPI object as `backend.app.main.app`; `pyproject.toml` is absent; `vercel.json` targets only `app.py` with the existing 60-second duration. |
| `.venv/bin/python -m pytest -q` | **35 passed in 4.43 s**; the same two upstream deprecation warnings remain. |
| `npm --prefix frontend run build` | Production build passed: **244.04 kB JS / 76.07 kB gzip**, **11.15 kB CSS / 3.34 kB gzip**, Vite build **441 ms**. |
| `PORT=8010 ./scripts/start.sh` then `.venv/bin/python -m scripts.smoke --url http://127.0.0.1:8010` | Passed built frontend, health, fixture and full-sample live calculations. Full sample: **0.852 s cold / 0.092 s warm**. |
| `.venv/bin/python -m pip check` | **No broken requirements found.** |

No corrected Vercel deployment has been claimed or verified yet; the next Vercel build must confirm that the platform selects `requirements.txt`, completes packaging and starts the Function.

**Conclusion: `PASS_1_VERCEL_READY_WITH_FUTURE_ARCHITECTURE_GAP`.** The current synthetic fixture/full-sample experience is deployable as one native FastAPI Vercel project. The React build and Python API share one domain, all UI requests remain relative, and recalculation stays live in `backend.app.main:app`. The browser sends only a small sample/SKU/store selector to `/api/forecast/sample`; Python generates and evaluates the requested sample at runtime.

The later workbook workflow has a confirmed transport gap. The full normalized synthetic dataset is **17,475,067 bytes**, above Vercel Functions' documented **4.5 MB** request/response limit. Pass 1 catalog and forecast responses are only **15,235 bytes** and **41,647 bytes** for the full sample, so the current UI does not hit that limit. Future uploads need direct object-storage transport with lifecycle/session controls or a container-capable host; this pass adds neither.

Deployment support added:

- `app.py`: root Vercel entrypoint that re-exports `backend.app.main:app` without duplicating dependencies.
- `vercel.json`: native FastAPI preset, exact locked frontend build, 60-second Function ceiling and deployment-bundle exclusions.
- `.vercelignore`: excludes local environments, caches, browser output, tests, generated sample artifacts, documentation and `.env*` files.
- `.python-version` already pins Python 3.14; `requirements.txt` and `frontend/package-lock.json` remain the dependency sources.
- No routing rewrite, API base URL, forecast snapshot, reduced sample, storage service or second deployment was introduced. The existing Dockerfile remains unchanged as a separate container path.

Checks executed for deployment readiness:

| Command / check | Actual result |
|---|---|
| `.venv/bin/python -m pytest -q` | **35 passed in 4.07 s**; two unchanged upstream Starlette/AnyIO deprecation warnings. |
| `npm --prefix frontend ci` | Succeeded: **56 packages**, **0 vulnerabilities**. The first sandboxed attempt stalled on registry access and was stopped; the approved network-enabled retry passed. |
| `npm --prefix frontend run build` | TypeScript and Vite production build passed: **244.04 kB JS / 76.07 kB gzip**, **11.15 kB CSS / 3.34 kB gzip**, Vite build **383 ms**. This is the build command committed for Vercel. |
| `CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e` | **6 passed in 3.8 s**. The suite verifies real API display/recalculation, product/store changes, fixture/full loading, navigation, fallbacks, responsive keyboard behavior and API failure recovery. |
| `PORT=8010 ./scripts/start.sh` then `.venv/bin/python -m scripts.smoke --url http://127.0.0.1:8010` | Production-style single service passed built UI, health, fixture and full live Python calculations. Fixture **0.138 s cold / 0.022 s warm**; full **0.824 s cold / 0.089 s warm**. Port 8010 was used because an unrelated process held 8000. |
| Isolated `agent-browser` production check | `/` loaded meaningful content, no page errors or error overlay appeared, expected controls/results rendered, and navigation opened Data and Assumptions. |
| Real API payload measurement | Fixture normalized input **2,684,842 B**, catalog **3,363 B**, forecast **41,649 B**. Full normalized input **17,475,067 B**, catalog **15,235 B**, forecast **41,647 B**. |
| `.venv/bin/python -m pip check` | **No broken requirements found.** |
| Vercel configuration and entrypoint assertions | JSON syntax and expected framework, build and `app.py` Function fields passed; importing root `app.py` exposes the same FastAPI object as `backend.app.main`. |
| `npx --yes vercel@latest --version` | Installed and reported **Vercel CLI 59.20.0**. Local Node 25 produced one CLI dependency engine warning because that dependency supports Node 20/22/24; the deployment setting uses Node 24. |
| `CI=1 npx --yes vercel@latest build` | Not executed to a build artifact: CLI stopped with **`project_settings_required`** because no local Vercel project link exists. It was not auto-linked, so no project or deployment was created. |
| `git diff --check` | Passed after configuration and documentation changes. |

The exact dashboard fields, Vercel limit sources, bundle/routing decisions and first-preview checks are in [DEPLOYMENT.md](DEPLOYMENT.md). The first real deployment must still prove remote Python wheel installation, the final Function bundle under 500 MB, hosted cold/warm behavior, same-origin routing, logs/retention behavior and fixture/full recalculation. No public host has been verified.

## GitHub Actions browser synchronization correction

Completed on **17 September 2026** for failed workflow run `35191513824`. This changes only Playwright synchronization in `frontend/e2e/forecast.spec.ts`; application behavior, forecast calculations, display values and Pass 2 scope are unchanged.

The Node.js 20 deprecation annotation was a warning and did not cause the failure. `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION` was not added. The actual failure occurred in “new-product fallback, full sample and zero-demand cases are visible”: after selecting the full dataset, the test immediately searched for an enabled button named “Recalculate live.” During full-sample loading the button is intentionally disabled and named “Calculating…”, so the locator exhausted GitHub Actions' five-second expectation timeout.

The test now:

1. Registers targeted 15-second waits for the successful `GET /api/sample?size=full` and full-dataset `POST /api/forecast/sample` before changing the dataset.
2. Selects the full dataset and awaits both responses.
3. Waits for the Product selector to become enabled and for its `SKU011` option to exist.
4. Registers and awaits the successful full-dataset/SKU011 forecast response before asserting that “Recalculate live” is enabled.

No arbitrary sleeps or global timeout increases were introduced.

Verification executed after the correction:

| Command / check | Actual result |
|---|---|
| `npm --prefix frontend run test:e2e -- --grep 'new-product fallback, full sample and zero-demand cases are visible'` | Affected test passed: **1 passed in 1.9 s**. |
| `npm --prefix frontend run test:e2e` — consecutive run 1 | **6 passed in 2.7 s**. |
| `npm --prefix frontend run test:e2e` — consecutive run 2 | **6 passed in 2.5 s**. |
| `npm --prefix frontend run test:e2e` — consecutive run 3 | **6 passed in 2.5 s**. |
| `.venv/bin/python -m pytest -q` | **35 passed in 3.95 s**; two unchanged upstream Starlette/AnyIO deprecation warnings. |
| `npm --prefix frontend run build` | TypeScript and production Vite build passed: **244.04 kB JS / 76.07 kB gzip**, **11.15 kB CSS / 3.34 kB gzip**, Vite build **384 ms**. |
| Isolated `agent-browser` sanity check | Live local page loaded with meaningful controls and results; no framework error overlay or browser errors were detected. |
| `git diff --check` | Passed after the test and status changes. |

## Final Pass 1 presentation correction

Completed on **17 September 2026**, before deployment-readiness work. This correction changes presentation formatting and browser regressions only. The forecast engine, model-selection logic, API `improvement_pct`, data contracts and all Pass 2 scope remain unchanged.

- The improvement headline now rounds the baseline and selected 28-day quantity MAEs to their displayed one-decimal values first, then calculates the whole-number percentage from those values. SKU001/S1 remains **10.4 → 7.5 = 28%**. SKU006/S1 now displays **19.0 → 13.4 = 29%**, while its API `improvement_pct` remains the unrounded **29.57393483709272** used by the engine.
- The seasonal-naive baseline is found explicitly by `method === "seasonal_naive"`; UI rendering no longer assumes candidate-array position zero.
- Browser regressions independently parse the displayed MAEs and recompute the headline. They cover SKU001/S1, SKU006/S1, a product change, a store change and explicit live recalculation. An unavailable product/store evaluation is accepted only when the headline and both MAEs all display `Unavailable`.
- Previous navigation styling, Pooled signed bias formatting, scenario icon, circle removal and API-backed controls remain covered.

Checks executed for this final correction:

| Command / check | Actual result |
|---|---|
| `.venv/bin/python -m pytest -q` | **35 passed in 4.03 s**; two unchanged upstream Starlette/AnyIO deprecation warnings. |
| `npm --prefix frontend run build` | TypeScript and production Vite build passed: **244.04 kB JS / 76.07 kB gzip**, **11.15 kB CSS / 3.34 kB gzip**, Vite build **395 ms**. |
| `CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e` | First run: SKU006 passed, but a product-change assertion rejected a valid all-`Unavailable` result; the assertion was corrected. Final run: **6 passed in 2.9 s**. |
| `.venv/bin/python -m scripts.smoke` | Passed health, built frontend, fixture and full-sample live API calculations. Fixture HTTP 0.022 s cold / 0.022 s warm; full sample 0.093 s cold / 0.089 s warm. |
| Isolated `agent-browser` verification | Page and controls rendered with no error overlay or browser errors. SKU006/S1 visibly showed **29%** and **Baseline 19.0 → selected 13.4 units**. |
| `git diff --check` | Passed after the final code and documentation changes. |

GitHub Actions for commit `f939b3e410e7b255f69a919a6ca5270f106ae3df` succeeded on Ubuntu. That run completed backend tests, solver smoke, frontend build, browser tests, Docker image build, Docker startup and production HTTP smoke testing. This is Linux/container CI evidence for that commit, not public-host or Vercel deployment verification.

## Narrow Pass 1 correction

Completed on **16 September 2026**, before Pass 2. No forecast calculation, data contract, planning, purchasing or allocation behavior changed.

- Data and Assumptions now retains the same light-green selected state as the other navigation items, including while the pointer remains over the button. The CSS uses `aria-current="page"` as an additional explicit selected-state hook.
- Forecast improvement is displayed as a whole percentage. The reference result now shows **28%** beside the same API-derived MAEs shown as **10.4 → 7.5 units**; recomputing from those displayed MAEs also rounds to 28%.
- The KPI is named **Pooled signed bias**, matching the evaluation table. Nonzero signed percentages with magnitude below 0.1% display as `<0.1%` when positive and `>−0.1%` when negative, in both the KPI and table.
- Scenarios uses a branching/comparison SVG instead of a Command-key symbol. Undefined hollow sidebar circles were removed.
- Browser coverage now explicitly changes the product to SKU002 and store to S2, captures each successful `/api/forecast/sample` response, checks the rendered run ID/product/store, then selects Recalculate live and verifies a new API run ID for SKU002/S2.

Correction checks actually run:

| Command / check | Actual result |
|---|---|
| `.venv/bin/python -m pytest -q` | **35 passed in 4.12 s**; the same two upstream Starlette/AnyIO deprecation warnings remained. |
| `npm --prefix frontend run build` | TypeScript and Vite production build passed after the final application correction: **243.65 kB JS / 75.95 kB gzip**, **11.15 kB CSS / 3.34 kB gzip**, Vite build **379 ms**. |
| `.venv/bin/python -m scripts.smoke` | Passed health, built frontend, fixture and full-sample live API calculations. Fixture HTTP 0.024 s cold / 0.022 s warm; full sample 0.103 s cold / 0.092 s warm. |
| `CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e` | **5 passed in 2.8 s** after the final reconciliation assertion. Covers navigation, selected styling, no circles, scenario icon, API-backed product/store changes, explicit recalculation, KPI formatting, fallback cases, mobile access and API error recovery. |
| Isolated `agent-browser` verification | Meaningful content loaded with no error overlay or browser errors. Confirmed 28% improvement, two `<0.1%` renderings (KPI/table), branching SVG present, Command symbol absent, Data and Assumptions background `rgb(217, 231, 189)`, and no hollow circles. |
| `git diff --check` | Passed after the final code and status changes. |

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
| Docker build/run | Docker remains unavailable locally. GitHub Actions for commit `f939b3e` successfully built and started the image on Ubuntu, then ran the production HTTP smoke test against it. |
| GitHub Actions / hosted test | **Succeeded on Ubuntu for commit `f939b3e`**: backend tests, solver smoke, frontend build, browser tests, Docker build/startup and HTTP smoke passed. This was CI validation, not a public deployment. |

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
- The current Pass 1 server-generated sample flow is configured for one native FastAPI Vercel deployment. Its actual catalog/forecast responses fit the platform limit. The **17.5 MB** full normalized sample still exceeds Vercel Functions' documented **4.5 MB** payload limit, so the later workbook upload requires direct object storage or a container-capable host. No storage or paid host was selected.
- Ubuntu CI verified the Docker/Linux build, startup and smoke path for commit `f939b3e`; Docker remains unavailable locally. Hosted memory/runtime/retention and a genuine cold target-host solver start are outstanding. The first local SciPy import exceeded 30 seconds; no full-plan performance claim is made. None of these prevents later work.

## Historical Pass 1 handoff to Pass 2 (now implemented above)

Read the build plan, this file and the forecasting/deployment notes. **Reuse this app and its existing contracts. Do not rebuild the frontend or replace the forecast engine.**

1. Begin with `backend/app/contracts.py`, `data/sample.py`, `data/validation.py` and `forecasting/engine.py`. Forecast outputs have 56 dated quantities, visible/tail flags and protection evidence. Resolve the actual SKU-store protection periods and capacity-coverage validation before funded planning. Do not silently use missing forecast quantities or unknown limits.
2. Create `backend/app/simulation/` for an **independent** daily stock/transit/cash replay. First implement the specification's one-SKU/seven-day hand fixture and assert its exact three alternatives: no action **50 unmet / 65 ending stock / 0 commitment / 0 cash**; transfer **0 / 15 / 0 / 20**; buy-and-move **10 / 65 / 400 / 220**, plus **200 payable later**. This hand fixture has not been implemented in Pass 1.
3. Create `backend/app/planning/` for the no-new-action projection, constrained order-up-to benchmark and joint SciPy MILP. Follow receipt/service/dispatch order, shared stock, integer packs, conditional MOQ/MOV, dated capacities/calendars, receiving volume, donor reserve with dated receipts, opposite-lane restrictions, commitment/payment/transfer limits and tail rules. Use one overall stage budget and report incomplete optimality honestly.
4. Independently replay each feasible candidate, including cash installments and existing obligations. Add adversarial tests for second-receiver duplication, donor demand/late receipts, funding timing and solver/lock failures. Never equate solver success with feasibility.
5. Extend result contracts/API and regenerate `frontend/src/contracts.generated.ts`. Replace only the explicitly unavailable Plan Review content in `frontend/src/App.tsx` with a minimal real plan inspection view. Retain live Demand Review and the shared visual styles. Scenario controls, uploads, review/export workflows remain for later passes.
6. Reconcile the hand fixture, run fixture then full sample, measure end-to-end cold/warm runtime and memory, and update this status with Pass 2 evidence. Reuse `scripts/solver_smoke.py`, `scripts/start.sh`, Dockerfile and CI skeleton; verify Linux/hosting before claiming deployment compatibility is complete.
