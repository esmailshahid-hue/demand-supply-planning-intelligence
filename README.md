# Demand and Supply Planning Intelligence

An independent Saudi retail planning portfolio: demand forecasting, multi-location allocation and cash/service trade-offs. Passes 1–4 provide live forecasts, feasible planning, original/frozen/replanned scenarios, local XLSX inputs, exact action review, final acceptance and portable exports. Pass 5 adds responsive navigation, keyboard evidence and recoverable review/error states. **Passes 5 and 6 are closed for release `ff2e42d907f6b0a83811849c7efab10ff1007dcc`; the public sample, calculation and hosted-latency gates are verified, and portfolio-MVP feature development is complete.** Hosted own-data remains intentionally unavailable pending an authorized private persistent-storage adapter. No orders are sent.

[Public sample application](https://demand-supply-planning-intelligence.vercel.app) · [Pass 6 audit, measured policy trade-offs and demo script](docs/RELEASE_AUDIT.md). The canonical production deployment is READY in `iad1` at exact commit `ff2e42d`, with successful normal verification run `35967399001`. Two consecutive unchanged canonical latency runs, `35967540536` and `35968872124`, passed the retained cold full-sample gate, replay, response-size, reconciliation, determinism, scenario capture and scoped-detail checks. Local/Docker own-data review and export are verified; hosted upload and accepted-export persistence remain disabled.

The default plan response loads daily stock evidence on demand from authoritative replay; accepted files retain the complete calculation. The provider-independent private storage boundary is tested, but no hosted provider is configured. See [private storage integration](docs/PRIVATE_STORAGE.md).

The app serves a React/TypeScript interface and a Python calculation API from one process. Demand Review evaluates three weekday forecasting methods on a 10-SKU fixture or 60-SKU sample. Plan Review exposes dated stock/cash evidence and exact accept/reject/edit decisions. Scenarios compares unchanged actions with a fresh constrained plan. Data and Assumptions validates a documented workbook before calculation. Baseline smoke retains its 10-second warm live target; fallback status is explicit and does not claim global optimality. See [BUILD_STATUS](docs/BUILD_STATUS.md) for measured results and cold-start qualifications.

Workbook processing happens on the server after explicit consent. Local data and review files are private temporary session objects, not durable history. Download accepted files before the one-hour expiry or reset. [WORKBOOK.md](docs/WORKBOOK.md) documents all sheets, units, validation, limits, review rules, file formats and external-ID reconciliation. On Vercel, sample workflows remain available but uploads and accepted-file workflows stay unavailable until a private storage adapter is implemented and verified.

Plans and scenario snapshots carry canonical source provenance: bundled fixture, bundled full sample, uploaded workbook or reopened portable snapshot, plus the normalized dataset hash and dimensions. A private dataset reference is authoritative over browser size labels, and source/hash mismatches fail instead of falling back to a bundled sample. The production component profiler uses the same `/api/plan/sample` route function with an empty request context and creates no review session objects:

```sh
.venv/bin/python -m scripts.planning_profile
```

## Run locally

Prerequisites: Python **3.14**, Node **24+** (tested locally with Node 25), npm.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm --prefix frontend ci
npm --prefix frontend run build
./scripts/start.sh
```

Open **http://127.0.0.1:8000**. API documentation: **http://127.0.0.1:8000/docs**. Startup checks for the compiled frontend; it uses one worker and disables HTTP access logs. Set `PORT` and `HOST` as needed.

For frontend development, run the API above and `npm --prefix frontend run dev` in another terminal. Vite proxies `/api` to port 8000.

## Verify

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.solver_smoke
.venv/bin/python -m scripts.export_contracts
npm --prefix frontend run generate:types
npm --prefix frontend run build
.venv/bin/python -m scripts.smoke  # requires the running production server
.venv/bin/python -m scripts.planning_smoke  # fixture/full, first/repeat
.venv/bin/python -m scripts.scenario_smoke
.venv/bin/python -m scripts.workflow_smoke  # local upload/review/accept/export, fixture + full
.venv/bin/python -m scripts.workbook --size full --output artifacts/full.xlsx
```

Browser tests (the suite can start the production server itself):

```sh
cd frontend
npx playwright install chromium
npm run test:e2e
```

Alternatively, set `CHROME_PATH` to an installed Chrome executable. On this Mac, the verified command was:

```sh
CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e
```

## Generate reproducible inputs

```sh
.venv/bin/python -m scripts.generate_sample --size fixture --seed 97 --output artifacts/fixture
.venv/bin/python -m scripts.generate_sample --size full --seed 97 --output artifacts/full
```

Each command writes separate `runtime-inputs.json`, `offline-truth.json` and `offline-labels.json`. **Only runtime inputs belong in calculation requests.** The API rejects unknown top-level fields and does not expose oracle files. Generated artifacts are git-ignored.

## Container skeleton

```sh
docker build -t planning-intelligence .
docker run --rm -p 8000:8000 planning-intelligence
.venv/bin/python -m scripts.smoke
```

Docker is unavailable in the current local workspace. Exact-commit GitHub Actions run `35967399001` succeeded for release `ff2e42d907f6b0a83811849c7efab10ff1007dcc`, including the established Linux/container verification matrix. See [deployment status](docs/DEPLOYMENT.md) for the completed public-sample evidence and the separate hosted-storage limitation.

## Project guide

- [Build specification](docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md): source of truth and six-pass scope.
- [Build status](docs/BUILD_STATUS.md): executed checks and remaining verification boundaries.
- [Release audit](docs/RELEASE_AUDIT.md): traced calculations, offline realized policy evaluation, verified hosted revision and final public-sample closure.
- [Workbook workflow](docs/WORKBOOK.md): sheets, validation, review, exports and reconciliation.
- [Forecast methodology and contracts](docs/FORECASTING.md): cutoff rules, fallback policy and metric definitions.
- [Planning methodology](docs/PLANNING.md): staged model, benchmark, independent replay and cash semantics.
- `backend/app/contracts.py`: canonical Pydantic request/data/result schemas; frontend types are generated from OpenAPI.
- `backend/app/data/`: seeded samples and cross-row validation.
- `backend/app/forecasting/engine.py`: the sole forecast/evaluation implementation.
- `frontend/src/`: four-screen shell, live Demand Review and Plan Review.

Calculations process inputs on the server after consent. There are no accounts, database, persistent history or automatic purchasing. The six-pass portfolio MVP is complete. Private hosted storage remains separate future work requiring authorization, implementation and lifecycle verification; no new scenario types, dashboards, AI narration or integrations are part of this release.

Offline release evidence (truth stays outside API inputs):

```sh
.venv/bin/python -m scripts.policy_replay --size fixture --output artifacts/policy-fixture.json
.venv/bin/python -m scripts.policy_replay --size full --output artifacts/policy-full.json
.venv/bin/python -m scripts.release_trace --output artifacts/calculation-trace.json
# Explicit existing-host browser verification; never deploys:
node scripts/hosted_browser.mjs https://demand-supply-planning-intelligence.vercel.app
```

The weekly evaluation executes only seven-day releases and reports withheld realized demand, dated payments, future obligations and average stock. In the tested four-week period, proposed and benchmark releases were identical. See the audit for the ex ante calendar extension, execution guard and precise simulation limitations.


## Own-data review and recovery

Start the local process or Docker container above with one worker. In **Data and Assumptions**, download the blank template or populated fixture. Follow the workbook’s Instructions and [sheet contract](docs/WORKBOOK.md): all named sheets/columns are required, quantities are base units, money is SAR, and blank demand is different from zero. Confirm server processing, upload the XLSX, correct the reported sheet/field errors, then select **Use validated data and calculate plan**. Incomplete funding does not produce an accepted funded plan.

In **Plan Review**, inspect action dates, payments, stock and shortages. Choose an action and accept its exact terms, reject it or enter a valid case quantity. The displayed plan becomes stale: regenerate before final acceptance. Resolve exact-lock conflicts rather than bypassing them. If regeneration succeeds but its result cannot load, select **Load regenerated result**; acceptance stays blocked until the current result is displayed. Acknowledge remaining service/buffer shortfalls when required, then **Finally accept plan**. Acceptance creates immutable planning files; it sends no orders.

Download both the reviewed XLSX and portable snapshot. Reopen the `.plan.json.gz` through Data and Assumptions; it opens read-only. **Create new draft** explicitly, then regenerate before accepting/exporting a changed version. Reconciliation of confirmed/executed actions uses stable external IDs as described in [WORKBOOK.md](docs/WORKBOOK.md). Save files before the one-hour object expiry, reset or process restart. After expiry, reimport your workbook or reopen your downloaded snapshot; unsaved decisions cannot be recovered. Network, runtime and provenance errors do not enable downloads.

## Calculation and operating limits

The synthetic fixture has 10 SKUs and 40 store series; the full sample has 60 SKUs and 240 store series across one DC/four stores. Both use a 28-day visible window, 56-day model and seven-day release window. Days 29–56 are provisional; expected demand and scenario comparisons are estimates, not guaranteed service or savings.

No sample outcome is precomputed, and complete plan responses are not cached. Generated immutable sample inputs and their validation can be reused per process; forecast preparation is memoized within a calculation. Each live plan calculates actions and independently replays stock/cash. First/warm smoke runs may share sample inputs; they are not proof of Vercel cold-start performance. The fixture keeps its two-second best-effort joint challenger; the full sample explicitly skips that challenger. A **Validated constrained plan** passed independent feasibility checks but is not globally optimal and can retain shortages.

The unchanged gates are 10 seconds for warm fixture/full planning HTTP requests, a 30-second calculation/scenario ceiling and a 4,500,000-byte sample-response guard. See [PLANNING.md](docs/PLANNING.md) and [SCENARIOS.md](docs/SCENARIOS.md) for the exact budget and fallback policies. Local workbook limits are 16 MiB compressed, 160 MiB expanded, 170,000 operational rows, 60 products, five locations, 12 suppliers and 420 history days. Portable snapshots have separate 16 MiB compressed/64 MiB expanded bounds. Full local file and session limits are in [WORKBOOK.md](docs/WORKBOOK.md). Hosted uploads, stored review files and accepted downloads are disabled until private storage is authorized and verified; public sample calculation remains available.

## Three-minute operator demo

Use the **local or Docker** app for this sequence. Dataset: `sample-v1-fixture-97`, seed 97, planning date **2026-09-14**, 10 SKUs/one DC/four stores. Values below were observed through the live API during Pass 5; they are demo checkpoints, not constants in the UI or business guarantees.

1. **0:00–0:25 — Demand Review.** Select the small fixture, SKU001 / Al Olaya (S1), and Recalculate live. The recency-weighted weekday mean gives **281.1 expected units** over 28 days. Historical displayed MAE is **10.4 → 7.5**, a displayed **28%** improvement; pooled signed bias is **<0.1%**, with **223/224** scored observations. Explain the provisional tail and that this is synthetic demand.
2. **0:25–1:05 — Plan Review.** Inspect `P-OFFER008-0`: **130 SKU008 units**, SUP08 → DC, order/dispatch **14 September**, receipt **28 September**, purchase commitment **SAR 1,430**. Open its evidence: **SAR 715** deposit on 14 September and **SAR 715** balance on 28 October. Total plan commitments are **SAR 91,606**, payments **SAR 97,746**. Projected visible fill is **52.7%**, leaving **7,567.4 units** uncovered; day-56 inventory value is **SAR 18,303.42**. Show the SKU008/DC→S1 shared-stock exception on 14 September: requested 150 units, only 10 pack-rounded units available. Feasible does not mean all demand is covered.
3. **1:05–1:50 — Scenarios.** Use this baseline, choose **Promotion**: SKU001, **+30%**, **14–27 September**, all ranged stores. Run live. Original keeps its original assumptions; frozen retains actions under the uplift; replanned calculates new actions under that same uplift. In this observed case frozen actions fail independent feasibility, so its service metrics and comparison deltas correctly remain unavailable. The validated replan shows **52.2% fill**, **7,742.8 unmet units**, **SAR 91,726 commitments** and **SAR 97,746 payments**. Open failure/action evidence; do not describe this as a quantified saving against an infeasible frozen plan. Reset returns to the original baseline.
4. **1:50–3:00 — Review and export locally.** Return to Plan Review, select `P-OFFER008-0`, change quantity from 130 to **120**, and Apply quantity edit. Show the stale banner and blocked acceptance/export. Regenerate, inspect the validated revised actions and any remaining shortfalls, acknowledge those shortfalls, then Finally accept. Download the reviewed workbook and portable snapshot. In Data and Assumptions, confirm processing and reopen the snapshot: it is read-only. Create new draft and regenerate before another acceptance. No order or transfer was executed.

For an own-data demonstration, replace the bundled start with the populated fixture XLSX upload described above. Hosted storage is still a release dependency: demonstrate sample calculation there only, and do not imply hosted review/export has been verified.
