# Prompt 2 cleanup — calibrated samples and three-way scenario deltas (24 September 2026)

Bundled inputs are versioned `sample-v2` and compact scenario snapshots `sample-scenarios-2`; stale sample hashes/versions are rejected. The 10-SKU fixture remains the exact funding stress case. Only the full sample funding changed, from the fixture's SAR 1,500/15,000 commitment, 4,000/18,000 payment and 800 transfer schedule to SAR **9,000 for weeks 1–2 then 30,000**, SAR **12,000 for weeks 1–2 then 30,000**, and SAR **1,200** transfer allowance. Pinned regression hashes confirm all non-financial inputs and withheld truth are unchanged.

Full visible demand is 101,822.7 units against 38,975 usable opening and 400 confirmed inbound units. Baseline before → selected after: fill **41.10% → 44.44%**, visible unmet **59,973.8 → 56,570.5**, commitments **SAR 92,550 → 186,336**, payments **99,050 → 192,896**, movement expense **3,100 → 3,160**, purchases **31 → 47**, movements **607 → 723**, grouped dispatches **155 → 158**. All A/B/C classes retain material shortages and **235** series remain short. Commitment headroom reaches zero and payment headroom reaches SAR 12. The roomier candidate achieved only 45.42% fill for SAR 41,800 more commitments, so it was rejected before policy evaluation.

Scenario responses and UI now show B − A scenario shock, C − B replanning, and C − A **net scenario plus replanning**. The last is explicitly not called replanning benefit. Invalid B retains dated replay reasons; its dependent deltas are unavailable while valid C − A remains numeric. Tighter funds is idempotent: exactly the first two funding weeks receive 30% of immutable baseline commitment authority at cent precision, payment ceilings remain unchanged, and other scenario families compose normally. Strict capacity/donor-reserve infeasibility, reset, snapshot immutability/provenance and arithmetic are covered.

The post-freeze withheld replay was run once per sample and not used for tuning. Fixture/full fill was **48.04% / 43.22%**; both were funding-feasible with zero cancelled movements and proposed actions exactly equaled benchmark actions. Targeted backend tests passed **31/31**; the final complete suite passed **230 tests plus 10 subtests** with two existing framework deprecation warnings. Generated contracts and the production frontend build passed; focused scenario Playwright passed **2/2**. Skill-guided live browser verification found meaningful content, expected controls, no error overlay and no captured console errors. Live fixture/full scenario smoke passed three-way deltas, deterministic repeats, two-week tighter funding, financial reconciliation and scoped evidence; the release trace reconciled all three delta families through review/export. Complete full planning first/repeat was **1.746 / 1.732 s**, **4,070,541 bytes**; combined full scenario first/repeat was **2.646 / 2.589 s**, **1,363,260 bytes**. All remain below unchanged 10/30-second and 4.5 MB gates. No algorithm, solver budget, dependency, push or deployment change was made.

---

# Prompt 1 cleanup — dated fallback shortage evidence (24 September 2026)

Implemented on the clean reviewed baseline `9264fda`; no push, deployment, budget, scenario, forecast, action-selection or solver-policy change was made. Final benchmark and no-new-action fallbacks now derive typed, dated shortage evidence from their independently replayed ledger. Benchmark construction notes remain separately labeled advanced diagnostics and no longer leak into every SKU/store reason. Visible/tail quantities reconcile exactly; equivalent adjacent evidence is coalesced and changing later causes become an explicit bounded attribution summary.

The dated analyzer checks timely transfers before purchasing-only conclusions, including donor reserve, calendars, receiving/lane headroom and grouped dispatch funding. Purchase checks use supplier/order-date grouped minimums, cent-rounded same-week deposit/balance/fee totals, existing obligations, dated supplier/shared/receiving/lane capacity and remaining headroom. A locally passing path is reported as uncertain because later stock, reserve and funding effects were not globally reoptimized.

Exact pre-change policy hashes were independently recomputed from an isolated `9264fda` archive after excluding only explanation fields. They match the corrected fixture/full hashes (`a511d451…` / `2275f5ee…`), covering every proposed/benchmark/no-action action, stock row, cash row, service quantity and summary. Targeted results: **48 planning tests passed**; **89 review/scenario/workbook/workflow/presentation/equivalence tests passed**; generated OpenAPI/TypeScript reproduced and the frontend production build passed. Python emitted two known FastAPI/Starlette deprecation warnings.

Comparable local Python 3.14.4 profile, full then fixture, before → after: full route first/repeat **2.023/0.727 → 2.979/1.729 s**, explanation **0.036/0.033 → 1.042/1.043 s**, compact **1,022,709/1,022,708 → 1,216,277/1,216,277 bytes**; fixture route **2.358/2.218 → 2.542/2.347 s**, explanation **0.005/0.005 → 0.125/0.124 s**, compact **331,541/331,542 → 371,872/371,870 bytes**. Both sizes remained deterministic `feasible_fallback` results and comfortably below the unchanged ten-second and 4.5 MB gates. These are local process-order measurements, not hosted or process-cold evidence.

Remaining limitation: evidence proves only the stated bounded single-path blocker. When timely paths pass or different paths fail different checks, the UI says no single cause was established and directs the user to scoped stock evidence; it does not claim a globally feasible improvement.

---

# Final public-sample release closure — 24 September 2026

**Final verdict:** Pass 5 is closed; Pass 6 is closed; the public sample demo is ready; calculation and hosted-latency gates passed; portfolio-MVP feature development is complete. This section supersedes all pending-readiness statements in the historical sections below.

The verified application release is exact commit **`ff2e42d907f6b0a83811849c7efab10ff1007dcc`**. Normal [Verify planning MVP run 35967399001](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35967399001) completed successfully for that exact commit, including the established application, browser, Linux/container and local-storage workflow verification matrix.

