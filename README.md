# Demand and Supply Planning Intelligence

An independent, synthetic Saudi retail planning portfolio: demand forecasting, multi-location allocation and cash/service trade-offs. **Passes 1 and 2 are implemented.** Forecast evaluation feeds live purchasing, allocation and dated payment plans. Scenarios, uploads and exports remain unavailable.

The working app serves a React/TypeScript interface and a Python calculation API from one process. Demand Review loads the 10-SKU fixture, evaluates three weekday forecasting methods and displays the actual result. A 60-SKU sample is also available. Open **Plan Review** to calculate the complete network, inspect independently checked recommendations and compare the constrained benchmark. Allow roughly 30 seconds per plan on the measured local machine. Time-limited results are explicitly labeled as fallbacks.

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
.venv/bin/python -m scripts.planning_smoke  # fixture/full, first/repeat; about two minutes
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

Docker is not installed in the local implementation environment. GitHub Actions successfully built and started the image on Ubuntu for commit `f939b3e`, then passed the production HTTP smoke test. The same native Vercel configuration is preserved. Pass 2 Linux/container and hosted checks have not run locally; the earlier CI success proves only the recorded Pass 1 commit. See the [deployment readiness assessment](docs/DEPLOYMENT.md) for exact settings and the future upload limitation.

## Project guide

- [Build specification](docs/DEMAND_SUPPLY_MVP_BUILD_PLAN.md): source of truth and six-pass scope.
- [Build status](docs/BUILD_STATUS.md): executed checks, limitations and exact Pass 3 handoff.
- [Forecast methodology and contracts](docs/FORECASTING.md): cutoff rules, fallback policy and metric definitions.
- [Planning methodology](docs/PLANNING.md): staged model, benchmark, independent replay and cash semantics.
- `backend/app/contracts.py`: canonical Pydantic request/data/result schemas; frontend types are generated from OpenAPI.
- `backend/app/data/`: seeded samples and cross-row validation.
- `backend/app/forecasting/engine.py`: the sole forecast/evaluation implementation.
- `frontend/src/`: four-screen shell, live Demand Review and Plan Review.

Calculations process inputs on the server. This is not a browser-only application. There are no user uploads, accounts or persistent user datasets in Passes 1–2, and no claim about a future host's retention policies.
