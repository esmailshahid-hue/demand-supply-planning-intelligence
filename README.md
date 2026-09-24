# Demand and Supply Planning Intelligence

An independent Saudi retail planning portfolio that turns synthetic demand, inventory, supplier and funding inputs into explainable forecasts and constrained purchase/transfer proposals. It compares original, frozen and replanned scenarios, supports an exact human review lifecycle locally, and never executes an order.

[Public sample](https://demand-supply-planning-intelligence.vercel.app) · [Current build status](docs/BUILD_STATUS.md) · [Deployment status](docs/DEPLOYMENT.md)

**Current release status: BLOCKED.** The public link is available, but its canonical Vercel alias still serves commit `27eb86c`; the attempted Prompt 3 deployment for `2ec1c06` failed before build. A local deployment-manifest correction is ready but has not been published. See the status documents for the exact evidence and remaining authorized release step.

## What the demo shows

- **Plan Review opens first.** The useful constrained plan loads without waiting for the Demand screen; full daily stock/cash evidence is fetched only when requested.
- **Demand Review** evaluates three simple weekday-aware methods with time-ordered historical scoring, dated fallback explanations and a 28-day visible forecast.
- **Scenarios** separates the B − A scenario shock, C − B replanning effect and C − A net change. Invalid frozen plans stay visibly invalid while a valid net comparison remains available.
- **Data and Assumptions** documents the synthetic samples. Local mode validates XLSX inputs and supports review, regeneration, acceptance and portable exports; those storage-backed controls are intentionally disabled on the public host.

The bundled data is `sample-v2`, seed 97, planning date 14 September 2026. The 10-SKU fixture is intentionally a funding stress case. The 60-SKU sample has explicit higher funding limits but still retains material shortages and residual binding constraints. Outcomes are modeled estimates, not observed savings.

## Three-minute workflow

1. Open **Plan Review**. Note `feasible_fallback`, dated action/shortage explanations, independent replay, commitments, payments and remaining headroom. “Feasible” does not mean all demand is covered or that the plan is globally optimal.
2. Open one action’s **Evidence**. The scoped daily stock/cash ledger loads on demand; the compact plan does not eagerly download all 16,800 full-sample stock rows.
3. Visit **Demand Review** and inspect a product/store forecast, historical error and fallback wording. The tail beyond day 28 is provisional.
4. In **Scenarios**, try promotion, supplier disruption, funding or delay, then combine controls. Compare original, frozen and replanned results; read dated failure evidence when frozen actions become infeasible.
5. Open **Data and Assumptions**. On the public host, confirm upload/review storage is unavailable. For the local own-data demo, upload a generated workbook, edit an action, regenerate, accept, download the workbook and portable snapshot, then reopen/reset it.

The public application is a portfolio sample, not a customer-data service. Use local or Docker mode for the complete own-data lifecycle.

## Run locally

Prerequisites: Python 3.14 and Node 24+.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
npm --prefix frontend ci
npm --prefix frontend run build
./scripts/start.sh
```

Open <http://127.0.0.1:8000>. API documentation is at <http://127.0.0.1:8000/docs>. For frontend development, run `npm --prefix frontend run dev`; Vite proxies `/api` to port 8000.

## Verify

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.solver_smoke
.venv/bin/python -m scripts.export_contracts
npm --prefix frontend run generate:types
npm --prefix frontend run build
CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e
```

With the production-style server running:

```sh
.venv/bin/python -m scripts.smoke
.venv/bin/python -m scripts.planning_smoke
.venv/bin/python -m scripts.planning_transport_smoke
.venv/bin/python -m scripts.scenario_smoke
.venv/bin/python -m scripts.workflow_smoke
.venv/bin/python -m scripts.release_trace --output artifacts/calculation-trace.json
```

Offline withheld-demand evaluation keeps truth outside API/model inputs:

```sh
.venv/bin/python -m scripts.policy_replay --size fixture --output artifacts/policy-fixture.json
.venv/bin/python -m scripts.policy_replay --size full --output artifacts/policy-full.json
```

Docker, where available:

```sh
docker build -t planning-intelligence .
docker run --rm -p 8000:8000 planning-intelligence
```

## Reproducible inputs and methodology

```sh
.venv/bin/python -m scripts.generate_sample --size fixture --seed 97 --output artifacts/fixture
.venv/bin/python -m scripts.generate_sample --size full --seed 97 --output artifacts/full
.venv/bin/python -m scripts.workbook --size full --output artifacts/full.xlsx
```

Only `runtime-inputs.json` belongs in calculation requests; `offline-truth.json` and `offline-labels.json` are evaluation-only. Unknown input fields and stale sample versions/hashes are rejected.

- [Build specification](docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md)
- [Forecast methodology](docs/FORECASTING.md)
- [Planning, solver stages and cash semantics](docs/PLANNING.md)
- [Scenario definitions and comparison arithmetic](docs/SCENARIOS.md)
- [Workbook, review and reconciliation contract](docs/WORKBOOK.md)
- [Private-storage boundary](docs/PRIVATE_STORAGE.md)
- [Historical verification records](docs/history/README.md)

## Limits

The fixture has 10 SKUs/40 store series; the full sample has 60 SKUs/240 series. Both use a 28-day visible window, 56-day model and seven-day release window. The unchanged gates are under 10 seconds for warm planning HTTP, 30 seconds for planning/scenarios and 4.5 MB for a complete sample response.

There are no accounts, database, durable hosted history, automatic purchasing or proven commercial savings. Local temporary objects expire after one hour or on reset/process restart; download accepted files promptly. Hosted uploads and accepted exports remain unavailable until an authorized private persistent-storage adapter is implemented and lifecycle-tested. Optional audit ideas and additional product features are deferred.
