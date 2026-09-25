# Final bounded MVP delivery correction — 25 September 2026

**Ready to deploy; hosted verification pending.** Started from clean `d8335ee9f6862350ae14dac0afbc04f49b4e6067`. This correction is uncommitted and has not been pushed, merged or deployed. No Vercel project settings or domains were changed. All planning, forecasting, scenario, sample-v3, solver and review behavior remains unchanged.

## Published base and remaining defect

The supplied release evidence confirms [CI run 36020922316](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/36020922316) passed for `d8335ee`: backend **233 passed / two pre-build static skips**, post-build static **5 passed**, Playwright **30 passed**, and Docker/forecast/solver/planning/scenario/transport/workflow smokes passed. Both Vercel status contexts succeeded. Those corrections are already published.

Canonical deployment `dpl_GCwAUNWCB115ngCeAN2gd2iQToJ6` is associated with `d8335ee`. Health and full `sample-v3` catalog return 200, but `/` and `/index.html` return FastAPI JSON 404. Build success therefore did not prove usable frontend delivery.

A clean local CLI build reproduced the failure: the separately registered `@vercel/static public/**/*` builder received no generated files; Vite created them later during the Python build command. There was no `.vercel/output/static`, and the root rewrite fell through to FastAPI. The existing FastAPI frontend pointed to unbuilt `frontend/dist`; previous tests inspected file/config text and a separate local build, not actual platform output.

## Bounded changes

- Build `frontend/dist` in every environment and retain the existing `app.frontend(..., fallback=None)`. A valid Python project manifest sets documented `cdn = true` for the public frontend despite middleware; dependency pins exactly match `requirements.txt`. Remove the manual root rewrite. API middleware and contracts stay intact. Local `/index.html` gets the same revalidation policy as `/`.
- Record public build identity in noncached `release.json` (commit SHA and immutable hostname only). Update Docker's frontend stage to include that build helper and exclude local Vercel artifacts from Docker/upload contexts.
- Check every HTML-referenced JS/CSS asset, MIME type, nonempty content, routing and cache policy. Normal CI now runs a pinned credential-free Vercel build and inspects actual output, including API/docs precedence and the Python function. The regression rejects the previously successful build with missing static output.
- Strengthen the existing manual canonical workflow with fail-fast public-route gates, exact commit evidence, unchanged serial latency/replay/finance/size checks, desktop/mobile browser verification, bounded failure evidence, always-uploaded JSON and a GitHub summary. Production is never called by ordinary PR CI. A stale exact-label selector in the existing hosted browser script was fixed using the already-tested accessible combobox locator.

Changed files:

| Scope | Files |
|---|---|
| Delivery | `pyproject.toml`, `vercel.json`, `frontend/package.json`, `backend/app/main.py`, `scripts/release_metadata.mjs`, `Dockerfile`, `.dockerignore`, `.gitignore`, `.vercelignore` |
| Verification | `.github/workflows/verify.yml`, `.github/workflows/production-latency.yml`, `backend/tests/test_static_delivery.py`, `backend/tests/test_public_routes.py`, `scripts/static_contract.py`, `scripts/static_delivery_smoke.py`, `scripts/vercel_output_check.py`, `scripts/production_latency.py`, `scripts/hosted_browser.mjs` |
| Documentation | `README.md`, `docs/BUILD_STATUS.md`, `docs/DEPLOYMENT.md` |

See [DEPLOYMENT](DEPLOYMENT.md) for the complete routing trace, official documentation and output evidence. No new feature, infrastructure, storage adapter or model calibration is introduced.

## Local verification

Python **3.14.4**, Node **25.6.1** for ordinary local checks; isolated Vercel build uses Node **24.21.0**, Vercel CLI **60.0.1**, uv **0.12.19**. Measurements below are local HTTP observations, not forced-cold or hosted timings.

