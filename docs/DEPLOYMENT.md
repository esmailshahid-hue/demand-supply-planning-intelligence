# Deployment handoff — 24 September 2026

The existing canonical deployment is READY. This bounded correction is not yet published, and its exact-commit CI / hosted verification are pending. No push, merge, deployment, Git disconnection or project-setting change was made.

## Read-only identity inspection

| Item | Observed value |
|---|---|
| Canonical alias | [demand-supply-planning-intelligence.vercel.app](https://demand-supply-planning-intelligence.vercel.app) |
| Owning project | `demand-supply-planning-intelligence` / `prj_9wUSzLP3zKbvVinWCeNvmyDelVh5` |
| Team | `team_zcIJkL6iQbO9rv4Wmu1sxNk1` |
| Deployment | `dpl_7AwN5kDSG3GCsfVW1HWgwniB8Y4A` |
| Immutable host | `demand-supply-planning-intelligence-y734osye3.vercel.app` |
| Source SHA / state | `905458262e68275e3b5339061a0932e5d3df6ed8` / READY production, `iad1` |

[CI run 36002190655](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/36002190655) for that SHA passed backend (233 + 10 subtests, one pre-build static skip) and post-build static tests (4). Browser results were 25 passed / 1 failed: Scenarios stayed disabled after Plan Review unmounted during review-status loading. Docker never started. The later transport/scenario/workflow connection-refused errors were dependency noise, not three independent application defects.

The `2ec1c06` deployment `dpl_99NuyddNXx6PnGL5r6fQcZkKsJCM` failed historically because its tool-only `pyproject.toml` lacked a PEP 621 `[project]` table for `uv lock`. Do not repair or redeploy that old SHA. The current base already removed it; this correction does not recreate a Python manifest or change the requirements source of truth.

## Static implementation and proof boundary

The [official Vercel FastAPI static-files documentation](https://vercel.com/docs/frameworks/backend/fastapi#serving-static-files) says project-root `public/` files are served by the platform, and warns that top-level middleware disables automatic promotion of application-mounted static files. The existing application has global body-limit/timing/cache middleware; cache headers alone did not bypass Python.

`build:vercel` compiles the same React shell and hashed assets into root `public/`. Vercel's build command uses it. An exact `/` → `/index.html` rewrite selects the static shell; there is no SPA catch-all. `/assets/*` uses immutable caching; `/` and `/index.html` must revalidate. `/api/*`, `/docs` and `/openapi.json` remain Python routes with the unchanged 60-second duration. Missing API/assets/pages remain 404. Local/Docker builds still use `frontend/dist` through FastAPI.

Local checks verify both builds are byte-identical and `public/` contains only the shell and compiled JS/CSS, with no private/runtime inputs. Route tests verify API priority, 404s and cache policy. **These tests do not prove CDN execution.** No corrected deployment exists yet.

Read-only canonical baseline on 24 September: root first/repeat **3.545 / 1.001 s**, JS **1.539 / 0.786 s**. Both root responses and both asset responses expose `application_import` 687.995 ms, `module_bootstrap` 688.435 ms and `fastapi_setup` 24.218 ms. Root was cache MISS both times; JS changed MISS → HIT, retaining the Python timing header. This confirms why immutable caching alone was insufficient. These are sequential measured loads, not controlled process-cold measurements or evidence about the unpublished correction.

## Exact manual release actions

1. Review the diff, commit this correction, and publish it through the existing repository release process. Record the new full SHA; do not call `9054582` the corrected SHA.
2. Require the exact-SHA Python 3.14 / Node 24 GitHub workflow to pass, including Docker build/start/health, container solver and every smoke. Local Docker is unavailable. The health step's actual outcome now gates dependent smokes; an earlier planning assertion may fail without suppressing other checks against a healthy server.
3. Confirm the canonical project's production deployment is READY and both immutable deployment metadata and canonical alias resolve to that new SHA. Do not deploy the unused duplicate.
4. Run the checks below on the unchanged canonical deployment. Retain raw timing/header/browser artifacts and correlate function logs. Root and assets must have no Python timing; the API must retain application timing. Verify immutable assets, HTML conditional revalidation, 404 priority, same-origin API, disabled hosted storage and desktop/mobile operation.
5. Compare fresh root/asset loads against the recorded `9054582` baseline, correlating cache status and function logs; demonstrate material improvement without equating a fresh TCP connection with a forced cold process. Run the established production-latency workflow twice consecutively on the same deployment. Only then close hosted verification.

```sh
.venv/bin/python -m scripts.static_delivery_smoke --url https://demand-supply-planning-intelligence.vercel.app
CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' node scripts/hosted_browser.mjs https://demand-supply-planning-intelligence.vercel.app
.venv/bin/python -m scripts.production_latency --output artifacts/production-latency-final-1
.venv/bin/python -m scripts.production_latency --output artifacts/production-latency-final-2
```

The static probe is intentionally not a passing local-FastAPI test. It rejects Python timing on root/assets. The browser script now starts at Plan Review and tests scoped movement evidence without depending on a particular full-sample transfer row. Hosted workbook upload, stored reviews and accepted exports remain unavailable; the local own-data workflow is verified separately.

## Manual duplicate-project account cleanup

Both projects still exist. The unused duplicate is `demand-supply-planning-intelligence-hahy`, project ID `prj_OQsMvdHhAK7KP6BKMbPL3Wsjvhk5`. It does **not** own the canonical alias listed above.

In the Vercel dashboard, select the team above, then open **the `-hahy` project** and confirm its project ID in Settings → General. Check Settings → Domains for any user-owned domain before removing anything. In Settings → Git, disconnect its repository to stop duplicate automatic builds. If the project is truly unused, optionally delete **that duplicate only** via Settings → General → Delete Project after checking its deployment history/domains. Deletion removes its deployments and is a separate user decision. Leave the canonical project's Git connection, domains and settings unchanged. This is account cleanup, not a source-code change, and has not been performed.

Official references: [Git disconnection](https://vercel.com/docs/git/vercel-for-github), [project removal](https://vercel.com/docs/projects/managing-projects).

Historical chronology is retained in [history](history/README.md); current local evidence is in [BUILD_STATUS.md](BUILD_STATUS.md).
