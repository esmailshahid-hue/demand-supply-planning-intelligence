# Demand and Supply Planning Intelligence

An independent Saudi retail planning portfolio: demand forecasting, multi-location allocation and cash/service trade-offs. Passes 1–3 provide live sample forecasts, feasible planning and original/frozen/replanned scenarios. **Pass 4 adds local XLSX inputs, exact action review, final acceptance, reviewed exports and portable snapshots. Hosted uploads remain blocked pending authorized private storage.** No orders are sent.

The app serves a React/TypeScript interface and a Python calculation API from one process. Demand Review evaluates three weekday forecasting methods on a 10-SKU fixture or 60-SKU sample. Plan Review exposes dated stock/cash evidence and exact accept/reject/edit decisions. Scenarios compares unchanged actions with a fresh constrained plan. Data and Assumptions validates a documented workbook before calculation. Baseline smoke retains its 10-second warm live target; fallback status is explicit and does not claim global optimality. See [BUILD_STATUS](docs/BUILD_STATUS.md) for measured results and cold-start qualifications.

Workbook processing happens on the server after explicit consent. Local data and review files are private temporary session objects, not durable history. Download accepted files before the one-hour expiry or reset. [WORKBOOK.md](docs/WORKBOOK.md) documents all sheets, units, validation, limits, review rules, file formats and external-ID reconciliation. On Vercel, sample workflows remain available but uploads and accepted-file workflows stay unavailable until a private storage adapter is implemented and verified.

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

Docker is unavailable locally. User-confirmed GitHub Actions `35308623547` passed for Pass 3 commit `259ddab`, including Docker and production planning/scenario checks. That evidence does not verify these Pass 4 changes. Exact-commit CI/container and hosted execution remain outstanding. See [deployment readiness](docs/DEPLOYMENT.md) for the hosted storage blocker.

## Project guide

- [Build specification](docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md): source of truth and six-pass scope.
- [Build status](docs/BUILD_STATUS.md): executed checks and remaining verification boundaries.
- [Workbook workflow](docs/WORKBOOK.md): sheets, validation, review, exports and reconciliation.
- [Forecast methodology and contracts](docs/FORECASTING.md): cutoff rules, fallback policy and metric definitions.
- [Planning methodology](docs/PLANNING.md): staged model, benchmark, independent replay and cash semantics.
- `backend/app/contracts.py`: canonical Pydantic request/data/result schemas; frontend types are generated from OpenAPI.
- `backend/app/data/`: seeded samples and cross-row validation.
- `backend/app/forecasting/engine.py`: the sole forecast/evaluation implementation.
- `frontend/src/`: four-screen shell, live Demand Review and Plan Review.

Calculations process inputs on the server after consent. There are no accounts, database, persistent history or automatic purchasing. Pass 5 is not implemented.