The canonical host is [https://demand-supply-planning-intelligence.vercel.app](https://demand-supply-planning-intelligence.vercel.app). It resolves to production deployment **`dpl_9zrziwJbe3abDQyxtA1hS6gfjnPa`**, immutable URL [https://demand-supply-planning-intelligence-3gdxptwpt.vercel.app](https://demand-supply-planning-intelligence-3gdxptwpt.vercel.app), state **READY**, target **production**, region **`iad1`**, deployed commit **`ff2e42d907f6b0a83811849c7efab10ff1007dcc`**.

Two consecutive unchanged canonical production-latency workflows passed:

| Workflow run | Full first HTTP / engine | Full repeat HTTP / engine | Compact bytes | Result |
|---|---:|---:|---:|---|
| [35967540536](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35967540536) | **9.033 / 5.381 s** | **3.248 / 2.557 s** | approximately 1,022,712 | success |
| [35968872124](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35968872124) | **7.969 / 4.841 s** | **2.995 / 2.429 s** | approximately 1,022,712 | success |

Both workflows used the canonical production hostname, passed the unchanged under-ten-second cold full-sample gate, returned structured `feasible_fallback` plans, passed independent replay, response-size, reconciliation and determinism checks, completed scenario capture and scoped-detail checks, uploaded retained measurement artifacts and reported no probe failures. Sample planning, scenarios and authoritative evidence are therefore production-verified.

The own-data boundary remains intentionally narrower. Local and Docker workbook upload, validation, review, regeneration, acceptance, export and portable reopen are verified. Hosted workbook upload, durable review state and accepted-export persistence remain disabled until an authorized private persistent-storage adapter is implemented, configured and verified for transport, isolation, expiry and deletion. This does **not** block the public sample portfolio demo, but it does block describing the application as a fully hosted own-data production service.

No additional feature or latency work is pending for the public portfolio MVP. Historical sections below remain as the audit trail for earlier failures and corrections; their statements that exact-commit CI, deployment or canonical latency acceptance were pending are superseded by this closure.

---

# Final cold-start latency correction — 24 September 2026

**Status: locally verified and ready to commit; exact-commit CI, deployment and canonical-host acceptance remain pending.** This work started from clean `17eaa4be79b7b8bdc7977a24f329438742db36b3`. No push, deployment, workflow dispatch, Vercel setting, latency/size gate, dataset dimension, planning rule or response contract was changed.

The user-supplied second canonical failure was full first/repeat **11.289 / 3.587 s HTTP**, **6.641 / 3.195 s engine**, **1,022,712 bytes**, `feasible_fallback`, independent replay passing, `iad1 → iad1`. Health was **0.216 s** and fixture first/repeat **4.425 / 2.753 s**. The first full request therefore contained approximately **4.648 s** outside the reported engine, versus **0.392 s** on repeat. This supersedes the earlier **12.358 / 8.060 s HTTP/engine** cold result as the latest hosted baseline; it does not count as evidence for this uncommitted correction.

The missing interval is now observable from the earliest application-owned standard-library timestamp through FastAPI construction, workflow/scenario route imports, lifespan startup, request body/schema handling, bundled sample construction and validation, provenance normalization, planning, response construction, FastAPI response validation/serialization and ASGI response readiness. Fixed-name numeric `Server-Timing` is always returned; structured timing logs remain opt-in with `PLANNING_DIAGNOSTICS=1`. The canonical probe stores the raw header and a fixed-allowlist parsed map. No input values, paths, identifiers, environment values or stack traces enter either surface.

The concrete cold-path defect was cross-row validation performing approximately **310,000 failed dynamic Pydantic attribute lookups** while walking the 99,160-row full history. Row schema membership is now resolved once per table, preserving the same row/reference checks and issue ordering. Planning also requests an internal forecast projection containing only the selected 56-day points and buffer/identity fields it consumes; it no longer constructs unused per-series final-check, history and public response models. Public forecast responses are unchanged. Hosted-disabled storage no longer creates an unused temporary directory, cleanup thread or exit handler. These changes reuse immutable work only inside the same calculation/sample object; they do not cache a completed recommendation or require a previous request.

Import-graph audit from a fresh interpreter confirmed `/api/plan/sample` does **not** import SciPy/HiGHS, NumPy, pandas, OpenPyXL or `backend.app.planning.optimizer`. The full plan continues to disclose `joint_model:not_attempted`. Workflow route declarations import lightweight workbook/review/scenario modules, but Excel itself remains function-local and absent from the sample request process. The measured route-import cost is **22.9–31.7 ms**; FastAPI construction is approximately **0.09 ms**. No broad module split was justified by that evidence.

Fresh-process macOS arm64 / Python 3.14.4 evidence was produced by [cold_start_profile.py](../scripts/cold_start_profile.py). Each of three samples started a new production-style Uvicorn process, performed only a TCP readiness check before the measured full plan, then issued one ordinary repeat on the same server. There was no health, fixture, forecast, sleep-based warm-up or prior planning request. Stable policy signatures matched across all six calculations.

| Final full-sample phase | Fresh process 1 | Fresh process 2 | Fresh process 3 |
|---|---:|---:|---:|
| Process launch to listening | 0.302 s | 0.287 s | 0.250 s |
| Module bootstrap/import | 0.210 s | 0.167 s | 0.166 s |
| Request parsing/validation | 0.0096 s | 0.0051 s | 0.0049 s |
| Sample construction + validation | 0.637 s | 0.611 s | 0.606 s |
| Input normalization/provenance | 0.079 s | 0.078 s | 0.080 s |
| Planning engine | 1.294 s | 1.267 s | 1.269 s |
| Response construction | 0.00004 s | 0.00004 s | 0.00004 s |
| Response serialization | 0.0022 s | 0.0022 s | 0.0023 s |
| ASGI response ready / HTTP total | 2.024 / **2.025 s** | 1.966 / **1.967 s** | 1.963 / **1.965 s** |
| Startup + HTTP | **2.327 s** | **2.254 s** | **2.215 s** |
| Ordinary repeat HTTP | 0.729 s | 0.729 s | 0.734 s |

The preceding correction's local component baseline was **2.266 s route / 1.366 s engine / 0.820 s sample input / 0.791 s forecast / 0.314 s benchmark**. The final wall-clock component profile is **1.948 / 1.262 / 0.605 / 0.684 / 0.316 s** respectively; replay/explanations remain live at **0.124 / 0.033 s**. First response size is **1,022,713 bytes** (the one-byte repeat variation is generated timing text). These values meet the requested local targets with substantial margin, but macOS measurements cannot establish corrected Vercel performance.

Behavioral parity is pinned by the pre-existing full-precision fixture/full forecast and complete-policy hashes. The cold/repeat comparison removes only generated IDs/timing and covers status/stages, forecasts, purchases/movements with action IDs/dates/quantities/values, commitments/payments/headroom, service/unmet demand, explanations and all replay ledgers. Scenario capture matches the returned actions, summary and cash. Final local verification:

- Complete backend suite: **220 passed, 10 subtests passed**, two existing framework deprecation warnings, **311.24 s**.
- Solver smoke passed SciPy 1.18.1 and HiGHS status 0. Contract export/generated TypeScript were byte-reproducible; production frontend build passed.
- Complete Playwright suite: **26/26 in 2.6 minutes**. Separate skill-guided browser inspection found meaningful content, no error overlay, no captured console errors and expected navigation/controls.
- Forecast, complete planning, compact/complete/scoped evidence, scenarios and fixture/full upload-review-accept-export-portable-reopen smokes passed. Full complete planning remained 31 purchases / 607 movements, exact SAR **92,550 commitments / 99,050 payments**, nonnegative headroom, independent replay and repeat determinism.
- `pip check`, installed npm-tree resolution, production `npm audit` (**0 vulnerabilities**), Python compilation and `git diff --check` passed. Docker/Podman/Colima/Lima remains unavailable locally, so exact-commit Linux/container evidence is pending CI.

The corrected worktree is ready to commit and enter normal CI. It is **not production-accepted**. After an authorized exact-SHA deployment, confirm the canonical alias serves that SHA, run normal exact-commit CI, then obtain **two consecutive unchanged** `Verify canonical production latency` passes and record both run/job IDs plus all cold/full phase measurements. Do not rerun an unchanged failure hoping for favorable placement.

---

# Narrow production-latency correction — 23 September 2026

**Status: locally verified and ready to commit; exact-commit CI, deployment and canonical-host acceptance remain pending.** Started from clean `d5eda7ad637e7b40ce799b6ae7bb6c786bf257cc`. No push, deployment, workflow dispatch, Vercel setting, sample dimension, planning rule, response contract or latency threshold was changed.

Manual production-latency [run 35858535758](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35858535758), job `107172785296`, reached the canonical deployment from GitHub's `westcentralus` runner over `sfo1 → iad1`. Its full first request failed the unchanged ten-second gate at **12.358 s** (first byte **12.131 s**, reported engine **8.060 s**, **1,022,712 bytes**). The repeat was **3.760 s** / engine **3.068 s**. Both returned `feasible_fallback`; independent replay passed and Vercel reported no runtime errors. The Ubuntu 26 annotation is informational.

Fresh-process profiling identified forecast candidate preparation as the cold engine bottleneck, with deterministic benchmark generation second. The evaluator constructed more than 200,000 fully validated `ForecastDay` response models merely to score internal candidate windows, rescored common horizon prefixes independently, and performed repeated event checks for the 232/240 full-sample series with no applicable event. The benchmark repeatedly scanned future receipt ranges and the complete offer/lane/assortment collections. Replay, explanations, response validation and JSON serialization were not material bottlenecks. The full path already avoided the joint optimizer; the profiler previously obscured that fact by importing SciPy before measuring full.

The correction keeps identical arithmetic and authoritative contracts while using lightweight date/quantity points only during candidate scoring, scoring the 7/protection/28-day prefixes in one pass, constructing public `ForecastDay` models only for the selected 56-day forecast, short-circuiting empty event sets, and indexing immutable request-local benchmark inputs/future receipt totals. Exact golden hashes for all forecasts and the complete policy remain unchanged. New regressions compare the combined scorer with the original per-horizon function and compare the entire cold/repeat result after removing only generated IDs/timing; the latter includes status/stages, actions and dates, quantities/values, commitments/payments/headroom, service/unmet results, explanations, all three replay ledgers and scenario baseline capture.

Fresh-process local macOS arm64 / Python 3.14.4 measurements, compact production route, no preceding health/fixture/forecast calculation:

| Full phase | d5eda7a before | Corrected after |
|---|---:|---:|
| API module import | not repeated in request | 0.154 s |
| Sample construction + validation | 0.819 s | 0.820 s |
| Forecast preparation | 1.414 s | **0.791 s** |
| Deterministic benchmark / candidate generation | 0.391 s | **0.314 s** |
| Independent replay (three calls) | 0.122 s | 0.121 s |
| Shortage explanations | 0.033 s | 0.033 s |
| Planning engine | 2.064 s | **1.366 s** |
| Complete route / response construction | 2.963 s | **2.266 s** |
| Contract validation / JSON serialization | 0.0007 / 0.0021 s | 0.00001 / 0.0022 s |
| Response bytes | 1,022,713 | 1,022,713 |

Corrected repeat route/engine was **0.718 / 0.637 s**; repeat reuse is retained but is not the cold evidence. The cold engine improved approximately **34%** in the final instrumented comparison. Values are local evidence only and do not establish Linux/container or canonical-host performance. Corrected-commit normal CI and production workflow run IDs are pending because this worktree is uncommitted and the instruction forbids push/deploy/dispatch. After authorized deployment of the exact corrected commit, require **two consecutive unchanged manual production-latency workflow runs** to pass the cold full request; retain both artifacts and do not select a favorable rerun.

Completed local verification:

- Focused optimized-path/scoring regressions passed; complete backend suite passed **219 tests, 10 subtests**, with two existing framework deprecation warnings, in **336.24 s**. The first sandboxed run had 218 passes and one loopback-bind denial; the complete permitted rerun is the recorded result.
- Solver smoke passed SciPy 1.18.1 and cold/warm HiGHS status 0. Production forecast smoke passed fixture **0.027 / 0.026 s** and full **0.933 / 0.159 s**. Complete planning smoke passed fixture **2.587 / 1.699 s** and full **1.404 / 0.724 s**; full engine was **1,293.4 / 630.3 ms** with 31 purchases, 607 movements, exact SAR 92,550 commitments / 99,050 payments, independent replay, nonnegative headroom and repeat determinism. Those planning labels followed forecast requests and are not cold-start evidence.
- Compact/complete/scoped-evidence smoke, production scenario smoke and fixture/full upload-review-accept-export-portable-reopen smoke passed. Full scenario compare first/repeat was **2.270 / 2.305 s**; future-path comparison **3.052 s**.
- Contract export and generated TypeScript were byte-reproducible; frontend production build passed. The complete Playwright rerun passed **26/26 in 2.7 min**. An earlier run had one transient response timeout (25/26); the isolated case then passed in 15.8 s before the clean complete rerun. Skill-governed browser verification also confirmed meaningful content, no error overlay and expected navigation/controls.
- `pip check`, installed npm-tree resolution, production `npm audit` (**0 vulnerabilities**), Python compilation and `git diff --check` passed. Docker/Podman/Colima/Lima is unavailable locally, so corrected Linux/container evidence remains an exact-commit CI responsibility.

The worktree is ready to commit and submit to CI. It is **not yet ready to claim deployment acceptance**: deploy only the reviewed exact commit after normal CI passes, then complete the two consecutive unchanged canonical production-latency runs described above.

---

# Final Pass 6 closure check — 20 September 2026

**Verdict: Pass 6 remains open — production latency gate not yet proven.** This section supersedes prior statements that corrected CI, Docker verification or deployment did not exist. Earlier observations remain below as history. Hosted own-data is a separate, intentionally blocked release gate; it is not by itself the reason public-sample Pass 6 remains open.

## Exact candidate, CI and deployment

Local `main`, HEAD and GitHub's live `main` commit lookup all confirmed **03bb1affbe8448849725ad34c939de9601e2dc67** before this closure work. [Verify planning MVP run 35493689224](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35493689224), [job 106032834212](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35493689224/job/106032834212), completed **successfully**. The job log explicitly checks out that SHA; this conclusion is based on logs and completed step results, not just a badge.

CI used Ubuntu **24.04.5**, runner **2.337.0** in **Azure westus**, Python **3.14.7**, Node **24.20.0**. Its HTTP checks address the local Docker container, not the canonical public host:

| Exact-commit workflow check | Actual log result |
|---|---|
| Complete backend suite | **209 passed, 2 warnings, 803.23 s** |
| Host and container solver smoke | Both passed; HiGHS status 0, x=2 |
| Contract export, generated types, committed-type comparison | All passed; `git diff --exit-code -- frontend/src/contracts.generated.ts` succeeded |
| Frontend production build | TypeScript and Vite passed; Vite build 1.16 s |
| Complete browser suite | **26 passed, 4.2 min** |
| Docker build, startup and health | All passed; dependency-download retry recovered during build |
| Forecast smoke | Built frontend, health, fixture/full calculations passed |
| Complete planning | All four rows below passed independent feasibility, finance, dimensions, size, determinism and ten seconds |
| Compact planning and scoped evidence | Passed compact/complete equality, repeated evidence, stock/cash/provenance, ten seconds and 4.5 MB |
| Scenarios | Original/frozen/replanned comparisons, invalid frozen-policy disclosure, future-path delays, finance, determinism and scoped evidence passed |
| Component profiling | Fixture/full first/repeat passed; three independent replay calls retained |
| Upload/review/accept/export/reopen | Fixture/full passed with CI's **local storage driver**; deterministic downloads, provenance, financial reconciliation, cleanup and session reset passed |

| CI complete plan | HTTP s | Engine ms | Bytes | Purchases / movements |
|---|---:|---:|---:|---:|
| Fixture first | 3.199 | 3,139.1 | 786,693 | 24 / 311 |
| Fixture repeat | 2.439 | 2,402.2 | 786,693 | 24 / 311 |
| Full first | 6.159 | 5,943.3 | 3,753,092 | 31 / 607 |
| Full repeat | 2.450 | 2,241.3 | 3,753,092 | 31 / 607 |

Fixture commitments/payments were **SAR 91,606 / 97,746**; full **SAR 92,550 / 99,050**. All four independently replayed policies were honestly **`feasible_fallback`**, with fixture `visible_must_stock:time_limit` and full `joint_model:not_attempted`, followed by the deterministic benchmark. No optimality or solver improvement is claimed.

CI compact full first/repeat HTTP was **2.329 / 2.444 s**, **1,022,713 / 1,022,711 bytes**; full capture **0.990 / 0.851 s**, scoped detail **2.086 / 2.214 s**, **110,149 bytes**. Full component-profile route first/repeat was **8.793 / 2.439 s**, forecast **3.986 / 0.178 s**, benchmark **1.360 / 1.326 s** and independent replay **0.296 / 0.282 s**. These are container evidence, not hosted latency or proven Vercel cold starts.

Both deployment-ID and canonical-host lookups confirmed **dpl_BHtMKw2mgLGXCksj6aB2GqnYBy27**, **READY**, target **production**, region **iad1**, exact **03bb1aff**. The canonical alias currently resolves to that deployment:

- Canonical: [demand-supply-planning-intelligence.vercel.app](https://demand-supply-planning-intelligence.vercel.app)
- Immutable: [demand-supply-planning-intelligence-qr2woqqgp.vercel.app](https://demand-supply-planning-intelligence-qr2woqqgp.vercel.app)

Exact-deployment runtime logs were inspected for **2026-09-20 06:15:29–07:09:00 UTC**. They contain **one HTTP 400: GET `/` at 06:21:59 UTC**. The connector supplies no cause for it; it predates this closure probe work and must not be silently classified as harmless. Separate 5xx, error/fatal and `timeout` searches returned no entries. There is no new canonical POST verification run to correlate yet. The connector does not expose invocation duration; absence of returned error logs is limited to this window and available telemetry.

## Production latency and manual workflow

The user confirmed no existing authorized remote shell/runner was available. The Codex shell's observed **bom1 → iad1** path and reported **9–14 s TLS establishment** must not count as passing production latency evidence. Earlier unsuccessful measurements remain in the history. Connection/TLS, post-connection waiting, reported calculation, response headers and body transfer must stay separate; no measured application defect has been established by these connection-heavy observations.

No new valid production POST timings were obtained in this closure. An initial ignored local helper rejected an unsupported curl option before sending any request; it is not latency evidence and was superseded by the tested workflow harness. The public session-capability GET via the connected Vercel tool returned HTTP 200 with **`enabled: false`, `driver: disabled`** at 07:06:45 UTC; its tool wall time is not an HTTP phase measurement.

| Required canonical measurement | New production result |
|---|---|
| Health, fresh connection | Pending manual workflow |
| Fixture compact first / repeat | Pending manual workflow |
| Two consecutive full compact plans | Pending manual workflow |
| Full-action scenario capture first / repeat | Pending manual workflow |
| SKU001 / S1 detail first / repeat | Pending manual workflow |

At the user's explicit direction, added [production-latency.yml](../.github/workflows/production-latency.yml), a separate **`workflow_dispatch`-only**, `ubuntu-latest` workflow. The existing green `verify.yml` is unchanged. It requires no Vercel secret, deployment access, Python package installation or new service. Read-only repository permissions and one concurrency group serialize manual runs without cancelling an in-progress run. Checkout/setup-python/upload-artifact use maintained **v7 / Node 24** actions; their official manifests and artifact inputs were checked.

[scripts/production_latency.py](../scripts/production_latency.py) uses the **canonical hostname only**, curl and the standard library. Each request group starts a new curl process; `--next` sends its repeat serially on the same session. It asserts observed fresh/reused connection counts. It records DNS, TCP-ready, TLS-ready, first-byte, body-drain and total seconds, bytes, HTTP/curl status, HTTP version, peer IP, Vercel request/region ID, optional Server-Timing, reported calculation, result status, solver stages and replay status. DNS/TCP/TLS are cumulative milestones; reused connections have no new TCP/TLS handshake. Absent API fields are recorded as null, not invented.

The probe retains **10 s** and **4.5 MB**, uses the existing `validate_plan` and `stable_plan` checks, and verifies capture/detailed evidence against a separate complete replay for the returned actions. Both sample sizes retain their complete dimensions. Slow/malformed/error responses remain failures; later safe checks continue, and missing prerequisite responses explicitly fail dependent checks. There are no retries, sleeps, redirects, warm-up calculations, skipped assertions or complete-response caches. Complete responses fetched for equality also retain the runtime/size checks.

The always-run artifact step uploads raw curl measurements, request/response bodies, headers, errors, aggregate assertions and runner/probe revision metadata under `production-latency-<run_id>-<attempt>` for 30 days. These requests contain only public bundled sample inputs; the workflow does not use private sessions. The runner region is **not assumed to be iad1**: inspect its job setup location and the recorded Vercel request IDs. A green manual run is necessary; alias/deployed-SHA confirmation and exact-deployment runtime-log correlation for its UTC interval remain required before the public verdict closes.

## Verification of the new workflow/harness

- `.venv/bin/python -m unittest backend.tests.test_production_latency -v`: **8 passed**. Includes actual curl POST connection reuse on a loopback server, retained slow-first failures, malformed/failed responses, missing measurements, size/reuse failures, money/policy drift and scoped identity mismatch rejection.
- `/private/tmp/planning-closure-actionlint/actionlint .github/workflows/production-latency.yml` (v1.7.12): passed. Official release binary used from a temporary directory; repository dependencies unchanged.
- Full new probe sequence against the **unchanged local API**, with a test-only in-process hostname/protocol substitution: all **11 requests / 105 assertions** and correctness/transport gates passed, including first/repeat connection counts, deterministic policy and authoritative 280-row evidence. Recorded in ignored `artifacts/closure-local-sequence/`; expressly **not production acceptance**.
- `.venv/bin/python -m compileall -q scripts/production_latency.py backend/tests/test_production_latency.py`: passed. `git diff --exit-code -- .github/workflows/verify.yml` plus byte comparison to HEAD: unchanged. Reviewed command references and **25 local documentation-link targets**, all valid. Final `git diff --check`: passed.
- `.venv/bin/python -m pytest -q`: **217 passed, 2 existing warnings, 10 subtests passed in 333.69 s**. This is the final local suite including the eight new manual-probe tests; it is separate from the deployed candidate's 209-test GitHub Actions run.

No frontend, application calculation, contracts, dependencies, deployment configuration or existing verification workflow was changed. Frontend build/browser/Docker application gates are already green for **03bb1aff**; they were not rerun solely for the separate probe. New exact-commit CI for the added workflow/script/tests is pending the user's push. The manual workflow was **not pushed or dispatched**.

**Next action:** the user pushes the workflow, obtains green verification for the new commit and manually runs **Verify canonical production latency** from GitHub Actions. Retain the artifact, verify the exact canonical deployment identity again, and inspect its runtime logs over the recorded interval. Public Pass 6 remains pending that successful canonical-host run and correlation. Hosted own-data remains separately disabled pending authorized private storage and real-provider verification; CI conformance/local-storage success does not create a production provider. The existing `demand-supply-planning-intelligence-hahy` project was confirmed in the Vercel project list and remains non-blocking housekeeping; neither project was changed.

---

# Final focused Pass 6 correction — 20 September 2026

Started from clean **055eb0a4f6ee78c77f697569a5acbd044a2f5c53**. This section supersedes earlier readiness statements; historical results remain below.

## Baseline CI and canonical deployment

[GitHub Actions 35491100761](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35491100761), job **106026056837**, completed **successfully** for 055eb0a. Logs confirm **197 backend tests in 590.51 s**, **26 browser tests in 4.3 min**, solver, contracts, production build, Docker build/start, container solver, forecast, complete/compact planning, scoped evidence, scenarios, component profile and upload/review/accept/export/reopen. Baseline Ubuntu/container full planning HTTP was **4.349 / 4.462 s** (engine **4,114.3 / 4,287.9 ms**). This is not CI for this new worktree.

Canonical metadata confirms deployment **dpl_vPgb8yq7ivQ7FxDqgAZGkpmotE6n**, immutable alias `demand-supply-planning-intelligence-10cys4089.vercel.app`, region **iad1**, exact **055eb0a**, serving `https://demand-supply-planning-intelligence.vercel.app`. Build readiness is not runtime acceptance. The separate `demand-supply-planning-intelligence-hahy` check is project housekeeping; no project was deleted, disconnected or changed. Its guessed public hostname did not resolve to a deployment through the connector, and project lookup encountered a connector argument-mapping error; no independent second-project runtime claim is made.

## Measured hosted boundary

User-supplied independent measurements retain full HTTP **25.74 / 20.34 / 19.79 s**, reported plan **7.94 / 8.01 / 7.84 s**, and fixture HTTP **23.20 s** versus plan **3.64 s**. One full response reached headers at **19.03 s** and drained in **0.77 s**. A separate fixture flow was plan/capture/detail **17.96 / 13.38 / 13.61 s**. These failures are not discarded because a subsequent repeat is faster.

New serial curl checks of the same canonical 055eb0a deployment in this correction:

| Request | TLS ready s | First response byte s | Body drain s | Total HTTP s | Reported calculation ms | Bytes |
|---|---:|---:|---:|---:|---:|---:|
| Health | 0.277 | 2.812 | 0.001 | 2.813 | unavailable | 104 |
| Full first | 0.172 | 11.516 | 0.774 | **12.290** | 7,536.7 | 1,022,713 |
| Full repeat | 0.176 | 8.535 | 0.705 | **9.240** | 7,737.1 | 1,022,712 |
| Fixture | 0.177 | 4.992 | 0.433 | **5.424** | 3,647.0 | 331,545 |
| Fixture capture | 0.173 | 2.052 | 0.491 | **2.543** | 896.0 | 179,504 |
| Fixture detail | 0.199 | 2.133 | 0.264 | **2.397** | 1,118.7 | 110,160 |

DNS/connect/TLS and full response metrics are retained in ignored `artifacts/final6-host-*-timing.json`; body drain is total minus first byte. These checks used serial public synthetic requests without concurrent hosted calculations. Fixture detail returned 280 rows and matching cash/provenance. The first full request still fails ten seconds and two consecutive passing full requests were not established. These are baseline observations, not measurements of the new correction or proven instance-cold starts.

The available Vercel runtime-log connector confirms successful invocation paths/statuses on the exact deployment, but exposes neither function duration nor startup/ASGI phase measurements. Diagnostics were off on this deployment. Client time cannot establish Vercel invocation start, new-instance status or attribute all pre-header waiting to Python. The variable residual before headers remains a measured **unattributed pre-header residual across application, platform and network**, not a proven fixed twelve-second network or solver delay. A separately authorized diagnostic deployment is needed to correlate the bounded new phase output with platform invocation duration and client timing. The retained HTTP gate is unchanged.

## Implemented local correction

- Defer `openpyxl` and its NumPy import until actual workbook parsing/export. Defer accepted-snapshot module loading to workflow routes. SciPy/HiGHS remains a lazy optimizer import; the full sample does not attempt a joint solve. Public import regressions also exclude private-provider and test utility modules.
- Serialize initial bundled-sample construction: Python LRU caching can execute the same first miss concurrently, producing equal but distinct objects and defeating exact-object registration. A lock now makes simultaneous catalog/forecast requests share one constructed sample; a concurrency regression verifies it.
- Add at most two derived forecast-preparation entries, eligible only for the exact server-registered fixture/full objects with unchanged complete SHA-256. The key includes dataset hash, engine/schema versions, internal forecast version and preparation/horizon version. Return independent copies and fresh forecast calculation UUIDs. Unregistered uploaded/reviewed copies and mutated sample objects bypass reuse. Misses run the unchanged evaluator; no actions, recommendations, replay ledgers, responses or private review state are cached.
- Keep scenario transformation, snapshot/data/action/scenario/forecast identity checks and every independent stock/cash replay. Reuse only the unchanged bundled forecast preparation; transformed future-path inputs still compute from their complete current contents. Private detail still validates the exact run/reference/revision and rejects stale reviews. Public detail retains its existing versioned snapshot/action identity, rather than inventing an authenticated plan-UUID guarantee.
- Add opt-in bounded timings for application import, workflow import, FastAPI setup/startup, request body, dataset/context preparation, planning, review attachment, actual FastAPI response validation and Pydantic serialization, ASGI response start/completion, and forecast reuse. Nested/startup metrics are explicitly distinct from per-request durations. Only fixed metric names and numeric times/counts are emitted, without dataset values, identifiers, provider errors or stack traces. No diagnostic environment setting was enabled remotely.
- Treat private metadata promotion/retirement as the commit point. Blob cleanup failures now retain tombstones and log only `private_cleanup_deferred` plus a count; they cannot hide a committed replacement, deletion/reset or successful upload finalization. Explicit sweep still reports failure nonzero and retries queued work. Accepted files stay owner-checked and readable; old references never return. Pre-commit and original validation errors remain failures.
- Tighten the **additional compact transport smoke** to the requested ten-second capture/evidence limits. Existing complete planning, scenario comparison, response-size, feasibility, financial, browser and Docker gates remain intact; complete-plan validation also explicitly reconciles movement-fee payments to the reported movement expense. External contracts, frontend source and deployment settings are unchanged.

## Local verification

Final serial local request measurements (same runtime, isolated 055eb0a baseline versus corrected process):

| Request | Baseline HTTP s | Corrected HTTP s | Corrected plan/evidence ms | Bytes |
|---|---:|---:|---:|---:|
| full first | 2.832 | 2.940 | 2,056.5 | 1,022,712 |
| full repeat | 2.061 | 0.816 | 728.9 | 1,022,712 |
| full capture | 1.654 | 0.410 | 241.3 | 381,064 |
| full detail | 2.000 | 0.732 | 635.5 | 110,148 |
| fixture first | 2.647 | 2.599 | 2,583.4 | 331,545 |
| fixture repeat | 2.424 | 2.179 | 2,163.9 | 331,544 |
| fixture capture | 0.266 | 0.066 | 38.8 | 179,504 |
| fixture detail | 0.319 | 0.118 | 101.7 | 110,160 |

The first uncached full request did not materially improve. Repeat work benefits from reuse; those cache hits are not cold-start or hosted proof. Actual ASGI/response validation/serialization phases and startup timings are in [RELEASE_AUDIT.md](RELEASE_AUDIT.md). All requests passed ten seconds, response size, deterministic actions/totals/explanations and authoritative scoped stock/cash/provenance checks.

### Final commands and actual results

Local runtime: macOS arm64, Python **3.14.4**, Node **24.21.0**, installed Chrome. Production HTTP checks ran serially against `PLANNING_DIAGNOSTICS=1 PORT=8030 ./scripts/start.sh`. Baseline component checks used an isolated `git archive` of 055eb0a with the same Python environment. No dependency upgrades or workflow changes were made.

| Executed command/check | Actual result |
|---|---|
| `.venv/bin/python -m pytest -q` | **209 passed, 2 existing warnings, 351.05 s** on final source. Includes 14 private-provider conformance tests, 6 injected-cleanup tests, 4 preparation reuse/evidence/concurrency cases and existing calculation-equivalence tests. |
| `PORT=8030 CHROME_PATH=/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome npm --prefix frontend run test:e2e` under Node 24 | **26 passed in 2.8 min**; frontend source/assertions unchanged. Production browser verification also displayed actual forecast results and navigation with no browser errors. |
| `.venv/bin/python -m scripts.export_contracts`; `npm --prefix frontend run generate:types` | Passed; final regeneration reproduced byte-identical OpenAPI and generated TypeScript. |
| `npm --prefix frontend run build` | TypeScript and Vite production build passed: 41 modules, JS 304.94 kB / 91.82 kB gzip, CSS 13.52 kB / 3.84 kB gzip. |
| `.venv/bin/python -m scripts.solver_smoke` | Passed installed SciPy/HiGHS smoke. |
| `.venv/bin/python -m scripts.smoke --url http://127.0.0.1:8030` | Built page, health and real fixture/full forecast requests passed. |
| `.venv/bin/python -m scripts.planning_smoke --url http://127.0.0.1:8030` | All four complete-ledger requests below passed runtime, size, dimensions, independent replay, financial reconciliation and repeat determinism. |
| `.venv/bin/python -m scripts.planning_transport_smoke --url http://127.0.0.1:8030` | Complete/compact actions, totals and explanations equal; fixture/full scoped stock, cash and provenance equal complete replay; repeated evidence deterministic. Every planning/capture/evidence request passed **10 s** and **4.5 MB**. |
| `.venv/bin/python -m scripts.scenario_smoke --url http://127.0.0.1:8030` | Passed comparisons, future-path changes, invalid-policy metric protection, independent replay, determinism and response-size gates. |
| `.venv/bin/python -m scripts.workflow_smoke --url http://127.0.0.1:8030` | Fixture/full upload, validation, review/regeneration/acceptance, XLSX/snapshot reconciliation, repeated download, reopen and reset passed using local storage. |
| `.venv/bin/python -m scripts.release_trace --url http://127.0.0.1:8030 --output artifacts/final6-trace.json` | Forecast/action/dated cash/scenario/review/export trace reconciled. |
| `.venv/bin/python -m scripts.planning_profile`, isolated baseline then current | All fixture/full first/repeat profiles passed; three independent replay calls retained. Components and fresh imports recorded in RELEASE_AUDIT. |
| `.venv/bin/python -m pytest -q backend/tests/test_policy_replay.py` | **7 passed in 0.23 s**, in addition to complete-suite coverage. |
| `.venv/bin/python -m scripts.policy_replay --size fixture --output …` and `--size full`, each twice | All four exited zero; each size's output was **byte-identical**. Proposed/benchmark actions match; stock/transit/acquisition value and funding reconcile. |
| `.venv/bin/python -m pip check`; `npm --prefix frontend ls --depth=0` | Both passed. |
| `.venv/bin/python -m compileall -q backend scripts`; `git diff --check` | Passed, including final source regeneration and documentation diff check. |

Final complete-ledger smoke (after the separate first-miss boundary measurement; these are preparation reuse hits, not cold starts):

| Request | HTTP s | Engine ms | Bytes | Actions purchase / movement | Replay / finance / determinism |
|---|---:|---:|---:|---:|---|
| Fixture first | 2.238 | 2,195.1 | 786,691 | 24 / 311 | passed / passed / reference |
| Fixture repeat | 2.178 | 2,161.4 | 786,693 | 24 / 311 | passed / passed / matched |
| Full first | 0.831 | 732.2 | 3,753,092 | 31 / 607 | passed / passed / reference |
| Full repeat | 0.820 | 721.6 | 3,753,092 | 31 / 607 | passed / passed / matched |

Fixture commitments/payments remain **SAR 91,606 / 97,746**; full **SAR 92,550 / 99,050**. Movement-fee payments explicitly equal movement expense. All retain honest `feasible_fallback`, fixture's two-second best-effort challenger and full's unattempted joint stage. Full retains 240 series and 16,800 stock rows. No complete recommendation is cached.

An initial backend run found three workbook tests patching the former eager parser import. Their patches now target `openpyxl.load_workbook` at the actual deferred-import boundary; the resource-cleanup assertions were retained, the three focused tests passed, and the final complete suite passed. The later concurrent first-sample identity issue was corrected and covered before the final 209-test run.

Changed files: `backend/app/data/{accepted,private_storage,workbook,workflow_api}.py`; `backend/app/{diagnostics,main}.py`; `backend/app/planning/{inputs,preparation}.py`; new cleanup, preparation and public-import regressions plus existing diagnostics/workbook tests; `scripts/{planning_smoke,planning_transport_smoke}.py`; BUILD_STATUS, DEPLOYMENT, RELEASE_AUDIT, PRIVATE_STORAGE and PLANNING docs. External contracts, frontend files and deployment configuration have no diff. Detailed ignored verification logs are `artifacts/final6-*`; they are local evidence, not published CI artifacts.

**No new exact-commit CI, corrected deployment or Docker result is claimed.** Docker, Podman, Colima and Lima are unavailable here. Baseline green Linux/Docker CI is explicitly separate from these corrected macOS results.

## Release boundary

The canonical host still reports private workflows disabled. No authorized blob/transactional metadata provider or credentials were introduced. [PRIVATE_STORAGE.md](PRIVATE_STORAGE.md) defines the required real-provider integration and lifecycle verification.

**Neither release gate can close yet.** Public sample needs CI for the exact new correction and a separately authorized canonical deployment passing fixture/full planning, two consecutive full requests, capture and evidence under ten seconds with all reconciliation/size gates. Full hosted own-data additionally needs authorized private persistent storage and the complete real-provider isolation/lifecycle/workflow checks. The request prohibits automatic push/merge/deploy/provisioning/settings changes, so new remote CI/deployment cannot be obtained within this local correction. No such action was performed.

---

# Pass 6 focused release correction — 20 September 2026

Started from clean `e51af6fc1dc5338e4f9d54380fe7acceca55edd1`. This section supersedes older release-readiness statements; historical evidence below is retained.

**Exact baseline CI is green:** [GitHub Actions 35464690297](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35464690297), job `105954779663`, completed successfully for `e51af6f`. It passed 173 backend tests (655.28 s), 26 browser tests (5.8 min), solver smoke, reproducible contracts, production build, Docker build/start, container solver, forecast/planning/scenario smokes, container component profiling and upload/review/accept/export/reopen. Fixture planning HTTP was 3.506 / 3.564 s; full was 9.162 / 9.304 s (engine 8,946.4 / 9,085.4 ms), with deterministic, financially reconciled, independently replayed fallback results. This is baseline evidence, **not CI for these uncommitted changes**.

The canonical Vercel deployment was confirmed at **e51af6f**, deployment `dpl_EjnDRZ4PWPW9qu3HvjctMyHpBvLM`, project `prj_9wUSzLP3zKbvVinWCeNvmyDelVh5`, `iad1`, immutable alias `demand-supply-planning-intelligence-f7633owp1.vercel.app`, production alias `demand-supply-planning-intelligence.vercel.app`. A serial baseline full request in this correction took **19.567 s HTTP / 11,446.3 ms engine / 3,753,044 bytes**, with first byte at 17.997 s. Independent replay passed and status remained `feasible_fallback`. This is another failed baseline runtime observation, not a cold-start claim. The host still reports storage `enabled: false`, `driver: disabled`. No corrected deployment exists and no Vercel settings were changed.

The focused implementation and measured bottlenecks are detailed in [RELEASE_AUDIT.md](RELEASE_AUDIT.md); storage integration and the conformance boundary are detailed in [PRIVATE_STORAGE.md](PRIVATE_STORAGE.md). Final local verification is recorded below. No push, merge, deployment, infrastructure provisioning or project-setting change was performed. Public sample release and full hosted own-data release remain separate gates, both awaiting the required external verification.

## Correction scope and actual local evidence

Calculation-path changes preserve forecast values, selection rules, horizons, constraints, benchmark ordering and the accepted fallback policy: request-local fixed-origin weekday reuse and byte-equivalent unchanged-field input serialization, bounded pure date conversion, and indexed opposing-transfer lookup. Full independent replay remains separate. Default plan/review responses now project only the full stock table out of the initial payload; typed selected-SKU evidence validates current plan/review identities and matches full replay. Accepted snapshots/workbooks keep complete authoritative results. Optional bounded diagnostics and an additional compact/detail CI smoke complement the unchanged full-ledger assertions.

The provider-neutral private-storage composition adds sealed upload/finalization, integrity/ownership/expiry, quota reservations, atomic review replacement and durable cleanup metadata interfaces. Conformance doubles cover two-instance conflicts and the actual parser/planning/scenario/review/export/reopen flow. No authorized provider exists here; production factory, concrete blob/transaction providers, signed transport endpoints and real-provider conformance remain prerequisites. Hosted workflows stay disabled. Exact capabilities and configuration roles are in [PRIVATE_STORAGE.md](PRIVATE_STORAGE.md).

The offline evaluator now carries acquisition values for in-transit units and aggregates usable/blocked/reserved stock valuation correctly at the next origin, with daily value-conservation assertions. It retains received transfer IDs for pending payments and active-product dates. These evaluator fixes do not change runtime planning calculations. Repeated fixture/full evaluation still yields identical proposed and benchmark policies; no improvement or savings is claimed.

Changed file groups:

- `backend/app/forecasting/{engine,identity}.py`, `planning/{inputs,benchmark,engine,contracts,presentation}.py`, `simulation/replay.py`, `data/{sample,validation}.py`, `main.py`, new `diagnostics.py`: equivalent calculation optimization, timings and typed projection.
- `backend/app/data/{storage,private_storage,workflow_api}.py`, `backend/app/scenarios/contracts.py`: provider boundary, atomic replacement and exact evidence identity.
- `frontend/src/{PlanReview,ScenarioEvidence}.tsx`, generated contracts, `frontend/e2e/{planning,scenarios,pass5-state}.spec.ts`: live lazy evidence and preserved review/navigation regressions.
- New backend tests for diagnostics, equivalence, presentation and private storage plus provider harness; extended policy replay tests.
- `scripts/{planning_profile,planning_smoke,planning_transport_smoke,policy_replay,release_trace}.py`, `.github/workflows/verify.yml`: expanded measurements and verification while retaining existing gates.
- README, BUILD_STATUS, DEPLOYMENT, PLANNING, RELEASE_AUDIT and new PRIVATE_STORAGE documentation.

Environment: **macOS arm64, Python 3.14.4, temporary Node 24.21.0**, single-worker production Uvicorn on port **8020**, diagnostics enabled locally. Application Node 24 / Python 3.14 and dependencies are unchanged. Timing runs were serial. Ignored `artifacts/correction-final-*` logs, policy JSON and trace/browser artifacts hold local evidence. No Docker-compatible executable is installed; these results are not Linux/container results.

| Dataset / run | HTTP | Engine | Full response | Replay / finance / repeat |
|---|---:|---:|---:|---|
| Fixture first | 2.431 s | 2,405.5 ms | 786,692 bytes | Passed; reference |
| Fixture repeat | 2.397 s | 2,380.7 ms | 786,692 bytes | Passed; matched |
| Full first | 2.193 s | 2,094.2 ms | 3,753,093 bytes | Passed; reference |
| Full repeat | 2.104 s | 2,005.8 ms | 3,753,092 bytes | Passed; matched |

All four full-ledger requests pass the **unchanged 10-second gate**. Fixture retains 24 purchases / 311 movements and SAR 91,606 commitments / 97,746 payments; full retains 31 / 607 and SAR 92,550 / 99,050. All report honest `feasible_fallback`; fixture's two-second challenger times out, full's zero-budget challenger is not attempted, and validated benchmark actions are deterministic. Full retains 240 series / 16,800 stock rows. Default compact full HTTP is **2.102 / 2.042 s**, **1,022,713 / 1,022,712 bytes**, **72.75% less** than the approximately 3.75 MB baseline. Scoped detail is deterministic and exactly reconciles to full replay. These first/repeat labels follow forecast smoke and do not establish cold starts.

Local full profile route improved **3.994 / 3.257 → 2.824 / 2.042 s**; forecast **2.168 / 2.200 → 1.321 / 1.325 s**; benchmark **0.721 / 0.720 → 0.394 / 0.392 s**. Replay remains three independent calls. Sample construction/validation, buffer/protection, contract conversion, JSON, process imports and transfer timing are broken out in [RELEASE_AUDIT.md](RELEASE_AUDIT.md). Baseline Ubuntu and hosted measurements there are explicitly separated from corrected local results.

### Commands and results for this correction

The production commands below used `--url http://127.0.0.1:8020`; profiling and offline evaluation run in separate processes. All listed final HTTP/evaluation commands exited zero.

| Executed command | Actual result |
|---|---|
| `PLANNING_DIAGNOSTICS=1 PORT=8020 ./scripts/start.sh`; agent-browser verification | Production startup, real forecast, four navigation items, screenshot and error checks passed. |
| `.venv/bin/python -m scripts.smoke` | Built page/health and actual fixture/full forecasts passed. Fixture HTTP 0.039 / 0.031 s; full 0.193 / 0.169 s. Historical script “cold/warm” labels are not instance-cold evidence. |
| `.venv/bin/python -m scripts.planning_smoke` | All four complete-ledger requests above passed dimensions, replay, finances, determinism, 4.5 MB and 10-second gates. Only its endpoint query changed to `include_stock=true`; assertions are retained. |
| `.venv/bin/python -m scripts.planning_transport_smoke` | Fixture/full compact first/repeat matched complete policy actions/totals/explanations; scoped detail matched authoritative stock/cash/provenance and repeat content. Added alongside existing CI gates. |
| `.venv/bin/python -m scripts.planning_profile` | Fixture/full first/repeat passed; exact local components and response sizes in RELEASE_AUDIT. Fresh-process API import 0.212 s, optimizer import 0.232 s. |
| `.venv/bin/python -m scripts.scenario_smoke` | Fixture comparisons 2.651 / 2.527 s, full 3.244 / 3.117 s; full detail 1.993 s, future-path comparison 4.520 s. Independent feasibility, unavailable invalid-policy metrics, cash, hashes, determinism and existing 30-second / 4.5 MB gates passed. |
| `.venv/bin/python -m scripts.workflow_smoke` | Fixture/full real workbook upload, validation, provenance, review/regenerate/accept, complete XLSX/snapshot reconciliation, deterministic downloads, portable reopen and reset passed. Full HTTP and source/expanded-byte evidence retained in the log. |
| `.venv/bin/python -m scripts.release_trace --output artifacts/correction-trace-final.json` | Forecast/action/dated cash/scenario/review/export trace passed. Initial harness mismatch compared compact revised response against the complete accepted snapshot; explicitly requesting the complete revised ledger preserves the original equality assertion. |
| `.venv/bin/python -m scripts.policy_replay --size fixture --output ...` and `--size full`, each twice; byte comparison | All four passed, each size byte-identical. Proposed and benchmark actions identical; fixture fill 48.0418%, full 39.8934%. Unit/transit/acquisition-value and dated funding reconciliation passed. |

| Executed command | Actual result |
|---|---|
| `PORT=8020 CHROME_PATH=... npm --prefix frontend run test:e2e` with Node 24.21.0 | **26 passed in 2.9 min** in the final complete serial run. The focused evidence/recovery regression also passed (11.1 s including startup). |
| `.venv/bin/python -m scripts.export_contracts`; `npm --prefix frontend run generate:types` | Passed; re-export/regeneration preserves SHA-256 exactly: OpenAPI `99245e855a4a04635abb9fc939d258173811208e8522302b13815a7733d960e3`, TypeScript `59ad465e0ddc981284e1b08044476a69e03fe304ed8cfbfbc90388d06f6316df`. Generated types intentionally differ from baseline for the new typed projection/evidence fields and query parameters. |
| `npm --prefix frontend run build` under Node 24.21.0 | TypeScript and production Vite build passed; 41 modules, JS 304.94 kB / 91.82 kB gzip, CSS 13.52 kB / 3.84 kB gzip, Vite 396 ms. |
| `.venv/bin/python -m pip check`; `npm --prefix frontend ls --depth=0` | No broken Python requirements; installed frontend dependency tree passed. No dependency upgrades. |
| `.venv/bin/python -m compileall -q backend scripts`; `git diff --check` | Passed. |
| Ruby YAML parse plus required planning/compact smoke and no failure-suppression assertions | Passed. Docker/Podman/Colima/Lima absent; corrected container build/start/smokes could not run locally. |

Earlier browser runs exposed two outdated harness assumptions: initial sample evidence now follows the exact private review reference locally, and stale review details are rejected until regeneration. The tests now wait for that authoritative endpoint and establish a current draft before exercising the existing held-response navigation guard. No assertion or timeout was relaxed. Intermediate suites were 24 passed / 2 failed; a subsequent interrupted focused run and retry against its long-lived server were not accepted as verification. The server log showed its temporary session directory was missing after the interruption; a fresh server rendered correctly, the focused regression passed, and all 26 tests then passed. A transient scenario baseline wait also passed on recheck and in the final suite without weakening its assertions.

Final `.venv/bin/python -m pytest -q`: **197 passed in 329.24 s**, with two existing Starlette/httpx/AnyIO deprecation warnings and no failures. This includes the complete original suite plus full-precision equivalence, input-identity mutation isolation, compact/detail equivalence, stale-reference rejection, diagnostics and private-provider conformance. Earlier complete suite was 194 passed (336.98 s); added cases are included in the final 197-test run.

The final explicit `.venv/bin/python -m pytest -q backend/tests/test_policy_replay.py` passed **7 tests**. `.venv/bin/python -m scripts.solver_smoke` passed SciPy 1.18.1 import and both cold/warm HiGHS checks with status 0 and expected x=2. These local checks do not substitute for the required container solver gate.

### Release verdict

**Local sample runtime passes. Pass 6 cannot close.** Corrected-commit GitHub Actions including Docker has not run, and corrected canonical hosted runtime/browser verification has not occurred. A separately authorized deployment must pass two serial full requests under ten seconds and the preserved sample gates. Full hosted own-data additionally requires authorized private persistent objects and transactional metadata, concrete integration and real-provider lifecycle/isolation/upload-through-reopen verification. No provider, credentials, paid resource, deployment or project configuration was created or modified.

---

# Build status

## Pass 6 final audit and release boundary — 19–20 September 2026

Started from a clean worktree at **599554c3ad4e44c47b0461eff3fac921318ea606**. Read the build specification, planning/deployment documentation, README, verification workflow and smoke scripts; no applicable repository AGENTS instructions were found. Preserved the existing application, sample dimensions, forecasting/selection logic, planning objectives, 56/28/7-day windows, two-second fixture challenger, full-sample fallback policy, hard constraints, contracts and runtime gates. No dependency, infrastructure or deployment configuration changed; no push, merge or deployment occurred.

**Exact baseline CI:** [run 35461717511](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35461717511), job **105946650205**, was initially pending and subsequently **completed successfully**. Downloaded job logs verify Ubuntu 24.04.5, **168 backend tests in 649.53 s**, **26 browser tests in 5.8 min**, solver smokes, reproducible contracts/build, Docker build/start, forecast/planning/scenario smokes, container profile and local-storage upload/review/accept/export/reopen. Fixture planning **3.534 / 3.560 s**; full **9.179 / 9.268 s**. **Pass 5 is now closed for 599554c.** This does not certify the new Pass 6 changes.

### Findings and bounded changes

- **Minor presentation defect, corrected:** actual hosted purchase evidence displayed `20.400000000000006 units`. `evidenceTarget.ts` now uses the existing one-decimal quantity formatter for both shortage and replenishment-need evidence. API precision and calculation results are unchanged. The browser regression checks the actual fixture evidence against the formatted API quantity.
- **Missing release evidence, completed locally:** added offline weekly realized-policy evaluation and five regression tests. The evaluator runs the existing planner with origin-known inputs; future truth is consumed only after actions are fixed. It carries realized censored sales, stock/transit, received IDs and outstanding payments. Full and fixture reports were each run twice and matched byte-for-byte. Both policies produced identical releases. Fixture realized fill **48.0418%**, unmet **9,154**; full fill **39.8934%**, unmet **62,717**. Funding and stock conservation passed; no improvement/savings claim is supported. Exact simulation/calendar assumptions, per-policy spending, inventory and reproduction commands are in [RELEASE_AUDIT.md](RELEASE_AUDIT.md).
- **End-to-end trace, completed:** new `scripts/release_trace.py` verifies real HTTP forecast, purchase, store transfer, dated deposit/balance, valid original/frozen/replanned deltas and local 130→120 quantity regeneration/acceptance/XLSX/snapshot reconciliation. Hosted trace independently passed sample arithmetic and the payment-ceiling control, and explicitly reported storage disabled. Initial audit-harness failures exposed required received-ID/empty-table carry-forward and the existing XLSX lossless-text numeric convention; the harness was corrected and rerun, with no production-contract workaround.
- **Hosted runtime blocker, unresolved:** canonical Vercel full-sample planning took **17.022 / 14.929 s**, engine **11,775.5 / 11,949.9 ms**, exceeding the retained **10-second** HTTP gate. All four sample responses passed replay, money, dimensions, payload and deterministic actions/totals/explanations. Full has no joint solve; baseline container profiling isolates ~6.27 s forecast preparation and ~2.15 s benchmark work, with a fresh-process route above 11.6 s. Hosted per-stage/cold-instance/memory profiling and a focused performance correction remain required. No thresholds, dimensions, objectives or solver policy were changed to turn the result green.
- **Hosted own-data blocker, unresolved:** actual hosted session reports `enabled: false`. Only `LocalStorage` exists and is intentionally disabled on Vercel. Existing provider-neutral interfaces remain; the audit specifies private direct upload/finalization/download, server ownership/content/size/expiry validation, atomic revision storage and lifecycle/isolation tests needed for an authorized adapter. No provider/resource was configured or provisioned, and no public-file/browser-Dataset/serverless-temp workaround was introduced.

### Commands and actual results

Local environment: macOS arm64, existing Python 3.14.4 / Node 25.6.1 environment, production Uvicorn single worker. Configured application Node 24 / Python 3.14 are unchanged. Port **8012** was used for dedicated production HTTP checks, while the browser suite used its normal production server on **8000**. Log/JSON/screenshot artifacts are ignored local evidence in `artifacts/pass6-*`; reproducible scripts and summarized findings are prepared for review.

Changed files: `frontend/src/evidenceTarget.ts`, `frontend/e2e/scenarios.spec.ts`, new `backend/tests/test_policy_replay.py`, new `scripts/{policy_replay.py,release_trace.py,hosted_browser.mjs}`, `README.md`, this status, `docs/DEPLOYMENT.md` and new `docs/RELEASE_AUDIT.md`. The hosted browser script is an explicit-URL verification harness; it does not deploy, upload own data or alter project settings.

| Executed check | Actual result |
|---|---|
| `.venv/bin/python -m pytest -q` | Baseline **168 passed**, two existing deprecation warnings, **284.24 s**. Final suite with new evaluator tests **173 passed**, same warnings, **328.71 s**. |
| `.venv/bin/python -m pytest -q backend/tests/test_policy_replay.py` | **5 passed in 0.34 s**; hand arithmetic, truth boundary, censoring, installments/received IDs, transfer guard and missing-oracle failure. |
| `.venv/bin/python -m scripts.solver_smoke` | SciPy 1.18.1 import **0.311 s**; cold/warm HiGHS status 0, expected x=2. |
| `.venv/bin/python -m scripts.export_contracts`; `npm --prefix frontend run generate:types`; `git diff --exit-code -- artifacts/openapi.json frontend/src/contracts.generated.ts` | Passed; contracts and generated types unchanged. |
| `npm --prefix frontend run build` | Passed before and after the correction. Final 41 modules; JS **305.84 kB / 91.84 kB gzip**, CSS **13.52 kB / 3.85 kB gzip**; final Vite **523 ms**. |
| `CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e` | Initial **26 passed in 3.3 min**. Focused evidence regression **1 passed in 23.9 s**. A concurrent-work rerun timed out in scenario-derived review regeneration and subsequent initial forecast (24 passed / 2 failed); both passed a serial recheck (**20.3 s**) without changing gates. Final full serial run **26 passed in 3.1 min**. No test timeout/assertion was weakened. |
| `PORT=8012 ./scripts/start.sh` plus agent-browser | Production startup passed; rendered forecast and navigation verified, screenshot inspected, no reported page errors. Local loopback/browser access required the execution environment's sandbox escalation. |
| `.venv/bin/python -m scripts.smoke --url http://127.0.0.1:8012` | Passed built index/health and fixture/full real forecasts. Fixture first/repeat **0.033 / 0.033 s**; full **0.940 / 0.172 s**. Script's historical `cold/warm` labels are process-order labels, not proof of cold instances. |
| `.venv/bin/python -m scripts.planning_smoke --url http://127.0.0.1:8012` | Passed all four: fixture **2.739 / 2.549 s**, full **3.273 / 3.255 s**. Largest **3,753,044 bytes**; complete dimensions, independent replay, reconciled cash/commitments, repeat actions/totals/explanations and 10-second gate all passed. |
| `.venv/bin/python -m scripts.scenario_smoke --url http://127.0.0.1:8012` | Passed. Fixture comparisons **2.697 / 2.679 s**, full **4.327 / 4.306 s**. Full detail **2.879 s**; future-path comparison **6.626 s**. Determinism, reconciliation, 30-second and 4.5 MB gates preserved. |
| `.venv/bin/python -m scripts.workflow_smoke --url http://127.0.0.1:8012` | Fixture/full upload, authoritative provenance despite wrong client size, review/regeneration, acceptance, workbook/snapshot, deterministic downloads, unique IDs, read-only reopen and reset passed. Fixture upload/plan/regenerate/accept/export **1.397 / 2.762 / 2.777 / 0.854 / 0.113 s**; full **10.797 / 5.790 / 6.169 / 6.810 / 0.863 s**. |
| `.venv/bin/python -m scripts.planning_profile` | Passed fixture/full first/repeat with deterministic validated results. Local full route **5.157 / 4.146 s**, serialization **0.014 / 0.014 s**; this run overlapped other local work and is not a latency gate or Docker measurement. Separate exact-baseline CI profile is retained in RELEASE_AUDIT. |
| `.venv/bin/python -m scripts.policy_replay --size fixture/full --output artifacts/pass6-policy-*.json`, repeated with `-repeat.json`; `cmp` | All four reports completed; byte-identical first/repeat for each dataset. Fixed seed, four origins, full dimensions, separate withheld truth, funding and conservation checks passed. |
| `.venv/bin/python -m scripts.release_trace --url http://127.0.0.1:8012 --output artifacts/pass6-local-trace.json` | Passed forecast/action/cash/scenario/review/export trace. Edited line 120 units / SAR 1,320; revised commitments **91,496**, payments **97,696**; XLSX and portable snapshot agree. |
| `.venv/bin/python -m pip check`; `npm --prefix frontend audit --omit=dev --json` | No broken Python requirements; **zero reported production npm vulnerabilities**. No dependency upgrades. Pip cache unavailable in sandbox, check still passed. |
| `.venv/bin/python -m compileall -q backend scripts`; `git diff --check` | Passed; final checks rerun after documentation. |
| Docker / Podman / Colima / Lima availability | No compatible executable installed. No local container build/start claimed. Baseline CI completed Docker checks; new Pass 6 commit/container CI remains outstanding. |

### Hosted evidence and remaining release actions

Canonical **https://demand-supply-planning-intelligence.vercel.app**, production deployment **dpl_FDjfTcpkSijxKDgpnJRHf5owkojH**, region **iad1**, verified deployed revision **599554c**. Read-only Vercel metadata and GitHub job/log tools were used; no external state was changed. Deployment build success was not used as runtime proof.

- Hosted forecast smoke passed fixture **0.687 / 0.636 s**, full **5.244 / 1.135 s**. Hosted planning fixture **8.230 / 5.473 s**, full **17.022 / 14.929 s**; planning script correctly exited nonzero for both full runtimes. All four payloads/replays/reconciliations/repeats passed.
- An overlapping scenario run failed with the explicit busy **429**. A serial rerun passed fixture/full scenario checks, unchanged 30-second/4.5 MB gates, original/frozen/replanned hashes, financial totals and repeat determinism. Full comparison **20.283 / 18.141 s**, largest **921,568 bytes**; scoped detail **12.395 s / 113,556 bytes**; future-path delay **27.489 s / 1,035,200 bytes**. Hosted release trace separately verified commitment and payment ceilings and valid +50-visible-unit replan delta at **6.137 s / 348,988 bytes**.
- Actual hosted session capability check: private workflows disabled. Vercel runtime-error lookup returned no clusters in the selected preceding hour; peak memory, complete log coverage and genuine instance-cold startup remain unverified. First/repeat request order is not a cold-start guarantee.
- **Final hosted browser verification passed:** `CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' node scripts/hosted_browser.mjs https://demand-supply-planning-intelligence.vercel.app`. Verified desktop Demand/Plan Review, full forecast product/store/recalculation, actual store-transfer/forecast evidence, 390px mobile layout, all four scenario controls in a live combined run, reset, disabled own-data upload, blank template download and active Data navigation. All 22 observed same-domain API responses were 200; page/console errors were empty. Screenshots inspected. Earlier agent-browser sessions lost their page to `about:blank`; the single-session harness also needed selector/dated-funding-row corrections before passing. Those were audit-harness issues, not evidence that failed attempts passed. The final script keys normalized funding assertions by date, not array position. This verifies the deployed baseline only; the local quantity-format correction is not yet hosted.

Detailed calculation traces, offline policy results/assumptions, hosted timings, private-adapter implementation checklist, three-minute demo, portfolio copy and synthetic-data/solver/savings disclosures: **[RELEASE_AUDIT.md](RELEASE_AUDIT.md)**. README links to the verified public sample with the runtime caveat; DEPLOYMENT distinguishes successful baseline CI from hosted runtime and unavailable private storage.

**Verdict:** Pass 5 closed for 599554c; Pass 6 release audit **blocked at hosted gates**; public sample is functional but **not ready against its 10-second gate**; full hosted own-data **blocked**. Remaining actions: targeted full forecast/preparation profiling and correction, true hosted cold/memory measurement; authorized private adapter plus isolation/lifecycle/direct-transport and full workflow checks; review/commit these changes and obtain exact-commit CI; separately authorize deployment and repeat hosted verification of that new SHA. Do not mark the complete release ready before those gates pass. No new product features or later scope began.

## Final Pass 5 mutation-transaction correction — 19 September 2026

Started from clean GitHub main commit **8e8f8973c03a6005ced05a2ab0fd33ac5e5eb366**. This correction changes frontend transaction state and browser regressions only. Forecasting, planning, replay, scenarios, storage, API contracts, dependencies, deployment configuration and Pass 6 scope are unchanged.

### Root cause and corrected lifecycle

The previous correction locked sidebar and brand navigation while a review mutation POST was unresolved, but several controls inside Plan Review were outside that lock: scenario-derived return, evidence-to-Demand navigation, the planning dataset selector and plan recalculation. `ReviewControls` aborts its active operation when Plan Review unmounts. Those controls could therefore remove the component after the server saved a replacement but before the browser received and recorded its new reference.

One App-owned `ReviewMutationPhase` now represents the protected transaction: `idle` or `awaiting-response`. `ReviewControls` enters `awaiting-response` before every mutation POST. For regeneration/new-draft it publishes the replacement reference, operation and complete review metadata to App recovery before returning to `idle`; for other mutations it publishes the returned plan reference before returning to `idle`. The subsequent replacement-plan GET is deliberately outside the global lock. If it fails or is interrupted, old quantities stay blocked and the saved replacement remains available through **Load regenerated result**.

The shared phase now guards both rendering and handlers for sidebar navigation, brand navigation, direct scenario handoff, scenario-derived return, evidence forecast navigation, planning dataset changes, plan recalculation/retry, sample dataset replacement/reset/reopen, linked-forecast navigation and scenario-to-review entry. The scenario-derived marker also follows the saved recovery reference while the displayed old plan still has its previous reference, so explicit abandon remains available after the POST is safely recorded. The existing **Saving review mutation…** status is shown in Review Controls and the sidebar until that boundary.

### Regression and verification results

- New delayed-response Playwright regressions hold real mutation responses after the server has completed them. They force-enable disabled controls and invoke their handlers, then assert that Plan Review remains mounted, the request is not aborted, no replacement calculation starts and the returned reference becomes authoritative.
- Scenario-derived regeneration: return remained blocked through the POST, the displayed run stayed mounted, the replacement GET used the returned reference, failed delivery remained recoverable, and explicit return worked after the reference was recorded.
- Evidence navigation: Demand Review navigation was blocked through the POST and worked after recovery was recorded; returning to Plan Review exposed the saved result loader.
- First review mutation: the initially enabled planning dataset and recalculation controls became locked; forced change/click callbacks produced no second `/api/plan/sample` request, and review metadata reloaded from the returned reference.
- Focused new regressions: **3 passed in 25.2 s**. Existing failed-delivery recovery regression: **1 passed in 8.0 s**. Complete Playwright suite: **26 passed in 3.1 min**.
- Final `npm --prefix frontend run build`: passed TypeScript and Vite production compilation, **41 modules**, JS **305.83 kB / 91.84 kB gzip**, CSS **13.52 kB / 3.85 kB gzip**.
- `.venv/bin/python -m scripts.export_contracts` and `npm --prefix frontend run generate:types` passed; `git diff --exit-code -- artifacts/openapi.json frontend/src/contracts.generated.ts` confirmed both committed contracts are unchanged.
- Final callback audit used repository-wide searches for screen, dataset, refresh, evidence and workflow callbacks. `git diff --check` passed. No backend or shared contract source changed, so backend tests were not rerun for this frontend-only correction.

Changed files: `frontend/src/{App,PlanReview,ReviewControls,ScenarioEvidence}.tsx`, `frontend/src/reviewState.ts`, `frontend/e2e/pass5-state.spec.ts`, and this status file.

Local implementation and verification are complete. **Pass 5 is not yet formally closed** because the exact corrected worktree has not been committed and therefore has no exact-commit GitHub Actions run. CI/container and hosted evidence remain pending. No push, merge, deployment or Pass 6 work occurred.

## Focused Pass 5 reviewed-baseline and recovery correction — 19 September 2026

Started from reviewed commit **4b7e53024f9f938aa90130c35831a923f31d8b10** and preserved the completed Pass 5 UI, accessibility, provenance, financial labeling and failure handling. No forecasting, optimizer, replay, horizon, sample dimension, API contract, dependency, infrastructure or deployment behavior changed. No Pass 6 work began.

### Reproduction and root cause

The reviewed-plan handoff was reproduced in the live application: after a full-sample plan was reviewed and regenerated, opening scenarios issued `POST /api/scenarios/baseline` with `{"size":"fixture"}`. `App.tsx` passed `initial={openedPlan ? null : planContext}`, so the presence of the reviewed plan deliberately removed the exact plan from the scenario capture path. The scenario screen then initialized its own fixture default. This could silently discard reviewed actions and authoritative bundled size.

The recovery gap came from keeping the replacement review reference only in `ReviewControls.pendingPlan`. A successful `regenerate` or `new-draft` mutation invalidates the previous reference before the follow-up result GET. If delivery failed and navigation unmounted the component, the only valid reference disappeared while the parent retained the invalid prior plan. During the correction, a second race was exposed by the new full-sample regression: publishing parent recovery state reran the review-loader effect, whose shared abort controller cancelled its own follow-up result GET. Review metadata loading and mutation/result delivery now have separate controllers.

### Corrected state transitions

- `App.tsx` owns the current exact plan context, review gate and replacement recovery record. A successful mutation publishes the new reference, revision and review state before result delivery. Navigation is disabled only while the mutation response itself is unresolved; once its reference is recorded, users may leave and return safely.
- Until the matching result loads, displayed quantities remain explicitly previous/stale. Acceptance, exports, direct scenario handoff and sidebar scenario entry remain blocked. Returning to Plan Review restores the replacement metadata and **Load regenerated result** fetches the saved calculation without another mutation. The same transition applies to explicit new-draft creation.
- Dataset replacement/reset clears plan, scenario and recovery state. Component aborts and generation boundaries prevent a late result from restoring abandoned state. Data reconciliation uses the replacement reference while recovery is pending.
- Scenario capture receives the exact independently replayed current plan and uses canonical `provenance.sample_size`: `full` remains full; uploaded and portable data send `size: null` and retain their private dataset reference, hash and dimensions. Capture payload purchases/movements are the displayed reviewed actions, and scenario exploration does not mutate the source plan.
- Stale, loading and failed-delivery plans cannot enter scenarios through either button. The capture component also rejects a supplied plan whose input hash is not the canonical dataset hash or whose replay is invalid.
- Scenario-derived reviewed plans are explicit. The existing capture contract cannot encode their scenario definition, so both handoff routes are disabled with an explanation and a **Return to original scenario baseline** action. Returning recaptures the untouched original actions; assumptions are neither dropped nor applied twice.

Changed files: `frontend/src/{App,PlanReview,ReviewControls,Scenarios}.tsx`, new `frontend/src/reviewState.ts`, `frontend/e2e/{product-finish,workflow}.spec.ts`, new `frontend/e2e/pass5-state.spec.ts`, and this status file. No backend, generated contract, lockfile, deployment or workflow file changed.

### Local verification

Local verification used macOS arm64, the existing Python 3.14 environment, the compiled frontend and one production Uvicorn worker. Exact-commit CI, Docker and hosted verification remain outstanding.

- Pre-fix production build passed while reproducing the defect. Final `npm --prefix frontend run build`: passed, **41 modules**, JS **305.42 kB / 91.75 kB gzip**, CSS **13.52 kB / 3.85 kB gzip**.
- Targeted Playwright: the three new plan-state regressions passed in **36.6 s**; regeneration and new-draft recovery tests passed **2 tests in 30.7 s**. The complete suite passed **23 tests in 2.7 min**.
- Browser regressions assert the actual capture payload and response actions for a reviewed full sample, a material valid quantity edit, uploaded and portable provenance/hash/dimensions, stale direct/sidebar blocking, scenario-derived return, failed result delivery across navigation, no duplicate regeneration/new-draft, current review locks, and dataset reset during a delayed obsolete delivery.
- Installed `agent-browser` opened the compiled application successfully; the interactive snapshot showed the API-backed demand result and all navigation, and page/console error checks were empty.
- Contract export and TypeScript generation ran twice. Both runs were byte-identical: OpenAPI SHA-256 `75cc199a8b3be096053a57878249e06ba2713f984b1b938dd6b2f8179bb018d5`; generated TypeScript `543eab94db5801ed2f23f3c29cba86a55e87ce71a3dbee66843332986f779616`. There is no generated-contract diff.
- Production scenario smoke passed independent feasibility, financial reconciliation, scoped evidence and repeat determinism. Fixture comparison first/repeat: **2.697 / 2.671 s**, **366,155 / 366,157 bytes**. Full: **4.325 / 4.364 s**, **921,567 bytes**. Future-path comparison: fixture **3.006 s / 362,703 bytes**, full **6.540 s / 1,035,199 bytes**.
- Production workflow smoke passed fixture and full upload, review, regeneration, acceptance, export and portable reopen with independent replay, financial reconciliation, unique external IDs, deterministic snapshot downloads and final private-session reset. Fixture upload/plan/regenerate/accept/export: **1.453 / 2.752 / 2.803 / 0.837 / 0.122 s**; full: **9.039 / 4.496 / 4.800 / 5.149 / 0.616 s**. Provenance remained uploaded through acceptance/export and portable after reopen, with exact hashes and dimensions.
- `git diff --check` passed before documentation and is rerun as the final worktree check. Backend source did not change, so the complete backend suite was not rerun for this frontend state correction, as directed by the correction scope.

**Pass 5 is ready for review locally.** The remaining limits are unchanged: recovery is intentionally in-memory and bound to the existing private session lifetime; scenario-derived plans must return to the original baseline because the current contract does not preserve a scenario definition in baseline capture; and no exact-commit CI/container or hosted success is claimed. No push, merge or deployment occurred.

## Pass 5 — product finish and scope freeze — 19 September 2026

Started from clean reviewed baseline **218db764b9e6addb8e87da9b8d829e584796b19f**; no reset or unrelated changes. User-confirmed GitHub Actions **35364586310** succeeded for that Pass 4 commit, including backend/browser tests, contracts/build, Docker verification, forecast/planning/scenario smoke, container profiling and upload/review/accept/export/reopen. This supersedes the historical pending-CI statements for that baseline only. No GitHub Actions run or hosted success is claimed for Pass 5.

### Observed gaps and corrections

Real browser inspection at **1440, 768 and 390 px** found a clipped fourth navigation item on mobile, hidden planning dates, raw/cramped review fields, missing evidence focus entry/return, no clear stale banner after review edits, and limited network/session-error recovery. Long-name screenshot inspection also found desktop Product collapse despite no document overflow. Corrections use the existing colors, typography, panels and dependencies:

- Responsive two-column navigation keeps all screens visible; decorative numbers no longer pollute accessible button names. Planning dates remain visible. Bounded selectors tolerate long names, review fields adapt to one column, amounts align right, long evidence wraps, and dense tables remain keyboard-focusable local scroll regions.
- Evidence panels take focus, close with Escape and return focus to the opener. They are inline regions, not modal dialogs. Retry is available for failed evidence and review loads. Inputs have visible focus; busy review/upload/calculation states use status announcements.
- Current dataset, source and planning date are explicit, including portable sources. Financial copy distinguishes commitment authority, payments, existing obligations, movement funding, inventory cost and visible/provisional windows. Scenarios describe original/frozen/replanned policies and identical changed assumptions; supplier selections include names. Fallbacks remain **Validated constrained plan**, with shortages and technical stage evidence retained.
- Review mutation visibly marks prior quantities stale and blocks scenario handoff/acceptance/export. A successful regeneration whose result GET fails remains stale and offers **Load regenerated result**; acceptance stays blocked until that result loads. Duplicate review/upload submits are guarded. Review requests abort on unmount; retry loops retain their original dataset reference. Portable reopening loads its catalog and plan before committing the active source, and cancels on replacement/navigation. Obsolete reset/upload responses cannot replace current state.
- Shared API errors retain stable codes, review conflicts and FastAPI field details, with network/expiry recovery instructions. Workbook sheet errors remain grouped without duplicate alert text. Failed acceptance never exposes new download links. Hosted storage remains disabled, with local/Docker and session-recovery instructions.

Changed files: `frontend/src/{App,DataWorkspace,Demand,Evaluation,PlanReview,ReviewControls,ScenarioEvidence,Scenarios}.tsx`, `frontend/src/{api,scenarioApi,errors}.ts`, `frontend/src/styles.css`, `frontend/e2e/{product-finish,workflow}.spec.ts`, `README.md`, `docs/DEPLOYMENT.md`, and this status file. No backend, generated contract, lockfile, infrastructure or deployment configuration changed.

### Verification

Local verification uses macOS arm64, the existing Python 3.14 environment and one production Uvicorn worker (`./scripts/start.sh`) serving the compiled frontend. Measurements below are local; sample input caches can be warm. No plan responses are cached.

- `.venv/bin/python -m pytest -q > artifacts/pass5-backend.log 2>&1`: **168 passed, 2 existing TestClient deprecation warnings, 274.36 s**.
- `.venv/bin/python -m scripts.solver_smoke`: SciPy 1.18.1 import **0.339 s**, HiGHS status 0 / integer x=2; cold **0.001 s**, warm **<0.001 s**.
- `.venv/bin/python -m scripts.export_contracts` and `npm --prefix frontend run generate:types` ran twice. SHA-256 comparisons matched both OpenAPI and TypeScript byte-for-byte. `git diff --exit-code -- frontend/src/contracts.generated.ts` passed.
- `npm --prefix frontend run build`: passed, **41 modules**, JS **301.85 kB / 90.44 kB gzip**, CSS **13.52 kB / 3.85 kB gzip**.
- `.venv/bin/python -m pip check`: no broken requirements; `npm --prefix frontend ls --depth=0`: installed tree resolved. No dependency upgrades or external vulnerability-audit claim. `.venv/bin/python -m compileall -q backend scripts` and `git diff --check` passed.

- Production commands ran sequentially with output retained in ignored `artifacts/pass5-*.log`: `.venv/bin/python -m scripts.smoke`, `.venv/bin/python -m scripts.planning_smoke`, `.venv/bin/python -m scripts.scenario_smoke`, `.venv/bin/python -m scripts.planning_profile`, and `.venv/bin/python -m scripts.workflow_smoke`.
- Forecast smoke passed: fixture **0.041 / 0.033 s**, full **0.178 / 0.166 s**. Its historical “cold” labels identify first requests in that smoke, not a cold application process here.

| Planning request | HTTP seconds | Engine ms | Response bytes | Purchases / movements |
|---|---:|---:|---:|---:|
| Fixture first | 2.541 | 2515.5 | 786,641 | 24 / 311 |
| Fixture repeat | 2.598 | 2580.1 | 786,644 | 24 / 311 |
| Full first | 3.437 | 3329.1 | 3,753,043 | 31 / 607 |
| Full repeat | 3.349 | 3251.1 | 3,753,044 | 31 / 607 |

All four planning requests passed: `feasible_fallback`, independent replay true/no failures, repeat actions/totals/ledgers/explanations matched. Fixture retained 40 series / 2,800 stock rows and the two-second `visible_must_stock:time_limit` challenger; full retained 240 series / 16,800 rows and `joint_model:not_attempted` with zero joint sub-budget. Both used `independent_fallback:benchmark`. Fixture commitment/payment lines reconcile exactly to **SAR 91,606 / 97,746**; full to **SAR 92,550 / 99,050**. Minimum commitment/payment/transfer headroom: fixture **0 / 14 / 120 SAR**, full **40 / 5 / 120 SAR**. The **10-second** planning and **4,500,000-byte** response gates remain unchanged.

Scenario smoke passed with independent feasibility, financial reconciliation, scoped evidence and repeat determinism. Fixture combined comparison first/repeat **2.753 / 2.682 s**, **366,155 / 366,157 bytes**; full **4.542 / 4.562 s**, **921,567 bytes**. Scoped detail: fixture **0.483 s / 114,868 bytes**, full **3.012 s / 113,556 bytes**. Future-path comparison: fixture **3.753 s / 362,703 bytes**, full **6.574 s / 1,035,199 bytes**. The 30-second scenario and payload gates are unchanged.

Profiler passed the production-route validation/determinism gates. Fixture route first/repeat **2.632 / 2.512 s**, serialization **0.0023 / 0.0023 s**, **786,641 / 786,644 bytes**. Full route **4.006 / 3.183 s**, serialization **0.0114 / 0.0111 s**, **3,753,044 bytes**. Full first/repeat phase seconds: sample input **0.802 / <0.001**, forecast **2.148 / 2.165**, benchmark **0.704 / 0.689**, replay **0.127 / 0.104**, explanations **0.034 / 0.033**; no joint model was attempted. Fixture joint total **2.036 / 2.037 s**, construction **0.039 / 0.051 s**, matrix preparation **0.013 / 0.013 s**, SciPy solve **1.984 / 1.973 s**. These retain existing instrumentation and overlap conventions; no performance policy changed.

Upload/review/regenerate/accept/export/reopen smoke passed for both dimensions, including deliberately wrong client sample labels. Provenance remained uploaded through regeneration/evidence/acceptance/download, then portable on reopen, retaining each exact dataset hash/dimensions. Independent replay, reconciliation, unique external IDs, deterministic repeated snapshot bytes and private-session reset passed.

| Workflow measure | Fixture | Full |
|---|---:|---:|
| XLSX / expanded bytes | 445,292 / 5,814,190 | 2,775,269 / 37,978,053 |
| Parse/validate ms | 1,267.52 | 8,483.84 |
| Upload HTTP s | 1.410 | 9.086 |
| Plan / regenerate HTTP s | 2.704 / 2.748 | 4.424 / 4.732 |
| Accept / export HTTP s | 0.829 / 0.111 | 5.074 / 0.602 |
| Reviewed XLSX bytes | 53,038 | 125,271 |
| Snapshot compressed / expanded bytes | 172,709 / 3,498,313 | 932,837 / 21,292,412 |

Browser verification:

- Focused `npm --prefix frontend run test:e2e -- product-finish.spec.ts`: **7 passed in 48.8 s** after fixing test selectors. Full final command: `CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' caffeinate -i npm --prefix frontend run test:e2e > artifacts/pass5-browser.log 2>&1`: **20 passed in 2.2 min**. `caffeinate` only prevented idle sleep for that local command; it changed no app/test/runtime setting.
- Coverage includes mobile API-backed sample review, keyboard action/evidence entry and Escape/focus return, arrow-key table scrolling, all three responsive widths with long names and usable selector widths, structured runtime/solver/field/expiry/network errors followed by retry, 429 admission retry, failed result delivery after successful regeneration, stale/export blocking, failed shortage acknowledgement and provenance acceptance, hosted-storage-disabled capability injection, and portable reopen → immutable view → explicit new draft → regeneration. Existing in-flight scenario/dataset/upload cancellation, forecast rounding and exact action-lock/provenance cases remain.
- Early test runs identified and corrected a strict date locator, decorative navigation-number naming, an exact-label selector that included option text, and duplicated workbook-error text. Subsequent bundled headless Chromium runs had intermittent response-event/transport waits in different tests. In the retained scenario trace, the UI had rendered the new comparison but Playwright recorded the request with no response event; another upload timeout snapshot already showed Validation passed. Idle-sleep prevention alone did not resolve this. No application cause was established, and no timeout/assertion was weakened. The repository-documented installed Chrome option passed the complete unchanged suite. Retained local trace: ignored `artifacts/pass5-browser-event-failure.zip`; confirm the default Linux browser in exact-commit CI.
- Inspected before/after desktop, tablet and mobile screenshots. Final screenshots in ignored `artifacts/pass5-{demand,scenarios,data}-{1440,768,390}.png` and `pass5-mobile-review.png` show readable active navigation/context and locally scrolling tables. Normal responsive workflows asserted no page/console errors or HTTP error responses. Deliberately injected failures are separate negative checks. The initial agent-browser console/page-error checks were empty; a later CLI selector attempt failed to navigate, so final review-control screenshots used Playwright with installed Chrome instead. Inspected `artifacts/pass5-review-{1440,768,390}.png`; the additional live browser check passed with no document overflow, page/console errors or HTTP errors.

**Pass 5 is ready for review locally, with feature scope frozen.** Exact-commit CI/container and hosted release verification remain outstanding; the bundled local browser event issue is recorded above rather than presented as a clean default-browser run.

### Operator demo

The approximately three-minute sequence is in [README.md](../README.md#three-minute-operator-demo). Live sample fixture `sample-v1-fixture-97`, as-of **2026-09-14**, produced SKU001/S1 **281.1** visible units, displayed MAE **10.4 → 7.5 / 28%**, **<0.1%** pooled signed bias and **223/224** scored observations. Purchase `P-OFFER008-0` proposes **130 SKU008 units / SAR 1,430**, ordered/dispatched 14 September, arriving 28 September, with **SAR 715** deposit 14 September and **SAR 715** balance 28 October. Visible fill **52.7%**, unmet **7,567.4**, inventory value **SAR 18,303.42**; SKU008/DC→S1 on 14 September has a shared-stock limit of **10** pack-rounded units against **150** requested.

The live Promotion preset (+30% SKU001, all stores, 14–27 September) made frozen actions infeasible; its metrics/deltas correctly remained unavailable. Replanning passed at **52.2% fill**, **7,742.8 unmet**, **SAR 91,726 commitments / 97,746 payments**. The demo makes no savings comparison against the infeasible frozen policy. It concludes with a valid quantity edit, stale-state/regeneration, shortage acknowledgement, acceptance, both downloads, read-only portable reopen and explicit new draft in the supported local environment. Actual data is retained in ignored `artifacts/pass5-demo.json`; no outcome was embedded into application code.

### Scope freeze and bounded Pass 6 handoff

Feature scope is frozen around the four existing screens and the required local sample/upload/review/scenario/accept/export/reopen workflow. Forecast selection/rounding, service priorities, constraints, independent replay, exact review decisions, provenance, snapshot integrity, execution reconciliation, dimensions/horizons, solver budgets and payload/runtime gates are unchanged. No model correction was needed.

No Docker, Podman, Colima or Lima executable is installed here: new container build/start, container solver/profile and workflow checks remain for exact-commit CI. Hosted private storage is a **Pass 6 release dependency**, not a completed feature. No storage was provisioned, Vercel setting changed, project removed, push/merge/deployment made, or Pass 6 implemented.

Pass 6 starts with specification and input-to-result/export audit, withheld synthetic policy replay and honest benchmark trade-offs, then exact-commit Linux/container and authorized hosted cold/warm runtime/payload/memory verification. Hosted own-data release also requires an authorized private storage adapter and isolation/expiry/deletion verification. Accounts, integrations, new scenario types, dashboards, AI narration, durable history and exact-optimizer research remain deferred. This is an independent synthetic portfolio project; no customer use or verified real-world savings is claimed.

## Narrow Pass 4 regeneration-provenance correction — 18 September 2026

Started from clean commit `e5abf21aba8f80424942ccd9815cd808d0e0eebd`. The defect was reproduced before modification: an uploaded fixture plan initially returned canonical `uploaded` provenance, but the regenerated review view and regenerated `PlanResult` both returned `null`. `rerun()` discarded the authoritative context returned by `draft_for()`, while `planning.review.regenerate()` replaced the prior result with a fresh provenance-free engine result. Final acceptance checked input/replay/forecast versions but did not compare plan provenance with the authoritative stored dataset.

The workflow boundary now uses one explicit attachment function after controlled regeneration and one acceptance validator. Regeneration attaches the context loaded from the owner-bound dataset/draft record. Final acceptance rejects absent or unequal provenance with structured `stale_provenance` conflict evidence and requires regeneration against the current dataset; it validates again before snapshot creation. The comparison covers the complete typed record: source, bundled sample semantics, dataset ID/hash and actual product/location/assortment/history dimensions. Forecasts, planning, scenarios, replay, review locks, snapshot format and calculations are unchanged.

Local verification completed:

- Focused workflow/profiler suite: **12 passed in 134.73 s**. HTTP regressions cover uploaded fixture/full regeneration, bundled fixture/full regeneration, portable reopen, deliberately wrong browser size labels, evidence, final acceptance, parsed accepted snapshots, deterministic repeated snapshot downloads, missing private references, and missing/mismatched provenance rejection. The existing profiler route-signature/storage regression remains green.
- Complete backend suite: **168 passed in 309.54 s**, with the two existing TestClient deprecation warnings.
- Planning profiler exited zero. Fixture first/repeat: **2.703 / 2.845 s**, **786,644 bytes**; full first/repeat: **4.716 / 3.550 s**, **3,753,042 / 3,753,043 bytes**. All were validated `feasible_fallback` results with deterministic repeats and unchanged component instrumentation/gates.
- Solver smoke passed with SciPy **1.18.1** and HiGHS status 0 (cold **0.001 s**, warm <0.001 s). `pip check` found no broken requirements and the installed npm tree resolved.
- OpenAPI export and generated TypeScript ran twice; both pairs compared byte-for-byte. The production frontend build passed: 40 modules; JS **294.87 kB / 88.68 kB gzip**, CSS **11.60 kB / 3.45 kB gzip**. Complete Playwright: **13 passed in 1.5 min**. The first sandboxed browser attempt could not bind port 8000; the identical permitted rerun passed.
- Production forecast smoke passed: fixture cold/warm **0.143 / 0.032 s**, full **0.931 / 0.168 s**. Production planning first/repeat passed: fixture **2.723 / 2.517 s**, full **3.212 / 3.231 s**. All four independently replayed, reconciled and matched deterministic actions/totals/explanations under the unchanged runtime and payload gates.
- Production scenario smoke passed: fixture comparisons **2.722 / 2.742 s**, full **4.278 / 4.189 s**; future-path comparisons **3.057 / 6.474 s**. Replays, finances, scoped detail and repeat determinism passed.
- Production workflow smoke passed after deliberately sending the opposite bundled size label with each private upload reference. Fixture provenance remained `uploaded` / sample size `null` / hash `421ebd82a7ec646ab1fbf9f45f3d89e119eb8bf0431a249354a23473f73475fc` / dimensions **10, 5, 40, 15,160** through initial plan, regenerated plan, evidence, final acceptance and downloaded snapshot; reopen became `portable` with the same hash/dimensions. Full remained `uploaded` / `null` / hash `bc389b4654552d00c9a1ff4e75515ae5d34d7a112bfd661905dd970a691f95d9` / dimensions **60, 5, 240, 99,160** through the same stages, then `portable` on reopen. Both plans were `feasible_fallback` with feasible independent replay. Snapshot downloads were deterministic byte-for-byte at **172,707 / 932,842 bytes**; financial reconciliation, unique IDs and session cleanup passed.
- Python compilation and `git diff --check` passed. The first sandboxed HTTP smoke client was denied loopback access before reaching an assertion; the permitted reruns above passed.

No Docker, Podman, Colima or Lima executable is installed, so no corrected local container build/start/profile was possible. GitHub Actions for the exact corrected commit, Vercel build/runtime checks and hosted runtime remain pending. Hosted uploads remain blocked pending an authorized private object-store adapter. No push, merge or deployment occurred, and the next pass was not started. This correction is ready for review and commit.

## Narrow Pass 4 profiler and provenance correction — 18 September 2026

Started from clean commit `3ea8f5d794548e81171af14b6b6f485d6ace4186`. GitHub Actions **35323370351** passed **156 backend tests**, solver smoke, contract export/generated-TypeScript comparison, frontend production build, **13 Playwright tests**, Docker build/start, production forecast/planning/scenario smoke, and production upload/review/accept/export/snapshot-reopen smoke. The only failed step was **Profile planning components inside container**, with `TypeError: sample_plan() missing 1 required positional argument: 'http'`. The route gained a required FastAPI request in Pass 4; the profiler still called its old signature. This run does not verify the correction.

The profiler now creates a valid empty Starlette request and calls the same production `sample_plan` route for fixture/full first/repeat. It supplies no private dataset header, cookie or review constraint, so `attach_draft` does not create a review draft or temporary object. All phase instrumentation, serialization, deterministic comparison and `validate_plan` acceptance gates remain. The workflow/Docker step is unchanged and blocking.

The separate provenance defect came from treating scenario `size` as source identity and from deriving review draft size by product count, including a hard-coded `snapshot('fixture', ...)` in reviewed detail. Canonical provenance now records one of bundled fixture, bundled full, uploaded or portable plus normalized dataset ID/hash and exact dimensions. New internal scenario snapshots checksum that record. The server derives it from the actual sample or private stored source; it does not trust a browser size label. Uploaded 10- and 60-product workbooks remain uploaded, portable reopen remains portable, and source/hash/reference mismatches fail clearly. Bundled behavior and legacy bundled snapshot validation remain compatible. Planning/scenario/detail responses expose the verified provenance; calculations and acceptance rules are unchanged.

Local verification completed:

- Focused profiler compatibility: bundled fixture/full traversed the current route with no new storage records.
- Targeted provenance scenarios included a full upload submitted with `size=fixture`, a fixture upload submitted with `size=full`, uploaded plan/capture/compare/reviewed-detail propagation, portable reopen/capture, expired/missing reference rejection, cross-reference mismatch rejection, and deterministic bundled fixture/full identifiers.
- `python -m scripts.planning_profile` exited zero. Fixture first/repeat: **2.744 / 2.567 s**, **786,644 bytes**, deterministic match; full first/repeat: **4.061 / 3.277 s**, **3,753,043 bytes**, deterministic match. All four were valid `feasible_fallback` results. Fixture retained its two-second challenger; full retained `joint_model:not_attempted`. Profile phases continued to report sample, forecast, benchmark, replay, explanation, joint construction, matrix preparation, solver, serialization and remaining route work.
- Final focused profiler/provenance/workflow/scenario suite: **30 passed in 116.10 s**, with the two existing TestClient deprecation warnings.
- Complete backend suite against the final tree: **162 passed in 278.37 s**, with the same two warnings. This includes all 156 tests from the tested Pass 4 commit plus six profiler/provenance regression cases (the bundled-ID case covers both sizes).
- Contract export and generated TypeScript ran twice and compared byte-for-byte. Frontend production build passed: 40 modules; JS **294.87 kB / 88.68 kB gzip**, CSS **11.60 kB / 3.45 kB gzip**.
- Complete Playwright suite: **13 passed in 1.4 min**. Existing demand, planning, scenario and workbook review flows remain green.
- Production forecast smoke passed: fixture **0.033 / 0.032 s**, full **0.168 / 0.287 s**. Production planning first/repeat passed at fixture **2.498 / 2.547 s** and full **3.539 / 4.705 s**; every run independently replayed, reconciled and matched deterministic actions/totals/explanations. Responses were **786,643** and **3,753,042–3,753,043 bytes**, under unchanged gates.
- Production scenario smoke passed. Fixture comparison first/repeat: **2.712 / 2.753 s**; full: **6.335 / 5.646 s**. Fixture/full future-path delay checks: **2.165 / 8.248 s**. Replays, finances, detail versions and repeat determinism passed; no scenario outcome changed.
- Production upload/review/accept/export smoke passed. Fixture/full source XLSX: **445,289 / 2,775,269 bytes**; multipart: **445,518 / 2,775,495**; expanded: **5,814,190 / 37,978,053**; parse: **1,245.89 / 10,583.74 ms**; planning: **1.704 / 5.758 s**; review regeneration: **2.768 / 7.704 s**; acceptance: **0.857 / 6.196 s**; export: **0.109 / 0.688 s**. Reviewed XLSX: **53,065 / 125,248 bytes**; compressed snapshots: **172,624 / 932,751**; expanded snapshots: **3,498,081 / 21,292,180**. Lossless round trips, replay, exact commitment/payment reconciliation, unique external IDs, immutable acceptance, portable reopen and final session cleanup passed.
- Solver smoke passed (SciPy 1.18.1; HiGHS status 0; cold **0.001 s**, warm <0.001 s). `pip check`, installed frontend dependency-tree resolution, Python compileall, generated-contract comparison and `git diff --check` passed. The attempted external `npm audit --omit=dev` was not executed: automatic approval review rejected sending dependency metadata to the npm registry. No dependency changed in this correction.

No planning actions, forecasts, objectives, budgets, replay, review locks, export values, storage policy or runtime/payload threshold was changed. Corrected-commit GitHub Actions, Ubuntu container profiler and hosted execution remain pending. Docker, Podman, Colima and Lima are unavailable locally, so no local container build/start/profile was run. Hosted upload/storage remains blocked pending an authorized private object-store adapter. No push, merge or deployment occurred; Pass 5 was not started. The narrow correction is ready for commit and CI.

## Pass 4 — workbook, reviewed actions and portable acceptance

Implementation starts from `259ddabcae407a84c3ea3b707d850182ee8f0b87`. This section supersedes historical statements below that uploads, action review and exports are unavailable locally. No Pass 5, push, merge, deployment, paid storage or external project setting change is included.

### Pass 3 closure (user-confirmed evidence)

GitHub Actions **35308623547**, commit **259ddab**, passed **108 backend tests**, **10 browser tests**, frontend build, contracts, Docker and solver checks, production planning smoke and production scenario smoke. Fixture planning: **3.331 / 3.323 s**; full planning: **8.278 / 8.128 s**; full scenario comparisons: **11.666 / 11.472 s**; full future-path-delay comparison: **17.699 s**. Both Vercel build checks succeeded. Hosted Vercel calculation execution was **not independently verified**.

The profiler measured a cold full route at **10.658 s**, including **2.456 s** sample construction. Planning smoke followed forecast smoke, which warmed the cached sample. Its sub-10-second measurements are not proof of Vercel cold-start performance. This closes the historical Pass 3 CI blocker only; it does not verify these new Pass 4 changes on Linux or a host.

### Architecture and scope

- The 15-sheet input workbook normalizes to the existing Dataset, with separate Instructions/Examples and optional explicit Reconciliation rows. Fixture/full round trips are exact; offline future truth is excluded. Bounded ZIP/XML preflight and read-only openpyxl parsing reject unsafe, ambiguous or incompatible input with grouped errors and distinct warnings. Request files are cleaned on success/failure/exception.
- Actual workbook/multipart measurement preceded transport selection. No authorized storage resource was configured. A provider-neutral interface and random, purpose/owner-bound local temporary references support local raw-XLSX upload. Calculations send references, never the full normalized JSON from the browser. Vercel fails closed for upload/review-file storage; sample calculations continue. Hosted upload gate remains **blocked** pending an authorized adapter/lifecycle verification. See [WORKBOOK.md](WORKBOOK.md).
- Reviewed accept/reject/exact quantity requirements constrain both benchmark and joint construction; each regeneration rebuilds dependent actions and independently replays the network. Full sample retains its zero joint sub-budget and honest benchmark fallback. No objective, forecast method or tolerance changes. Clearing a review cannot restore confirmed quantities or increase an explicit unconfirmed remainder.
- Final acceptance checks current versions, exact decisions and independent ledger equality, then creates immutable accepted files. Shortfalls require acknowledgement; hard constraints cannot be waived. Engine-valued XLSX and checksummed lossless gzip snapshots have explicit size bounds. Reopen is read-only; creating a new draft requires regeneration. Checksums are corruption detection, not authenticated provenance.
- Confirmed external IDs replace exported candidates, with explicit partial/executed/open quantities. Replay retains existing stock/transit/payable semantics. No durable execution history or automatic ordering is introduced. Uploaded data also uses existing scenario and scoped evidence endpoints.
- CI retains every existing gate and adds production upload/review/accept/export smoke; Docker includes that smoke script. No new Docker/Ubuntu/Vercel result is claimed for this working tree.

### Verification record

Final expanded backend suite: **156 passed in 187.55 s**, with two existing TestClient deprecation warnings. Initial targeted review/API suite: **20 passed in 45.36 s**. Earlier complete runs passed 150 and then 153 tests as coverage expanded. New browser workflows: **3 passed in 32.8 s**. The valid browser edit was corrected to 120 units: the attempted 140-unit fixture purchase rightly exceeded its SAR 1,500 commitment cap. A backend collection attempt overlapped Vite's replacement of dist/assets; it was rerun after the build completed and passed. No acceptance constraint was weakened.

### Remaining boundary

Local temporary storage requires one worker and is not durable or suitable as Vercel object storage. Accepted files survive only until expiry/reset/restart unless downloaded. Exact reviewed locks can cause an honest conflict under the bounded heuristic even if a different feasible policy exists. Hosted storage integration, lifecycle/security testing, exact-commit CI/Docker and hosted execution remain outstanding. Pass 5 is not started.

### Local production measurements (Pass 4)

macOS arm64, Python 3.14.4, one Uvicorn worker, built frontend, port 8011. Forecast smoke preceded planning smoke; these are warm sample/live calculations, not Vercel cold starts. All four plans independently replayed and reconciled; repeated actions, totals, explanations and ledgers matched. Fixture challenger stayed 2 seconds; full stayed `joint_model:not_attempted` with 0 seconds. The unchanged 10-second/4,500,000-byte planning gates passed.

| Planning run | HTTP s | Engine ms | Response bytes | Purchases / movements |
|---|---:|---:|---:|---:|
| Fixture first | 2.565 | 2,551.1 | 786,380 | 24 / 311 |
| Fixture repeat | 2.564 | 2,560.0 | 786,380 | 24 / 311 |
| Full first | 3.197 | 3,179.9 | 3,752,788 | 31 / 607 |
| Full repeat | 3.209 | 3,191.3 | 3,752,788 | 31 / 607 |

Fixture commitments/payments were SAR **91,606 / 97,746**; full **92,550 / 99,050**. Line/payment sums matched exactly and minimum cash headrooms were nonnegative. Forecast fixture HTTP **0.025 / 0.022 s**, full **0.885 / 0.093 s**. Scenario comparison fixture **2.696 / 2.696 s**, full **4.355 / 4.478 s**; future-path fixture/full **3.075 / 6.530 s**. Scenario repeat determinism, invalid frozen suppression, independently feasible replans, financial reconciliation, scoped evidence and existing 30-second/4.5 MB gates passed. Full comparison response **921,311–921,312 bytes**, detail **113,299 bytes**, future-path **1,034,943 bytes**.

| Workbook workflow | Blank | Fixture | Full |
|---|---:|---:|---:|
| XLSX bytes | 18,696 | 445,292 | 2,775,270 |
| Measured multipart bytes (local transport sends raw XLSX) | 18,923 | 445,521 | 2,775,496 |
| Expanded XML/ZIP bytes | 73,462 | 5,814,190 | 37,978,053 |
| Operational rows incl. Settings | 18 empty keys | 15,891 | 103,241 |
| DemandHistory rows | 0 | 15,160 | 99,160 |
| Parse/validation ms | intentionally incomplete | 1,281.33 | 8,359.61 |
| Upload HTTP s | — | 1.378 | 8.671 |
| Uploaded plan HTTP s | — | 2.914 | 4.350 |
| Reviewed regeneration HTTP s | — | 2.743 | 4.865 |
| Final acceptance HTTP s | — | 0.938 | 5.222 |
| Export HTTP s | — | 0.097 | 0.534 |
| Reviewed XLSX bytes | — | 53,076 | 125,215 |
| Snapshot compressed bytes | — | 172,618 | 932,770 |
| Snapshot expanded bytes | — | 3,498,063 | 21,292,162 |

These workbook measurements are from the final production recheck after parser row attribution, review metadata and reconciliation-error reporting changes. Each generated workbook has 18 physical sheets: 15 required inputs, optional Reconciliation, Instructions and Examples. Parser reports 16 input/reconciliation sheets. Counts are unchanged: 10/60 products, five locations, 40/240 assortment series, 12 suppliers, 50/300 inventory rows, 560/3,360 supplier-capacity rows, five lanes, two open orders, two payables, 14 budgets, three events and empty OpenTransfers/Reconciliation. Exact fixture/full Dataset round trips, replay, purchase/payment reconciliation, unique external IDs and read-only snapshot reopening passed. Request temporary directories were removed and final private-session reset passed. File byte counts vary slightly with ZIP timestamps and accepted UUIDs; normalized contents are checked losslessly.

### Commands and results

- `.venv/bin/python -m pytest -q`: **156 passed in 187.55 s** (all 108 prior tests plus 48 Pass 4 cases). Focused `test_review.py`: **19 passed in 39.26 s**, including received-purchase stock/unpaid-balance reconciliation. Joint exact lock/prohibition plus parser success/error cleanup selection: **3 passed in 9.34 s**. Workbook/parser coverage includes full round trip, physical row attribution and warning-overflow blocking.
- `scripts.export_contracts` + `npm --prefix frontend run generate:types`, twice; OpenAPI and generated TypeScript compared with `cmp`: byte-identical.
- `npm --prefix frontend run build`: TypeScript/Vite passed; JS **294.85 kB / 88.67 kB gzip**, CSS **11.60 kB / 3.45 kB gzip**.
- `PORT=8011 CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e`: **13 passed in 1.6 min**; preceding complete run also passed 13 in 1.3 min. New upload/review/export tests plus all 10 prior browser regressions retained. New rejection test also verifies the rejected action remains available for explicitly returning it to draft.
- `.venv/bin/python -m scripts.smoke`, `scripts.planning_smoke`, `scripts.scenario_smoke`, `scripts.workflow_smoke`, each with `--url http://127.0.0.1:8011`: passed; measurements above. The workflow smoke generates and round-trips both fixture/full files before actual HTTP upload/review/accept/export/reopen.
- `scripts.workbook --size blank --output artifacts/blank.xlsx`: passed; actual multipart measured with httpx. Blank is a template, correctly rejected as incomplete operational input.
- `scripts.solver_smoke`: SciPy 1.18.1 import **0.288 s**, expected integer solution/status, cold **0.001 s**, warm <0.001 s.
- `.venv/bin/python -m pip check`: no broken requirements; `npm --prefix frontend ls --depth=0`: resolved installed tree; `npm --prefix frontend audit --omit=dev`: **0 vulnerabilities**. Only XLSX/XML runtime dependencies were added (openpyxl 3.1.5, et_xmlfile 2.0.0, defusedxml 0.7.1).
- `compileall -q backend scripts`, Ruby YAML parse with smoke presence/nonzero-gate checks, and `git diff --check`: passed. Docker/Podman/Colima/Lima commands unavailable. Docker build/container smoke, exact-commit GitHub Actions and hosted/Vercel/storage execution were **not run**.

Local Pass 4 functionality is ready for review. Hosted upload/storage readiness is explicitly not complete. The next step is review of these changes and authorized exact-commit CI; no push/deploy is performed here. No Pass 5 scope is included.

## Focused Pass 3 runtime, supplier-preset and evidence correction — 18 September 2026

Started from clean Pass 3 commit `bfce1ded9de5e74c2b9c0d49e9b6b9b2d1825b0a`. The local correction gates pass, but **Pass 3 is not formally closed** because the exact corrected commit has not yet completed a green GitHub Actions run. No push, merge, deployment or Pass 4 work occurred.

### Failed CI evidence and root cause

User-supplied GitHub Actions run **35242117761** passed 102 backend tests, 10 browser tests, frontend build, Docker build/start, forecast smoke and container solver smoke, then failed both full planning latency assertions at **13.009 s HTTP / 12,960.3 ms engine** and **12.283 s / 12,234.7 ms**. Fixture passed. The valid deterministic full results were `feasible_fallback`, independently replayed, financially reconciled, repeat-identical and approximately 3.75 MB. Production scenario smoke did not run because the preceding planning step failed. The GitHub CLI is unavailable here and the public workflow page could not be fetched, so this supplied run evidence was not independently downloaded.

The workflow profile attributed about **6.6 s** to forecast preparation, **1.45 s** to the deterministic benchmark, **3.0 s** to the joint challenger and **1.6–1.7 s** to remaining work. The 240-series challenger did not complete its first required objective and could never be selected, but consumed the margin needed by the unchanged 10-second live target. The route also revalidated the same immutable cached sample after sample generation had already validated it.

### Correction and calculation guarantees

- The joint MILP implementation, objectives, zero-gap completion rule and focused small-model tests are unchanged. The fixture remains a genuine **2.0-second** best-effort challenger. The full 240-series sample has a disclosed **0-second live challenger budget** and reports `joint_model:not_attempted`; it selects the same deterministic benchmark only after independent replay. A joint plan is still selected only if every required objective stage completes correctly. No fallback is labeled optimal.
- Exact per-series forecast results are preserved. Within a forecast call, range, event, status and training results are memoized by their complete date/cutoff inputs; planning indexes immutable offers and DC/store lanes once per request. The sample API passes its already calculated validation result into planning. Custom datasets and transformed scenarios still validate their complete current input, so changed assumptions cannot reuse stale validation, forecasts or plans. No complete API response is cached.
- Scenario smoke now runs with `if: !cancelled()` after planning smoke, so it still supplies diagnostic coverage when planning fails. Either nonzero smoke result still fails the job; there is no `continue-on-error`, retry, threshold increase or assertion removal.
- Supplier disruption now chooses one supplier with an existing receipt and applicable future paths. The sample selects **SUP08**: `PO-LATE-001` receives the delay and SUP08 receives the dated remaining-availability reduction. The summary displays the supplier ID and name, the submitted request is tested against it, reset remains exact and manual controls remain independent.
- Purchase evidence is derived once in Python from the selected feasible policy's validated replay. It chooses the earliest reachable store shortage, then the largest same-day shortage and location ID; without a shortage it chooses the greatest positive replay-backed replenishment need and location ID. If neither exists, or the policy is infeasible, no store link is invented. Plan Review, original, frozen and replanned scenario outcomes use the same typed targets. Evidence states that purchases arrive into pooled DC inventory, the store is demand context, and other stores compete for that stock.

Correction files: planning/forecast performance and contracts in `backend/app/forecasting/engine.py`, `backend/app/planning/{engine,inputs,contracts,evidence}.py` and `backend/app/main.py`; scenario metadata/targets in `backend/app/scenarios/{contracts,engine}.py`; shared UI routing and preset behavior in `frontend/src/PlanReview.tsx`, `Scenarios.tsx`, `ScenarioEvidence.tsx` and `evidenceTarget.ts` plus generated contracts; regressions in `backend/tests/test_{planning,planning_smoke,scenarios}.py` and `frontend/e2e/scenarios.spec.ts`; smoke/workflow changes in `scripts/{planning_smoke,scenario_smoke}.py` and `.github/workflows/verify.yml`; and the four handoff documents.

### Verification actually executed

| Check | Actual result |
|---|---|
| Complete backend suite | **108 passed in 38.61 s**, with two existing TestClient deprecation warnings. |
| Targeted engine/evidence tests | Final focused run: **7 passed** for purchase routing, deterministic ties, replenishment/no-association fallbacks, size-aware budget, coherent supplier metadata and feasible/invalid scenario-policy routing. Earlier exact small-MILP/deadline-focused selection also passed eight tests. |
| Supplier/evidence browser regression | `scenarios.spec.ts`: **2 passed in 32.9 s**; request/summary supplier consistency, manual independence, non-S1 Plan Review routing, replanned/frozen policy routing, reset and stale-response behavior passed. |
| Complete browser suite | **10 passed in 51.2 s**. |
| Contract reproducibility | OpenAPI SHA-256 `dba747a4…e10331` and generated TypeScript `b0a093f0…2a7378` were identical before and after a second export/generation. |
| Frontend production build | Passed: 38 modules; JS **284.66 kB / 85.63 kB gzip**, CSS **11.60 kB / 3.45 kB gzip**. |
| Solver/dependencies/compilation | SciPy 1.18.1/HiGHS status 0; cold 0.001 s, warm <0.001 s. `pip check` found no broken requirements; production `npm audit` found **0 vulnerabilities**; Python compileall passed. |
| Workflow/diff | Ruby parsed the workflow; scenario follows planning with `!cancelled()` and no `continue-on-error`. `git diff --check` passed. |
| Docker/Linux/CI/hosted | `docker`, Podman, Colima and Lima are unavailable locally. No corrected-commit Docker, Linux CI, Vercel build or hosted runtime verification was performed. |

Production forecast smoke passed at fixture **0.132 / 0.020 s** and full **0.796 / 0.089 s** HTTP. Final production planning measurements were:

| Planning run | Dimensions | HTTP s | Engine ms | Status / stages | Budget s | Actions | Bytes | Replay | Commitments / payments | Minimum headroom C/P/T |
|---|---:|---:|---:|---|---:|---:|---:|---|---:|---:|
| Fixture first | 40 series / 2,800 rows | 2.690 | 2,676.3 | fallback; visible must-stock timeout → benchmark | 2.0 | 24 / 311 | 786,362 | pass | 91,606 / 97,746 | 0 / 14 / 120 |
| Fixture repeat | 40 / 2,800 | 2.468 | 2,464.3 | same | 2.0 | 24 / 311 | 786,362 | pass | 91,606 / 97,746 | 0 / 14 / 120 |
| Full first | 240 / 16,800 | 2.985 | 2,968.4 | fallback; joint not attempted → benchmark | 0.0 | 31 / 607 | 3,752,770 | pass | 92,550 / 99,050 | 40 / 5 / 120 |
| Full repeat | 240 / 16,800 | 2.946 | 2,929.3 | same | 0.0 | 31 / 607 | 3,752,770 | pass | 92,550 / 99,050 | 40 / 5 / 120 |

All purchase values equaled commitments, payment ledgers equaled payment totals, capacity/funding headrooms were nonnegative, and repeat actions, totals and explanations matched. The existing 10-second and 4,500,000-byte gates passed without relaxation.

The production combined scenario was SKU001 +30% for days 1–14, SUP08 `PO-LATE-001` +3 days, SUP08 remaining availability zero for days 1–56, and first-week new commitment authority zero. Final fixture baseline/first/repeat/detail were **2.736 / 2.691 / 2.651 / 0.449 s**, with comparison/detail responses **365,892–365,893 / 114,604 bytes**. Full baseline/first/repeat/detail were **3.763 / 4.101 / 4.020 / 2.812 s**, with comparison/detail responses **921,311–921,312 / 113,298 bytes**. Fixture/full future-path checks were **2.981 / 6.230 s**, below the 30-second scenario limit; the full future-path response was **1,034,943 bytes**. Frozen replay was explicitly infeasible and therefore exposed no evidence targets; replanned replay passed as `feasible_fallback`. Repeats matched, finances reconciled, applied changes were returned, and the measured first replanned purchase targeted **SKU001 / S4** from its own outcome evidence.

### Remaining gate

The local correction is ready for commit and CI, but Pass 3 is ready to close only after the exact corrected commit completes a green GitHub Actions run with both production smoke suites. That run must provide the outstanding Ubuntu/Docker timings. No public-host or Vercel-runtime claim is made.

## Pass 3 — sample review and immutable scenarios — 17 September 2026

**Historical pre-correction Pass 3 implementation gate: met locally.** Started from clean `47dc0217df22d8f31eed2a534e7d279e597861bd`, preserving the accepted Pass 2 engine. The 18 September correction and its outstanding exact-commit CI gate supersede this readiness statement. No push, merge, deployment or later-pass implementation occurred.

### Pass 2 closure evidence

The user supplied successful GitHub Actions run **35228781514** for **47dc021**: 82 backend tests, eight browser tests, contract generation/build, Docker build/start, forecast/container solver smoke, fixture first/repeat **2.865 / 2.851 s**, full **7.604 / 7.496 s**, independent replay, deterministic actions and financial reconciliation. Pass 2 is closed under the approved validated constrained fallback policy. Historical blocked statements below are superseded for that commit. This run was not independently downloaded in this session and does not verify the new Pass 3 changes.

### Implemented flow and contracts

- Plan Review retains its real API results, visible/tail metrics, constrained benchmark/no-action comparisons and explicit benchmark equality. Purchase/movement inspection now links complete selected-SKU stock/cash/receipt evidence and the actual store forecast. A selected inventory series also opens its forecast. Evidence respects pooled stock and grouped fees, without inventing purchase-to-transfer dependencies.
- Scenarios loads a live fixture/full baseline or captures and independently replays the already displayed Plan Review actions without reoptimizing the baseline. Editable Promotion, Supplier disruption and Tighter funds presets populate ordinary controls; scope/date/amount changes can be combined. A pre-run change summary and dirty-state notice prevent old comparisons appearing current.
- Immutable baseline actions and sample version/checksum are carried in small requests. Every scenario starts from a copied baseline. Original, frozen and replanned results are distinct, and frozen/replanned share exactly one transformed dataset/demand/buffer preparation. Overlaps, unknown identifiers, invalid money and unsupported timing envelopes are rejected. No-op/reset preserves the original outcome.
- Demand uplift is applied once to future expected quantities, outside historical evaluation. Receipt delays distinguish selected existing orders from future purchasing paths; calendars and new receipt-relative balances apply, while fixed existing payables remain unchanged and counted once. Availability reductions affect dated remaining capacity for new purchases. Commitment limits and payment ceilings are independent.
- Infeasible frozen policies retain their attempted decisions, cash and failures but expose **no stock/service/aggregate outcome metrics or corresponding deltas**. The replay's diagnostic negative stock cannot masquerade as service. Replanned policies require independent feasibility before being called executable. All sample replans tested returned honest `feasible_fallback` results.
- Compact comparison responses contain summaries, actions, cash, shortages and versions, without daily stock. Scoped detail reconstructs the full network and returns only the selected SKU's 56-day stock, payments, related receipts/movements and underlying evaluated forecast with separate adjustments. Every response identifies baseline/scenario/policy versions; detail does not rerun optimization.
- Browser state is per-session. Editing/reset/dataset changes abort pending rendering and clear obsolete results/detail. Admission-control 429 responses honor Retry-After; stale responses cannot overwrite newer state. No history or daily ledgers are posted back, and no durable process memory is required.

Full transformation rules, status semantics, versioning and stateless endpoints are in [SCENARIOS.md](SCENARIOS.md). Baseline snapshot checksums provide consistency, not cryptographic authentication or execution authority. They are internal transport, not portable exports. No accounts, upload/template workflow, review locks, acceptance, exports, AI or extra scenario family was added.

### Checks actually executed

| Check | Result |
|---|---|
| Complete backend suite | **102 passed in 39.46 s**, two existing TestClient deprecation warnings; all 82 prior regressions retained plus 20 scenario cases/parameter cases. |
| Scenario invariants | Hand-checkable receipt/calendar/balance timing, fixed-payable uniqueness, capacity invalidation, independent commitment/payment limits, existing-obligation infeasibility, frozen invalid-metric suppression, scope/date uplift once, combinations/overlaps, no-op, reset/immutability, repeat determinism, session isolation, version checks, scoped evidence and byte limits passed. |
| Contract export + frontend type generation | Exported/generated twice and compared with `cmp`; byte-identical. Expected new scenario contracts generated in the working tree; original plan/forecast contracts unchanged. |
| Frontend production build | TypeScript/Vite passed; final JS **282.95 kB / 85.00 kB gzip**, CSS **11.60 kB / 3.45 kB gzip**, Vite **455 ms**. |
| Complete browser suite | Final **10 passed in 1.0 min**. Actual API action/forecast inspection, three presets, combined shock, frozen failures, reset and in-flight control/dataset replacement passed alongside existing forecast/planning cases. Previous full run also passed 10 in 57.0 s. |
| Solver smoke | SciPy 1.18.1, import **0.302 s**; expected integer solution/status, cold **0.001 s**, warm <0.001 s. |
| Production forecast/planning/scenario smoke | Passed; detailed measurements below. Baseline threshold remains **10 seconds** and **4,500,000 bytes**. Scenario smoke independently checks a **30-second** HTTP ceiling and the same byte guard, including future-path delays. |
| Python/frontend dependencies | `pip check`: no broken requirements. `npm ls --depth=0`: installed tree resolved. `npm audit --omit=dev`: **0 vulnerabilities**. No dependency upgrades. |
| Compileall / workflow YAML / diff | Compileall, Ruby YAML parse with preserved baseline/new scenario gate checks and `git diff --check` passed. No `continue-on-error`, warning suppression or threshold increase. |
| Docker / CI / hosted | Docker and local VM alternatives unavailable; no new Docker, corrected-commit CI or public/Vercel verification executed. Dockerfile/workflow include the scenario smoke for the next authorized CI run. |

During implementation, the first TypeScript build caught optional action-array iteration and was corrected. A later import cleanup omitted `Funding`; five dependent fixture setups failed, the import was restored, and the complete final backend suite passed. No failures were skipped or assertions removed. React component/effect/accessibility review used the available React best-practices skill; existing evaluation/presentation regressions remain covered.

### Final production measurements

Local macOS arm64, Python 3.14.4, one production Uvicorn worker on port 8011. These final checks followed browser verification; sample input caches were warm. “First/repeat” means successive live calculations for that dataset in the smoke process, not Vercel cold starts. Forecast smoke passed at fixture **0.022 / 0.021 s** and full **0.096 / 0.091 s** HTTP.

| Baseline planning run | HTTP s | Engine ms | Bytes | Purchases / movements |
|---|---:|---:|---:|---:|
| Fixture first | 2.600 | 2,587.1 | 782,591 | 24 / 311 |
| Fixture repeat | 2.618 | 2,614.1 | 782,589 | 24 / 311 |
| Full first | 6.024 | 6,006.2 | 3,747,962 | 31 / 607 |
| Full repeat | 5.983 | 5,964.6 | 3,747,962 | 31 / 607 |

All four baseline runs returned `feasible_fallback`, with `visible_must_stock:time_limit` → `independent_fallback:benchmark`, independent replay true and no failures. Repeated actions, totals and explanations matched. Fixture purchase values/commitments reconciled at **SAR 91,606**, payment ledger/total at **SAR 97,746**, minimum commitment/payment/transfer headroom **0 / 14 / 120 SAR**. Full values reconciled at **SAR 92,550 / 99,050**, minimum headroom **40 / 5 / 120 SAR**. The unchanged baseline 10-second and 4,500,000-byte gates passed.

The pre-correction scenario smoke combined SKU001 +30% demand on days 1–14, the selected existing SUP08 receipt +3 days, SUP01 remaining availability zero for days 1–56, and first-week new commitment authority zero. That mixed-supplier definition is historical evidence only; the corrected coherent SUP08 definition and final measurements are recorded above. It also separately tested a SUP01 future purchasing-path delay of one day.

| Scenario request | HTTP s | Engine ms | Request bytes | Response bytes |
|---|---:|---:|---:|---:|
| Fixture live baseline | 2.603 | 2,591.2 | 19 | 217,349 |
| Fixture combined first | 2.684 | 2,678.4 | 84,378 | 360,234 |
| Fixture combined repeat | 2.680 | 2,674.7 | 84,378 | 360,233 |
| Fixture scoped detail | 0.495 | 489.2 | 165,312 | 97,986 |
| Fixture future-path delay | 3.106 | 3,100.1 | 84,053 | 355,346 |
| Full live baseline | 6.100 | 6,093.7 | 16 | 678,961 |
| Full combined first | 6.601 | 6,578.5 | 159,171 | 974,263 |
| Full combined repeat | 6.621 | 6,599.8 | 159,171 | 974,262 |
| Full scoped detail | 2.967 | 2,948.0 | 292,827 | 97,983 |
| Full future-path delay | 9.134 | 9,111.5 | 158,846 | 1,025,787 |

Both combined runs retained identical original baseline outcomes. Frozen fixture/full actions were infeasible with **9 / 20 explicit failures**, so their outcome metrics and deltas were unavailable. Replanned fixture first/repeat had **22 purchases / 301 movements**, commitments **SAR 89,316** and payments **SAR 95,416**. Replanned full first/repeat had **22 / 516**, commitments **SAR 91,136** and payments **SAR 97,316**. All four replans were independently feasible `feasible_fallback` results with exact purchase/commitment and payment/cash reconciliation and nonnegative funding headroom. Repeated actions, totals, cash, shortages and explanations matched exactly.

Scoped detail retained 280 selected-SKU/location/day rows, matching policy cash and forecast version. Both future-path-delay cases also returned independently feasible replans and honestly infeasible frozen decisions. All scenario requests/responses stayed below 4,500,000 bytes and the separate 30-second scenario smoke ceiling. Baseline planning was not relaxed.

### Files changed

- `backend/app/scenarios/contracts.py`, `backend/app/scenarios/engine.py`: immutable definitions, snapshots, transformations, comparable policies, deltas and scoped detail.
- `backend/app/main.py`, `backend/app/planning/engine.py`: bounded scenario endpoints and internal prepared-forecast reuse; baseline semantics retained.
- `frontend/src/Scenarios.tsx`, `ScenarioEvidence.tsx`, `scenarioApi.ts`: live scenario controls, comparisons, evidence and abort-aware retry handling.
- `frontend/src/App.tsx`, `PlanReview.tsx`, `Demand.tsx`, `styles.css`: linked review flow, shared unchanged forecast renderer, existing visual styles and evidence navigation.
- `frontend/src/contracts.generated.ts`: generated scenario API types.
- `backend/tests/test_scenarios.py`, `frontend/e2e/scenarios.spec.ts`, `frontend/e2e/forecast.spec.ts`: invariant and real-browser coverage; obsolete placeholder assertion replaced by the implemented screen while preserving navigation/icon checks.
- `scripts/scenario_smoke.py`, `Dockerfile`, `.github/workflows/verify.yml`: production scenario gates alongside unchanged baseline verification.
- `docs/BUILD_STATUS.md`, `PLANNING.md`, `SCENARIOS.md`, `DEPLOYMENT.md`: semantics, measured evidence and handoff.

### Short demo using calculated results

1. Open Demand Review on the fixture and inspect SKU001/S1's selected recency-weighted weekday forecast, candidate evaluation and censored history.
2. Open Plan Review: the baseline has **24 purchases / 311 movements**. Expand a purchase or movement and choose its evidence button to inspect dated stock, payments and pooled receipts. Open that actual forecast in Demand Review.
3. Open Scenarios using the same baseline. Apply Promotion and Supplier disruption. Add the first funding week and set new commitment authority to zero, keeping its payment ceiling unchanged. Review the listed scopes/dates, then run live.
4. Inspect the frozen policy's explicit failures and unavailable outcome deltas. The fixture combined replan has **22 purchases / 301 movements**, **SAR 89,316** commitments and **SAR 95,416** payments. Inspect its scoped stock/cash evidence; this is a validated fallback, not a proven optimum or a quantified improvement over invalid frozen arithmetic.
5. Reset to baseline; original actions/outcomes return unchanged. Tighter funds can also be applied separately and edited through the ordinary weekly controls, as verified in the browser suite.

### Remaining limitations and exact Pass 4 handoff

No local Docker runtime is installed. Pass 3's corrected-commit Ubuntu workflow, container timings and all public/Vercel execution remain unverified. Native solver deadlines and admission control are cooperative/per-process. The full baseline response remains close to the payload limit; retain compact comparisons and scoped evidence. Invalid frozen actions intentionally have no stock/service metrics, and current fixed Payables cannot model receipt-dependent existing contracts. Sample snapshots are consistency-checked internal transport, not authenticated or accepted plans.

Pass 4 starts with the existing normalized dataset contracts and validation, `planning/engine.py`, independent `simulation/replay.py`, and the review/scenario components. Add the specified workbook/template parser and choose the documented upload transport before attempting the 17.5 MB normalized full input through Vercel. Then implement explicit accept/reject/quantity-edit dependencies, stale-result invalidation, full replay before final acceptance, reviewed action workbook and portable versioned snapshot. Keep internal scenario transport distinct from accepted exports, preserve external-ID reconciliation and do not duplicate ledgers. None of those Pass 4 features is implemented here.

---

## Pass 2 runtime diagnostics and correction — 17 September 2026

Started from clean `55d1f392b540d0a9f37145a48b66faa10d3ff155`. **The unchanged 10-second gate passes locally; Linux/Docker verification remains outstanding.** No push, merge, deployment or Pass 3 work occurred. This section supersedes the earlier local-only readiness statement for the runtime question.

### Failed CI evidence and limits

User-confirmed GitHub Actions run **35227104588**, job **105221381314**, passed 71 backend tests, eight browser tests, contracts, production build, Docker startup, forecast smoke and container solver smoke. Fixture first/repeat passed in **3.309 / 3.231 s** with deterministic validated benchmark actions. Full first passed feasibility, financial and size assertions, then failed `Exceeded documented 10-second live sample target`. The old smoke asserted before printing; its exact HTTP/engine time and stages are **unknown**, and full repeat did not execute. This evidence was supplied by the user, not independently downloaded during this correction. It is not a corrected-worktree CI pass.

This machine is macOS arm64, Python 3.14.4. `command -v docker colima podman limactl orb` found no runtime; no Linux execution environment is available. **No production Linux/Docker profile has been executed here.** Local profiling identifies real avoidable work and deadline defects, but cannot establish the exact phase responsible for that historical Linux overrun. The next corrected-commit workflow must supply that evidence before claiming the CI runtime issue fully resolved.

### Measured bottleneck and correction

An initial local cProfile showed repeated receiving-space summation in the benchmark (18,617 calls) alongside substantial forecast evaluation, rather than a purely solver-bound request. Low-overhead wall-clock phase measurements below were then collected through the production sample route. The profile pre-imports SciPy separately (0.370 s before / 0.356 s after), reports sample generation/validation separately, and serializes with Pydantic's response type adapter. It is not an HTTP or Vercel cold-start measurement. `scipy_solve` includes SciPy/HiGHS input handling, presolve, solve and result conversion; matrix preparation is measured separately. Construction includes action extraction/cleanup if reached. Values below are seconds, before → after:

| Full-sample phase | First | Repeat |
|---|---|---|
| Sample input generation/validation | 0.768 → 0.757 | <0.001 → <0.001 |
| Forecast generation | 2.377 → 2.366 | 2.348 → 2.352 |
| Benchmark construction | **1.030 → 0.555** | **1.020 → 0.546** |
| Independent replay (all calls) | 0.144 → 0.108 | 0.135 → 0.107 |
| Joint construction | 0.164 → 0.152 | 0.165 → 0.177 |
| Sparse matrix preparation | 0.080 → 0.090 | 0.080 → 0.084 |
| SciPy/HiGHS solve | 2.274 → 2.221 | 2.262 → 2.224 |
| Explanation generation | 0.033 → 0.034 | 0.036 → 0.033 |
| Other validation/context/selection | 0.519 → 0.514 | 0.520 → 0.524 |
| Production route total, excluding serialization | **7.388 → 6.796** | **6.566 → 6.047** |
| Response serialization | 0.013 → 0.012 | 0.012 → 0.012 |

Corrections are deliberately small:

- Benchmark receiving-space totals are reused only within the current calculation and unchanged location/day state. Every day clears the cache; movements invalidate both source and destination; purchases invalidate the DC. Original summation order and constraints are retained. Both fixture/full actions and all benchmark exceptions compare exactly with the uncached implementation at the starting commit, now guarded by regression snapshots and independent replay. No complete plan response is cached.
- The engine no longer replays an incomplete incumbent that policy already rejects. No-action replay, benchmark replay and **separate final proposed-plan replay remain** (three calls on sample fallbacks instead of four). Completed joint plans still receive candidate and final independent checks.
- Joint construction now checks its deadline every 256 variables/rows, and sparse preparation checks while assembling rows. Preparation time is deducted before giving HiGHS its remaining time. Expiration discards partial construction/actions and discloses the timed-out stage. The exact model, objectives, zero gap, two-second sub-budget and 30-second overall limit are unchanged. Native SciPy/HiGHS still cooperatively overshot the sub-budget: corrected full joint totals were 2.462 / 2.486 s. This is **not** a hard process deadline.
- Smoke prints measurements before acceptance gates, collects per-run failures, and executes all four requests when possible. It exposes transport/malformed-response errors with tracebacks, marks unavailable/mismatched comparisons, and exits nonzero after the final failure summary. The 10-second threshold, independent feasibility, financial, size, full-dimension and fallback gates remain active.
- `scripts/planning_profile.py` provides separate phase measurements without changing API contracts. Explanation assembly was extracted unchanged for measurement. Docker includes the script; CI runs it after planning smoke on either smoke success or failure, preserving the original failure and every existing check. It does not run if smoke was skipped/cancelled. Linux profile command: `docker exec planning-pass1 python -m scripts.planning_profile`.

### Production HTTP evidence for this correction

Fresh single-worker process, `PORT=8011 ./scripts/start.sh`; forecast smoke first populated input caches, as in CI. No complete plan cache exists. All responses retain the full 56-day network (fixture 40 series/2,800 stock rows; full 240 series/16,800 rows).

| Run | HTTP s | Engine ms | Response bytes | Purchases / movements | Determinism |
|---|---:|---:|---:|---:|---|
| Fixture first | 2.775 | 2,762.7 | 782,590 | 24 / 311 | Reference |
| Fixture repeat | 2.651 | 2,645.5 | 782,590 | 24 / 311 | Matched |
| Full first | 6.053 | 6,034.9 | 3,747,962 | 31 / 607 | Reference |
| Full repeat | 6.068 | 6,049.3 | 3,747,963 | 31 / 607 | Matched |

All four: HTTP 200, **`feasible_fallback`**, stages **`visible_must_stock:time_limit` → `independent_fallback:benchmark`**, replay feasible with zero failures, no worse lexicographic service than no new actions, and responses below 4,500,000 bytes. Repeated policies (actions, totals, ledgers and explanations) matched exactly, excluding timing/run IDs. Financial reconciliations apply independently to each first and repeat run:

| Dataset | Purchase values = commitments | Payment ledger = payment total | Minimum commitment / payment / transfer headroom |
|---|---:|---:|---|
| Fixture first and repeat | SAR 91,606.00 | SAR 97,746.00 | SAR 0.00 / 14.00 / 120.00 |
| Full first and repeat | SAR 92,550.00 | SAR 99,050.00 | SAR 40.00 / 5.00 / 120.00 |

### Checks actually run

- `.venv/bin/python -m pytest -q`: **82 passed in 17.99 s**, two existing TestClient warnings. New regressions cover later construction expiration, matrix-preparation budget deduction, no late solve, smoke continuation after slow/invalid/malformed/transport/mismatch responses, nonzero CLI failure, and exact fixture/full benchmark equivalence.
- `.venv/bin/python -m scripts.solver_smoke`: SciPy 1.18.1 import 0.298 s; expected integer solution/status, cold 0.001 s and warm <0.001 s.
- Contract export, `npm --prefix frontend run generate:types`, generated-contract diff: passed, no contract changes.
- `npm --prefix frontend run build`: TypeScript/Vite passed, 259.40 kB JS / 79.41 kB gzip, 11.15 kB CSS / 3.34 kB gzip, Vite 388 ms.
- `PORT=8011 npm --prefix frontend run test:e2e`: **8 passed in 19.6 s** against the production server.
- Production forecast smoke: passed, fixture HTTP 0.167 / 0.023 s; full 0.820 / 0.095 s.
- Production planning smoke: **all four passed**, results above, exit zero.
- `.venv/bin/python -m scripts.planning_profile`: before/after phase timings above, both repeat comparisons and validated-plan gates passed. Raw local profiles are in ignored `artifacts/profile-before.txt` / `profile-after.txt`.
- Direct original/corrected benchmark comparison: exact fixture/full action and exception equality. An initial one-off comparison command stopped after fixture because its artifact writer omitted a `Path` import; corrected rerun verified both datasets, then permanent regression tests passed.
- Python dependency check: no broken requirements. Compileall passed.
- Ruby YAML parse and smoke/profile ordering/condition checks passed; no `continue-on-error`. Existing browser, contract, Docker and smoke steps retained.
- `git diff --check`: passed. Forecasting, independent replay, generated contracts, runtime dependency versions and frontend source remain unchanged.
- Docker build/start/profile/smoke: **not executed, runtime unavailable**. CI and hosted verification for this corrected worktree remain outstanding. The threshold was not raised; there is no evidence here justifying a different latency target.

Remaining blocker: execute the corrected workflow or equivalent production Linux container checks, inspect all four HTTP timings plus the now-automatic component profile, and confirm the same 10-second gate there. Do not treat the local Mac pass as Linux runtime proof or begin Pass 3 on that basis.

## Final Pass 2 product readiness — 17 September 2026

**Revised product gate: passed locally.** Started from clean commit `5494b6ecceeba61f512b2c420bd4cde858782515`. This deliberate user-authorized decision supersedes the historical exact-fixture gate and blocked status below. The MVP requires independently feasible, useful purchasing/allocation/cash actions; default sample zero-gap MILP completion is no longer required. No Pass 3 implementation, push, merge or deployment occurred.

The live joint challenger receives **2.0 seconds** inside the existing **30-second overall request limit**, with at least two seconds reserved from that limit for final replay/serialization. Forecast, deterministic benchmark and benchmark replay precede the challenger. Prior profiling spent approximately 28 seconds on the first objective and returned the same benchmark. Two seconds retains fast hand-model completion and leaves substantial room for full-network forecasts and replay. It is a cooperative solver budget, not a hard process termination guarantee. The live sample target is **under 10 seconds HTTP**, now enforced for both datasets by smoke; CI and hosted timing remain unverified for these edits.

A completed joint plan must report the exact required stage sequence, every stage optimal, no positive reported gap, and pass independent replay. Otherwise the deterministic benchmark is selected only after replay passes and its eight-priority lexicographic service score is no worse than no new actions. Incomplete timing-dependent incumbents are not selected. The safe no-new-action/invalid-plan paths remain available for custom failures but do not satisfy the sample action gate. Solver implementation, zero-gap tolerance, forecasts, horizons, constraints, supplier rules and independent replay are unchanged.

Plan Review says **“Validated constrained plan”** and explains that the deterministic constrained planner supplied the recommendations after the joint optimizer did not complete. API status remains `feasible_fallback`, with no global-optimality claim. Detailed interrupted/fallback stages and existing explanations remain available. The exact optimizer and hand-model tests remain available.

### Final production measurements

Fresh production process on localhost:8011; forecast smoke ran first, populating sample input caches. These are live calculations, not cached plan responses or proof of Vercel cold starts. Both networks retain one DC, four stores, 12 suppliers and the 56-day horizon.

| Dataset/run | SKUs / series / stock rows | HTTP s | Engine ms | Bytes | Purchases / movements | Determinism |
|---|---|---:|---:|---:|---|---|
| Fixture first | 10 / 40 / 2,800 | 2.908 | 2,895.0 | 782,590 | 24 / 311 | Reference |
| Fixture repeat | 10 / 40 / 2,800 | 2.644 | 2,639.5 | 782,591 | 24 / 311 | Exact match |
| Full first | 60 / 240 / 16,800 | 6.468 | 6,450.7 | 3,747,963 | 31 / 607 | Reference |
| Full repeat | 60 / 240 / 16,800 | 6.673 | 6,654.3 | 3,747,963 | 31 / 607 | Exact match |

Every run returned **`feasible_fallback`**, with exactly **`visible_must_stock:time_limit` → `independent_fallback:benchmark`**. Every proposed replay was feasible with zero failures. Proposed actions matched benchmark actions; both repeated complete policy results (including stock/cash ledgers, totals and explanations) matched exactly. Run IDs and timing fields are excluded from this comparison.

| Runs | Purchase lines = commitments | Payment ledger = scheduled payments | Minimum commitment / payment / transfer headroom |
|---|---:|---:|---|
| Fixture first and repeat | SAR 91,606.00 | SAR 97,746.00 | SAR 0.00 / 14.00 / 120.00 |
| Full first and repeat | SAR 92,550.00 | SAR 99,050.00 | SAR 40.00 / 5.00 / 120.00 |

All four passed the no-worse-than-no-action lexicographic service comparison, funding limits, full-dimension and 4,500,000-byte response guards. The planning smoke **exited zero**. The full response still approaches the Vercel payload limit; future scenarios must compare frozen/replanned validated policies under identical assumptions and share/reference daily ledgers rather than duplicate them.

### Checks actually executed

| Check | Result |
|---|---|
| Complete backend suite | **71 passed in 11.93 s**, two existing TestClient deprecation warnings. Added budget/fallback determinism, false-completion/positive-gap rejection, completed hand-model selection, and smoke-gate corruption checks. |
| Solver smoke | SciPy 1.18.1; import 0.319 s, cold solve 0.001 s, warm <0.001 s; expected integer result/status. |
| Contract export, TypeScript generation, committed-contract diff | Passed; no schema/type changes. |
| Production frontend build | Passed TypeScript/Vite; JS 259.40 kB (79.41 kB gzip), CSS 11.15 kB (3.34 kB gzip), Vite 398 ms. |
| Full Playwright suite | **8 passed in 21.1 s**, including real API fallback wording, repeat action/explanation equality, dataset changes and existing Pass 1 checks. |
| Production startup and forecast smoke | Passed; fixture HTTP 0.140 / 0.021 s and full 0.814 / 0.090 s first/repeat. |
| Production planning smoke | All four validated-plan gates passed; exact measurements above. Earlier run also passed (fixture 2.621 / 2.740 s, full 7.124 / 7.368 s during concurrent local verification). |
| Python dependency check / frontend dependency tree | No broken Python requirements; frontend tree resolved. |
| `npm audit --omit=dev` | Zero vulnerabilities. |
| Compileall / `git diff --check` | Passed. |
| Docker | Unavailable locally (`command -v docker` returned no executable). Container build/start/smoke remains an outstanding CI check. |
| Protected implementation diff | Optimizer, benchmark, independent replay and prior GitHub Actions maintenance unchanged. |

No GitHub Actions success is claimed for this uncommitted correction. Earlier successful runs below apply only to their named commits; no public/Vercel hosted planning verification was performed. Next work may begin Pass 3 only when separately requested, preserving identical scenario assumptions, independent replay, provenance, honest fallback labels and the ledger response-size constraint.

## Historical correction evidence


## Focused Pass 2 correction attempt — 17 September 2026

This worktree is **not ready for review as the requested complete correction** because the unchanged 10-SKU fixture still does not finish the first lexicographic stage within the existing budget. The strict fixture smoke assertion remains active and correctly exits nonzero. No solver incumbent is relabeled, no objective or hard constraint is relaxed, and Pass 3 has not started.

The explanation defects were corrected independently:

- `_shortage_causes` now uses the independently replayed daily stock ledger and evaluates supply only when it can reach the affected store by the actual shortage date. Each cause includes SKU, store, date, shortage quantity and dated evidence. A merely saturated or available constraint is not called causal; viable alternatives produce an explicit uncertain-attribution record.
- Existing DC/store stock and every eligible inbound transfer lane are checked before attributing a shortage solely to purchasing. Donor reserve, lane calendar, transit, store receipt and remaining lane capacity are included; an available transfer is described as an alternative requiring reoptimization, not proof of allocation error.
- Supplier minimum evidence is calculated for the complete supplier/order-date group, including other planned lines already contributing to the group. The remaining minimum is converted to a case-rounded incremental quantity. A minimum is blamed only when the smaller timely line passes the other dated checks and the larger qualifying group requirement fails a hard limit.
- Candidate deposits, balances and transfer fees are rounded to cents and grouped by funding week before comparison with replayed headroom. Existing obligations and planned payments are already included in that headroom exactly once. This fixes the SAR 50 + SAR 50 same-week case against SAR 60 headroom while retaining feasibility when installments fall in separate sufficiently funded weeks.
- `scripts/planning_smoke.py` retains the fixture/full acceptance rules and now prints dimensions, action counts, response bytes, independent replay, commitment/payment reconciliation and minimum commitment/payment/transfer headroom for every run.

Optimizer profiling and discarded experiments:

- Baseline fixture model construction produced **15,904 variables, 9,936 integer variables and 23,899 rows**. Forecasting completed in approximately **0.36 s**; HiGHS then spent the remaining approximately **28 s** in `visible_must_stock` without an incumbent in the unchanged formulation.
- Semantics-preserving experimental reductions removed redundant activation/deposit variables, tightened stock bounds, supplied an independently replayed benchmark start and isolated the exact 28-day visible state. The best measured first-stage run still consumed the remaining budget with an open **0.2–0.9% MIP gap** and never reached the later objectives.
- Those experimental optimizer edits were discarded. `backend/app/planning/optimizer.py`, the 30-second budget, horizons, candidates, integrality, constraints, objective order and zero-gap requirement remain unchanged. Meeting the gate now requires a separately reviewed temporal/network decomposition or an equivalent compact formulation with a complete optimality certificate; accepting the incumbent or loosening the gap would violate the specification.

Current-worktree validation:

| Command / check | Actual result |
|---|---|
| Explanation regressions | **5 passed**: satisfied minimum/timing, genuinely blocking grouped minimum, same-week cash aggregation, separate-week feasibility, cent rounding/existing obligations and transfer-stock alternative evidence. |
| `.venv/bin/python -m pytest -q` | **67 passed in 9.26 s**; two unchanged upstream TestClient deprecation warnings. |
| `.venv/bin/python -m scripts.solver_smoke` | SciPy **1.18.1** import **0.382 s**; HiGHS cold **0.006 s**, warm **<0.001 s**, expected integer result. |
| Contract export, TypeScript generation and committed-file diff | Passed; contracts remained reproducible and unchanged. |
| `npm --prefix frontend run build` | Passed: **259.25 kB JS / 79.38 kB gzip**, **11.15 kB CSS / 3.34 kB gzip**, Vite **398 ms**. |
| Full Playwright suite | After installing its pinned Chromium runtime, **8 passed in 2.1 min** against the current production server. The initial attempt could not launch because that browser binary was absent; no application test ran in that attempt. |
| Production forecast smoke | Passed: fixture **0.147 / 0.022 s**, full **0.836 / 0.093 s** first/repeat HTTP. |
| Planning smoke, fixture first/repeat | Expected strict-gate failure: **28.104 / 28.079 s HTTP**, **28,083.1 / 28,070.7 ms engine**, **782,410 / 782,409 bytes**, 40 series, 2,800 stock rows, **24 purchases / 311 movements**, replay true. Both were `feasible_fallback` after `visible_must_stock:time_limit`. Commitments and payments reconciled at **SAR 91,606 / SAR 97,746**; minimum commitment/payment/transfer headroom was **SAR 0 / 14 / 120**. |
| Planning smoke, full first/repeat | Accepted fallback behavior: **28.381 / 28.489 s HTTP**, **28,355.5 / 28,468.4 ms engine**, **3,747,784 bytes**, 240 series, 16,800 stock rows, **31 purchases / 607 movements**, replay true. Commitments and payments reconciled at **SAR 92,550 / SAR 99,050**; minimum headroom was **SAR 40 / 5 / 120**. The script exited nonzero only for the two fixture gate failures. |
| `.venv/bin/pip check` / `npm --prefix frontend ls --depth=0` / `npm audit --omit=dev` | No broken Python requirements; installed frontend tree resolved; **0 npm vulnerabilities**. |
| Docker | Not executed because `command -v docker` returned no executable. A corrected-code container check therefore remains outstanding. |
| `git diff --check` | Passed before documentation updates and will be rerun on the final worktree. |

The exact next step is an optimizer-only correction in `backend/app/planning/optimizer.py` that produces exact first/repeat fixture completion through `stable_action_ties` inside the existing budget, followed by the full verification matrix and Docker/Ubuntu CI. The explanation corrections can be reviewed independently, but the requested Pass 2 correction exit gate remains unmet.

## GitHub Actions maintenance — 17 September 2026

Failed GitHub Actions run `35215202230`, job `105181927681`, was inspected through GitHub's public Actions API. It ran commit `bb06db8` on `ubuntu-latest`. Checkout, Python/Node setup, dependency installation, backend tests, host solver smoke, contract generation/diff, frontend build, browser tests, Docker build and Docker startup all succeeded. The final combined smoke step failed because both fixture planning calls returned the independently replayed `feasible_fallback` after `visible_must_stock` reached its time limit. That is the unresolved application-level optimizer gate documented below; the Node 20 annotations did not cause the failure.

Workflow-only maintenance now uses the current Node 24 action lines recommended by the official repositories:

- `actions/checkout@v7` (currently v7.0.1) uses Node 24 internally. Its safer behavior for `pull_request_target` and `workflow_run` does not change this workflow's existing `push` and `pull_request` triggers. The Node 24 action runtime requires Actions Runner **2.327.1 or newer**; the maintained GitHub-hosted `ubuntu-latest` runner satisfies that requirement.
- `actions/setup-node@v7` (currently v7.0.0) retains `node-version: '24'`, explicit npm caching and `frontend/package-lock.json`. Its ESM/dependency update and cache-output additions require no input changes here; the workflow does not use the removed `always-auth` input.
- `actions/setup-python@v7` (currently v7.0.0) retains `python-version: '3.14'`. Its ESM/dependency update requires no input changes here; the workflow does not use the removed `pip-install` input.

The workflow now gives forecast smoke, container solver smoke and planning smoke separate named steps. Container readiness has its own final health check. The planning smoke remains last and retains its nonzero exit when the fixture is anything other than `feasible`; full continues to allow `feasible` or `feasible_fallback`. No assertion, test, Docker check, trigger, cache, permission or runtime version was removed or weakened. `ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION`, warning suppression, `continue-on-error` and Pass 3 changes were not added.

Local maintenance validation is recorded after the workflow edits. No GitHub Actions success is claimed for this worktree; a run for a future committed/pushed correction will be separate evidence. The next application correction must still make fixture first/repeat complete every joint stage through `stable_action_ties` within the existing budget.

| Maintenance check | Actual result |
|---|---|
| GitHub public Actions API for run `35215202230`, job `105181927681` | Confirmed `failure` for commit `bb06db8`; steps through Docker startup succeeded and the final combined smoke step failed. The `gh` CLI was unavailable locally, so the public API was used instead. |
| Official v7 `action.yml` metadata and release notes | Confirmed all three actions declare `using: node24`; existing `node-version`, `python-version`, npm cache and cache lockfile inputs remain supported. Confirmed the minimum Node 24 action runner requirement and reviewed the v7 input changes before selecting the versions. |
| Ruby YAML parse plus workflow invariant script | Passed. Verified `ubuntu-latest`, push/pull-request triggers, Node 24, Python 3.14, npm cache path, contract diff, backend/browser/Docker checks, three separately named smoke steps, absence of `continue-on-error` and the unchanged planning acceptance policy. |
| `.venv/bin/python -m py_compile scripts/planning_smoke.py` | Passed; the fixture/full acceptance assertions remain executable. |
| `.venv/bin/python -m pytest -q` | **62 passed in 9.06 s**; two unchanged upstream TestClient deprecation warnings. |
| Contract export, generated TypeScript comparison | Passed; no generated contract diff. |
| `npm --prefix frontend run build` | Passed: **259.25 kB JS / 79.38 kB gzip**, **11.15 kB CSS / 3.34 kB gzip**, Vite build **388 ms**. |
| `git diff --check` | Passed. |

## Narrow Pass 2 correction — 17 September 2026

This correction remains **blocked at the fixture joint-optimizer exit gate** and is not ready for review or commit. The default 10-SKU fixture still reaches the 30-second planning budget in `visible_must_stock` with an open MIP gap and correctly returns `feasible_fallback`; it does not complete through `stable_action_ties`. No incomplete incumbent is labeled optimal, no hard constraint or horizon was relaxed, and Pass 3 has not started.

Implemented and locally covered in the current worktree:

- Protection-period paths now require an offer to be valid and orderable at each origin, including order/dispatch weekdays, supplier lead time, DC receipt, lane dispatch and store receipt calendars. Expired and not-yet-orderable offers are excluded, current slower valid sources remain part of the conservative longest path, and absence of any valid path returns `no_valid_replenishment_path`.
- Joint optimizer `RuntimeError` handling is limited to the optimizer call. It discards partial solver output, records a sanitized `joint_model:error` stage, independently replays the benchmark, then uses benchmark/no-action/invalid-plan in that order according to replay feasibility.
- Completed joint plans supplement `DATED_SUPPLY_SHORTFALL` with evidence-backed dated supplier SKU/shared-capacity, commitment, payment, grouped-minimum or lead-time causes where the final actions and remaining headroom prove the limit.
- `scripts/planning_smoke.py` now requires `feasible` for the fixture, permits the documented fallback for full, and prints stages plus independent replay status. It intentionally fails while the fixture gate above remains unresolved.
- Pass 3 must not duplicate the full daily ledger for each scenario comparison because the measured full response is already close to the 4.5 MB Function response limit.

Measured optimizer blocker: repeated profiles show forecasting/context/benchmark construction completes in under one second, while HiGHS spends the remaining approximately 27 seconds on the first fixture service objective. Formulation experiments reduced variables and found feasible incumbents, but exact optimality proof and the remaining ordered objectives still exceeded the unchanged budget. Unsafe service relaxations and incomplete certificates were discarded; `backend/app/planning/optimizer.py` remains at the original Pass 2 implementation.

GitHub Actions run `35201527675` succeeded on Ubuntu for original Pass 2 commit `6c587cc`. It completed **56 backend tests**, solver smoke, frontend production build, browser tests, Docker build/start, forecast smoke, fixture/full planning smoke and solver smoke inside the container. Later run `35215202230` for correction commit `bb06db8` failed only at the intentionally stricter fixture planning gate described above. Neither run verifies a public host or Vercel-hosted planning runtime.

Local correction checks executed so far:

| Command / check | Actual result |
|---|---|
| Targeted offer-validity tests | **5 passed in 2.75 s**. |
| Solver-error and separate timeout fallback tests | **2 passed in 1.87 s**, with two upstream TestClient deprecation warnings. |
| Binding commitment explanation test | **1 passed in 0.61 s**. |
| `.venv/bin/python -m pytest -q` | Final run: **62 passed in 8.71 s**; two unchanged upstream TestClient deprecation warnings. |
| Contract export, TypeScript generation and generated-file diff | Passed; generated contracts remained unchanged. |
| `npm --prefix frontend run build` | Passed: **259.25 kB JS / 79.38 kB gzip**, **11.15 kB CSS / 3.34 kB gzip**, Vite build **399 ms**. |
| Full Playwright suite | Initial run accidentally reused a stale Pass 1 server on port 8000 and timed out waiting for planning responses. After stopping that server and starting the current application, **8 passed in 2.0 minutes**. |
| Production forecast smoke | Passed. Fixture **0.152 / 0.031 s**, full **0.846 / 0.094 s** first/repeat HTTP; all were live evaluated results. |
| Planning smoke, fixture first/repeat | Expected exit-gate failure after recording both results: **28.097 / 28.085 s HTTP**, **28,080.3 / 28,078.5 ms engine**, **782,437 / 782,439 bytes**, **24 purchases / 311 movements**, independent replay true. Both returned `feasible_fallback` with `visible_must_stock:time_limit`, then benchmark fallback. |
| Planning smoke, full first/repeat | Accepted full-sample behavior: **28.353 / 28.321 s HTTP**, **28,330.7 / 28,301.3 ms engine**, **3,747,785 bytes** both runs, **31 purchases / 607 movements**, independent replay true. Both returned `feasible_fallback` with the disclosed timeout and benchmark stage. The script exits nonzero only because both fixture runs violate the new `feasible` requirement. |
| `.venv/bin/python -m pip check` | No broken requirements found. |
| `.venv/bin/python -m compileall -q backend scripts` | Passed. |
| `git diff --check` | Passed on the final worktree. |

The exact starting point for further correction work is `backend/app/planning/optimizer.py`: obtain an exact fixture solution through all staged objectives within the existing overall budget without changing model semantics. Only after that gate passes should the complete backend, contract, frontend, browser, production forecast and first/repeat planning smoke matrix be rerun. Pass 3 must not begin before this correction is complete.

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

**Original Pass 2 exit gate:** this was recorded as met locally for commit `6c587cc`; the narrow correction gate documented above is currently unmet. Ubuntu/container checks for that original commit subsequently passed in GitHub Actions run `35201527675`. Correction CI and all public-host/Vercel planning-runtime checks remain outstanding. The complete six-pass MVP release gate remains unmet.

### Limitations and handoff

The measured sample results are independently feasible fallbacks with substantial visible and provisional-tail shortages. The joint solver did not finish its highest-priority stage within the allotted budget on this machine; neither sample is advertised as lexicographically optimal or better than the constrained benchmark. A small hand model finishes all stages optimally. Benchmark receiving-space reservations and single-line supplier-minimum handling are conservative. Runtime may change with hardware; the shared budget is cooperative, not an OS-enforced deadline.

Docker is not installed locally (`command -v docker` returned no executable). GitHub Actions run `35201527675` supplied the Ubuntu Docker build/start and production smoke evidence for original Pass 2 commit `6c587cc`; it does not cover the current correction. Hosted cold latency, memory, wheel packaging and response limits still need verification. The future workbook payload/storage gap remains unchanged; no upload transport was introduced.

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
