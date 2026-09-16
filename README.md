# Demand and Supply Planning Intelligence

An independent, synthetic Saudi retail planning portfolio: demand forecasting, multi-location allocation and cash/service trade-offs. **Pass 1 is implemented.** Purchasing, allocation, scenarios, uploads and exports remain unavailable.

The working app serves a React/TypeScript interface and a Python calculation API from one process. Demand Review loads the 10-SKU fixture, evaluates three weekday forecasting methods and displays the actual result. A 60-SKU sample is also available.

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

Docker is not installed in the implementation environment, so the container build and Linux runtime are **not yet verified**. The equivalent local production startup and HTTP smoke test passed. No infrastructure was provisioned. See [hosting assessment](docs/DEPLOYMENT.md) before selecting a host.

## Project guide

- [Build specification](docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md): source of truth and six-pass scope.
- [Build status](docs/BUILD_STATUS.md): executed checks, limitations and exact Pass 2 handoff.
- [Forecast methodology and contracts](docs/FORECASTING.md): cutoff rules, fallback policy and metric definitions.
- `backend/app/contracts.py`: canonical Pydantic request/data/result schemas; frontend types are generated from OpenAPI.
- `backend/app/data/`: seeded samples and cross-row validation.
- `backend/app/forecasting/engine.py`: the sole forecast/evaluation implementation.
- `frontend/src/`: four-screen shell and live Demand Review.

Calculations process inputs on the server. This is not a browser-only application. There are no user uploads, accounts or persistent user datasets in Pass 1, and no claim about a future host's retention policies.