| Check | Result |
|---|---|
| Complete backend suite | Final full run **243 passed + 26 subtests**, **343.65 s**, after adding late-failure artifact coverage. Two existing upstream deprecation warnings; no relaxed assertions or new skips. |
| Static/public/probe regressions | Post-build static suite **5 passed**; final combined delivery/probe regressions **22 passed + 26 subtests**, **0.87 s**. Explicit late-latency failure coverage verifies JSON and summary survive with frontend evidence intact. |
| Frontend production build | `npm --prefix frontend run build` passes. `build:vercel` passes inside actual CLI builds and produces the same frontend in `frontend/dist`. Shell **834 B**, JS **309,510 B**, CSS **13,520 B**. |
| Contracts | OpenAPI export and TypeScript generation pass; `git diff --exit-code -- frontend/src/contracts.generated.ts` passes. |
| Complete Playwright suite | **30 passed**, 3.5 min, including mobile navigation, review ownership/race/recovery, scenario and local workbook lifecycle. |
| Production startup/static/API | `scripts/start.sh` on port 8001; `/`, `/index.html`, referenced JS/CSS, health, docs, OpenAPI and compact sample pass. Unknown API, asset and page paths remain 404. Agent-browser confirms rendered Plan Review with no browser errors; screenshot retained. |
| Solver | SciPy **1.18.1** import **0.390 s**; cold/warm HiGHS integer smoke **0.002 / 0.001 s**, both status 0 and x=2. |
| Forecast smoke | Fixture first/repeat **0.029 / 0.029 s**; full **0.804 / 0.166 s**, all live evaluated responses. |
| Complete planning smoke | Fixture **2.318 / 2.291 s**; full **1.618 / 0.989 s**. Every result independently feasible, deterministic and financially reconciled; unchanged ten-second/4.5 MB gates pass. Full complete responses **4,050,396 / 4,050,395 B**. |
| Compact/detail smoke | Fixture/full compact vs complete actions, totals, explanations, provenance and scoped stock/cash match. Full scoped detail **0.794 / 0.730 s**, **98,481 B**, repeat deterministic. |
| Scenario smoke | Fixture/full combined shock first/repeat, future-path delay, tighter funding, unchanged baseline, three-way delta arithmetic and scoped evidence pass. Frozen infeasibility remains explicit; replans independently feasible. |
| Local own-data workflow | Fixture/full upload → plan → lock/review → regenerate → accept → workbook/snapshot export → read-only reopen → reset passes. Full upload **8.794 s**, plan **2.455 s**, review **2.819 s**, acceptance **3.612 s**, export **0.588 s**. |
| Hosted browser script rehearsal | Passes against **local** port 8002 with `VERCEL=1` (hosted storage disabled). Desktop/full plan, movement evidence, mobile combined scenario, disabled hosted upload, template download, same-origin 200 APIs and zero material console errors. A second local run with synthetic matching build/probe identity also passes. No hosted result is claimed. |
| Dependency checks | `pip check` and npm dependency tree pass; production and full `npm audit` each report **0 vulnerabilities**. No runtime dependency versions changed. |
| Hygiene | Python compilation, both JS script syntax checks, workflow YAML parsing and `git diff --check` pass. |
| Actual Vercel output | Broken clean base has no static output. Corrected output contains shell, hashed JS/CSS, release metadata, API/docs precedence and Python function; output inspection passes. Explicit `outputDirectory=public` alone also failed on a clean build. See local limitations below. |
| Docker / GitHub | Docker executable unavailable locally. Corrected Ubuntu CI, Linux Vercel collection, Docker build/start/homepage/API/container solver and smoke gates await publication. The base's green CI is not substituted for corrected-commit evidence. |
| Canonical hosting | Corrected commit is **not deployed or hosted-verified**. Actual CDN headers/routes, commit identity, desktop/mobile flow and canonical full-first latency await the manual workflow. |

Local CLI inspection used dummy IDs and empty authentication; production secrets/settings were not downloaded. CLI 60.0.1 requires its local `VERCEL_FASTAPI_STATIC_CDN=1` capability flag. The default macOS run installs Linux wheels and cannot import `pydantic_core._pydantic_core` for discovery; the inspection-only successful build used the existing macOS site-packages via `PYTHONPATH`. That proves generated routing/static contents, not Linux execution. CI runs the collector on Ubuntu without the macOS workaround. No local output bundle is to be deployed.

Evidence is reproducible and ignored under `artifacts/static-release/`: baseline/corrected CLI logs and routing JSON, `vercel-output.json`, backend/browser/static/probe logs, serial smoke logs and local desktop/mobile screenshots. Large response payloads are not part of the future workflow upload allowlist.

## Final release action

After user commit/push, green exact-SHA normal CI and deployment to the unchanged canonical project, run **Verify canonical production latency** on **main**. Its JSON artifact and job summary are the authoritative hosted record, including the workflow run link; no documentation-only follow-up commit is needed.

Release closure requires the corrected deployed SHA, homepage/every referenced asset/API/docs/sample gates, desktop/mobile usability with no material console errors, green production latency including the existing full-first ten-second gate and independent replay. A green build alone never closes the release. If these gates pass, no further planning or feature work is required.

Duplicate-project cleanup is optional administration. Hosted own-data storage remains intentionally disabled and is not a blocker for the public sample portfolio demo. Local/Docker own-data workflow and all completed MVP corrections remain preserved; see [SAMPLE_CALIBRATION](SAMPLE_CALIBRATION.md), [PLANNING](PLANNING.md), [SCENARIOS](SCENARIOS.md) and [WORKBOOK](WORKBOOK.md).
