# Deployment readiness

Assessed on **17 September 2026**. No public deployment, paid service, custom domain or external infrastructure was created.

## Conclusion

`PASS_1_VERCEL_READY_WITH_FUTURE_ARCHITECTURE_GAP`

The current Pass 1 sample application is suitable for a first Vercel deployment. It remains one deployment with one Python calculation implementation: Vercel loads `backend.app.main:app` as a FastAPI Function, builds the React frontend during the same deployment, and serves the UI and relative `/api/*` requests from one domain. The fixture and full sample are generated inside Python from the requested sample identifier; the browser does not upload either normalized dataset. Live recalculation therefore remains a Python request, not a static or precomputed substitute.

The final MVP upload workflow is not yet compatible with a direct browser-to-Function workbook or normalized-data POST at the measured full-sample size. That is a later architecture decision, not a defect in the current Pass 1 sample flow.

## Committed Vercel shape

- Root `app.py` exposes the existing `backend.app.main:app` instance through a FastAPI entrypoint recognized by Vercel. Keeping deployment metadata out of `pyproject.toml` makes Vercel install the existing pinned `requirements.txt` instead of asking uv to lock a second dependency manifest.
- `.python-version` pins Python 3.14, which is supported by Vercel's current Python runtime.
- `vercel.json` selects the native FastAPI preset, runs the locked Vite production build, gives the calculation Function a 60-second ceiling and excludes tests, local dependencies and generated development artifacts from its bundle.
- `.vercelignore` keeps caches, local environments, browser artifacts, generated samples, documentation and `.env*` files out of the deployment upload.
- `requirements.txt` remains the runtime dependency manifest. `frontend/package-lock.json` remains the frontend dependency lock.
- No rewrite or API base URL is required. FastAPI owns `/api/*` and `/`; the frontend uses relative `/api/*` requests. The application has one browser URL, `/`; its four screens are in-page navigation states, so there are no additional client-side route refreshes to configure.
- The existing Dockerfile remains a separate, valid single-container deployment option. Vercel uses its native Python Function build and does not consume that Dockerfile.

