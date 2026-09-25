# Final static-delivery release handoff — 25 September 2026

**Ready to deploy; hosted verification pending.** This work starts at `d8335ee9f6862350ae14dac0afbc04f49b4e6067`. No push, merge, deployment, domain change or Vercel project-setting change is performed by this correction.

## Established release state

The supplied exact-commit evidence for `d8335ee` is [GitHub run 36020922316](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/36020922316): 233 backend tests passed / two pre-build static skips, five post-build static tests and 30 Playwright tests passed, together with Docker, solver, forecast, planning, scenario, transport and workflow smoke. Both Vercel deployment contexts succeeded.

The canonical project is `demand-supply-planning-intelligence` (`prj_9wUSzLP3zKbvVinWCeNvmyDelVh5`, team `team_zcIJkL6iQbO9rv4Wmu1sxNk1`). Its canonical alias remains [demand-supply-planning-intelligence.vercel.app](https://demand-supply-planning-intelligence.vercel.app). Deployment `dpl_GCwAUNWCB115ngCeAN2gd2iQToJ6` is associated with `d8335ee`: health and full `sample-v3` catalog return 200, but `/` and `/index.html` return FastAPI's `404 {"detail":"Not Found"}`. These are established handoff facts, not claims that the new correction is deployed.

## Root cause and supported correction

A clean archive of `d8335ee` reproduced the build contract failure using Vercel CLI **60.0.1**, Node **24.21.0** and uv **0.12.19**. Vite's Vercel command generated root `public/index.html` and its JS/CSS during the Python build command. `builds.json` registered `@vercel/static` for `public/**/*` separately from `@vercel/python`; the static builder's input snapshot did not contain these later-generated files. The successful build had **no `.vercel/output/static` directory**. Its root rewrite pointed at an absent `/index.html`, and the framework rewrite fallback sent requests to `/fastapi`. FastAPI's existing frontend registration pointed at `frontend/dist`, which this build never created. Local tests instead used an already-built `frontend/dist` and compared files/configuration, so they missed the missing platform output.

The correction uses [Vercel's documented FastAPI frontend promotion](https://vercel.com/docs/frameworks/backend/fastapi#serving-frontend-and-static-assets): Vite now builds `frontend/dist`, and the existing `app.frontend("/", directory=DIST, fallback=None)` supplies that public frontend to the Python builder after the build command. A valid PEP 621 `pyproject.toml` sets `[tool.vercel.fastapi.static] cdn = true`, explicitly permitting public static delivery despite body-limit, timing and cache middleware. API requests retain all middleware. Runtime dependencies are identical to `requirements.txt`, enforced by a test; the earlier invalid tool-only manifest is not recreated.

There is no manual root rewrite, new service, proxy, Build Output API generator or committed frontend bundle. `/` and `/index.html` resolve to CDN HTML; `/assets/*` uses one-year immutable caching. HTML revalidates. API, docs and OpenAPI receive generated precedence routes to the function; unmatched requests retain function 404 behavior. The UI changes screens without changing URL paths, so no SPA fallback is required. Local startup and Docker keep serving the same `frontend/dist` through FastAPI, including safe caching for `/index.html`.

`release.json` contains only the build's commit SHA and immutable Vercel hostname, from `VERCEL_GIT_COMMIT_SHA` and `VERCEL_URL`. Production builds fail if these are missing; no credentials or environment dump is published. Its CDN policy is `no-store`. The hosted verifier requires that SHA to match the workflow checkout and verifies identity again after probes/browser interactions.

## Actual output evidence and local limits

The corrected CLI output contains:

```
.vercel/output/static/index.html
.vercel/output/static/assets/index-ClTcXrlP.js
.vercel/output/static/assets/index-D6upZBaq.css
.vercel/output/static/release.json
.vercel/output/functions/fastapi.func/.vc-config.json
```

Generated GET/HEAD precedence routes include `/api/health`, `/api/sample`, `/docs` and `/openapi.json`; POST routes include planning, forecast and scenarios. No precedence route captures `/`, `/index.html` or assets. The initial routing phase falls through to static filesystem resolution, and the later framework rewrite targets `/fastapi`. `scripts.vercel_output_check.py` reads these actual files, validates all HTML asset references/bytes/cache rules, rejects static shadowing, and requires API precedence and the Python function. It does not manufacture build output.

The local build used dummy project/team IDs and an empty authentication directory. No production settings or secrets were pulled. CLI 60.0.1 needs its `VERCEL_FASTAPI_STATIC_CDN=1` collector capability flag locally. On macOS it installs Linux binary wheels, which fail app discovery (`pydantic_core._pydantic_core` cannot import); the successful **inspection-only** run supplied existing macOS site-packages through `PYTHONPATH` for discovery. This is not a Linux-runtime or deployable-bundle claim. Normal Ubuntu CI uses the local capability flag without that macOS workaround and gates the actual output. Production uses the documented FastAPI mechanism; actual CDN delivery is still a hosted gate.

Automatic approval review rejected production configuration pulls because they could copy secrets. The credential-free fixture made the build investigation possible without that access. Docker is unavailable locally; corrected Linux/Docker evidence remains for normal CI. See [BUILD_STATUS](BUILD_STATUS.md) for exact local results.

## One final hosted action

After the user commits/pushes this correction through the existing release process, requires green exact-SHA normal CI, and the canonical project deploys that commit, run **Verify canonical production latency** against **main** once.

That existing manual workflow is the authoritative final hosted evidence. It:

1. Fails on the first broken homepage, referenced JS/CSS, `/index.html`, health, docs/OpenAPI or compact `sample-v3` catalog route, with URL, status, MIME type and bounded sanitized excerpt.
2. Verifies deployed commit/immutable hostname evidence. Static content must bypass Python, assets must have immutable caching, and HTML must not be immutable. Static timings are recorded without cache-state-dependent timing gates.
3. Runs the unchanged serial fixture/full first/repeat, capture, detail and complete-response probes with the **ten-second full-first HTTP gate**, existing connection behavior, response-size limits, independent replay, financial reconciliation and determinism checks.
4. Runs the existing desktop/mobile browser flow, including full planning, evidence, forecasts, combined scenarios, disabled hosted own-data controls, same-origin APIs and console errors.
5. Always uploads bounded JSON evidence and a job summary, even if a later latency/browser gate fails. Raw plan payloads, cookies and response dumps are not uploaded. The summary includes host, commit/deployment hostname, frontend/assets/API results, browser outcome, latency table and run link.

Ordinary PR CI never probes production. A green Vercel build alone is insufficient. If the exact deployed correction passes this workflow and normal CI, no further planning/feature work or documentation-only run-ID commit is required; the workflow artifact and summary close release evidence. Until then the verdict remains **Ready to deploy; hosted verification pending**, not MVP complete.

## Optional administration and intentional boundaries

The duplicate `demand-supply-planning-intelligence-hahy` (`prj_OQsMvdHhAK7KP6BKMbPL3Wsjvhk5`) does not own the canonical alias. Disconnecting/deleting it is optional user-controlled administrative cleanup, not a release gate. This task does neither.

Hosted own-data storage stays intentionally disabled. Local/Docker upload, review, regeneration, acceptance and export remain available. Private persistent hosted storage is not required for the public synthetic sample portfolio demo.