Vercel documents root `app.py` detection, build commands and the single-Function execution model in its [FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi). Its [Python runtime guide](https://vercel.com/docs/functions/runtimes/python) lists Python 3.14, `requirements.txt` support and a 500 MB uncompressed Python bundle limit.

## Current Pass 1 traffic and runtime fit

Measured uncompressed JSON sizes from the real API are:

| Dataset | Normalized dataset if sent to `/api/forecast` | `GET /api/sample` response | `POST /api/forecast/sample` response |
|---|---:|---:|---:|
| Fixture | 2,684,842 bytes | 3,363 bytes | 41,649 bytes |
| Full sample | 17,475,067 bytes | 15,235 bytes | 41,647 bytes |

The Pass 1 UI calls `/api/forecast/sample` with only `size`, `sku` and `location_id`. Both API responses are far below Vercel's 4.5 MB request/response limit. A production-style local restart measured the full sample at **0.824 s first request / 0.089 s warm**, with **91.8 ms / 87.8 ms** reported inside the forecast engine. The 60-second Function setting leaves headroom over the engine's existing cooperative 30-second budget without changing it.

The installed local SciPy and NumPy trees are approximately 99 MB and 34 MB. The complete Linux Vercel Function bundle has not been produced, so the actual hosted bundle size and cold import remain first-deployment checks. SciPy is installed for compatibility but is not imported by the Pass 1 forecast request path. The existing Ubuntu GitHub Actions evidence for commit `f939b3e410e7b255f69a919a6ca5270f106ae3df` successfully completed backend tests, solver smoke, frontend build, browser tests, Docker build, Docker startup and HTTP smoke. This proves the separate Linux/container path, not Vercel packaging.

Vercel's documented limits for the assessed Hobby shape are 2 GB / 1 vCPU, up to 300 seconds and a 500 MB uncompressed Python bundle. The same limits page fixes Function request and response bodies at **4.5 MB**. See [Vercel Functions limits](https://vercel.com/docs/functions/limitations).

## Exact dashboard settings for the first deployment

Import the repository as one Vercel project and use these values:

| Dashboard field | Value |
|---|---|
| Framework Preset | **FastAPI**. This is also enforced by `vercel.json`. |
| Root Directory | **`.` (repository root)**. Leave at the default root; do not select `frontend`. |
| Build Command | **Leave at default / no dashboard override.** `vercel.json` supplies `npm --prefix frontend ci && npm --prefix frontend run build`. |
| Output Directory | **Leave at default / no override.** Do not set `frontend/dist`; the FastAPI deployment owns the application and its built frontend files. |
| Install Command | **Leave at default / no override.** Vercel installs `requirements.txt`; the committed build command performs the locked frontend `npm ci`. |
| Development Command | **Leave at default / no override.** Local repository development continues to use `scripts/start.sh` or Vite plus FastAPI as documented in the README. |
| Environment Variables | **None required for Pass 1.** Do not add secrets or API base URLs. |

Additional settings:

- Use Node.js **24.x** for the frontend build to match the Dockerfile and GitHub Actions. If 24.x is already the project default, leave it unchanged.
- Leave Fluid Compute enabled at its project default.
- Leave Function memory, region, Git integration, deployment protection and domains at their defaults for the first preview. `vercel.json` already sets `maxDuration` to 60 seconds.
- Do not add rewrites, a second Vercel project, a separate frontend deployment or a static forecast artifact.

## Future workbook and planning architecture gap

The application middleware accepts up to 32 MiB, but Vercel rejects a Function request or response above 4.5 MB before that application limit can make a larger upload viable. The 17.5 MB normalized full sample proves that the final workbook flow cannot assume a direct POST through the Function. The platform limit and Vercel's recommended source-upload pattern are documented in [the 4.5 MB payload guidance](https://vercel.com/kb/guide/how-to-bypass-vercel-body-size-limit-serverless-functions).

Before Pass 4 uploads, choose and verify one of these designs:

1. Upload the workbook directly from the browser to authorized object storage using a short-lived client upload token or pre-signed URL, then send a small object reference to the Python Function. Add per-session isolation, file-size/type validation, explicit deletion/retention behavior and server-processing disclosure.
2. Use a container-capable host that accepts the required upload size and can manage temporary files within a verified retention policy.

Pass 2 must also measure the real full planning solve with SciPy on the selected host. If cold import, memory or total staged runtime is unsuitable for one synchronous Function invocation, the later workflow will need durable object storage plus a job/status mechanism or a container worker. In-process `lru_cache` data and the semaphore are per Function instance and cannot provide cross-replica durability or a global concurrency limit.

No storage, queue, database, background worker or upload transport is added in this readiness pass.

## Verification and first-deployment checks

The first deployment of commit `1d251fc` failed before dependency installation. Vercel found the tool-only `pyproject.toml`, selected uv and ran `uv lock`; uv rejected the file because it had no PEP 621 `[project]` table. The correction removes that incomplete project manifest, adds the recognized root `app.py` wrapper and points the existing Function settings at `app.py`. Runtime dependencies remain pinned once in `requirements.txt`.

Vercel CLI **59.20.0** was downloaded and invoked. `vercel build` stopped with `project_settings_required` because the repository has not been linked to a Vercel project. It was not rerun with `--yes`, because that would pull or create external project state and the requested scope explicitly stops before deployment. The committed build command, local production service and HTTP/browser paths all passed; details are recorded in `BUILD_STATUS.md`.

The first real preview deployment still needs these host-specific checks:

1. Confirm the remote build installs the pinned Python wheels and keeps the Function bundle below 500 MB.
2. Open `/`, `/api/health`, the fixture and full sample; change product and store; run live recalculation; verify the returned run ID and displayed values.
3. Measure Vercel cold and warm latency and memory, including a new instance rather than only a warm cache.
4. Confirm `/assets/*` delivery, API routing, logs without raw rows, deployment protection and actual platform retention behavior.
5. Reconfirm that requests and responses stay below 4.5 MB. Do not test the future 17.5 MB normalized upload as if it were supported.

Until those checks run, this repository is deployment-ready but no public or Vercel-hosted application has been verified.


## Pass 2 runtime assessment and CI evidence

Pass 2 preserves `app.py`, the native FastAPI preset, relative same-domain API paths, the existing frontend build and the **60-second** Vercel Function setting. No services were provisioned or deployed. GitHub Actions run `35201527675` succeeded on Ubuntu for original Pass 2 commit `6c587cc`: 56 backend tests, solver smoke, frontend build, browser tests, Docker build/start, forecast smoke, fixture/full planning smoke and solver smoke inside the container all completed. This is CI evidence for that exact commit. The current narrow correction still requires its own CI run after commit/push.

The new `/api/plan/sample` path calculates all 60 products/four stores over 56 days, including 240 evaluated forecasts, a benchmark, the joint model and independent replay. SciPy/HiGHS is now imported during planning requests, whereas Demand Review still follows the existing forecast-only calculation path. The total planning target remains 30 seconds across all stages with replay time reserved; timed-out stages stop and return only independently validated incumbents/fallbacks. No optimality or serverless performance guarantee is implied.

Final local production HTTP measurements on macOS arm64:

| Planning sample | First / repeat seconds | Largest response |
|---|---:|---:|
| Fixture | 28.178 / 28.169 | 782,412 bytes |
| Full (60 SKUs, 240 series) | 28.321 / 28.343 | 3,747,785 bytes |

These requests followed forecast smoke in the same fresh service, so sample caches were already populated. Both planning runs used live Python calculations and returned feasible fallbacks with disclosed shortages; all purchase/payment totals reconciled. These values are below the configured 60-second ceiling and documented 4.5 MB response limit, but leave less payload margin than Pass 1. Raw normalized inputs are not returned. Any later result expansion must remeasure the payload rather than assume the current margin remains.

A separate fresh Python process measured full-sample generation, planning and serialization at **28.720 s**, with macOS peak RSS **672,497,664 bytes (641.3 MiB)**. This includes the lazy solver import but is not a Vercel invocation or a Linux bundle measurement.

The target-host first/repeat planning runtime, peak memory, packaging and HTTP behavior still require actual Vercel verification. A successful Vercel build does not establish hosted planning execution. Local and Ubuntu container tests cannot establish those target-host properties. Keep the existing per-instance concurrency limitation and future 17.5 MB workbook transport gap in the hosting decision. No storage, job queue, scenario API or upload workaround was added in Pass 2.

Reproduce the local check after a production startup:

```sh
PORT=8011 ./scripts/start.sh
# In another terminal:
.venv/bin/python -m scripts.smoke --url http://127.0.0.1:8011
.venv/bin/python -m scripts.planning_smoke --url http://127.0.0.1:8011
```
