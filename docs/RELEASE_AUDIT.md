# Historical release audit through `ff2e42d`

> This audit is preserved as historical baseline evidence. It does not describe the current production candidate. See [current build status](BUILD_STATUS.md), [current deployment status](DEPLOYMENT.md) and the [chronology archive](history/README.md).

# Final public-sample release closure — 24 September 2026

Pass 5 and Pass 6 are closed for exact release **`ff2e42d907f6b0a83811849c7efab10ff1007dcc`**. Normal verification [35967399001](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35967399001) succeeded. The canonical READY production deployment is **`dpl_9zrziwJbe3abDQyxtA1hS6gfjnPa`** in **`iad1`**, available at [the canonical URL](https://demand-supply-planning-intelligence.vercel.app) and [immutable URL](https://demand-supply-planning-intelligence-3gdxptwpt.vercel.app), both serving the exact release commit.

Two consecutive unchanged canonical latency runs passed with no probe failures: [35967540536](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35967540536) measured full first/repeat HTTP **9.033 / 3.248 s** and engine **5.381 / 2.557 s**; [35968872124](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35968872124) measured **7.969 / 2.995 s** HTTP and **4.841 / 2.429 s** engine. Approximately **1,022,712-byte** compact responses passed the unchanged cold latency, size, reconciliation, determinism, scenario capture, scoped-detail and independent replay gates. Both runs retained measurement artifacts. The public sample demo, sample planning, scenarios and evidence are production-verified; portfolio-MVP feature development is complete.

Local/Docker workbook upload, review, acceptance, export and portable reopen remain verified. Hosted workbook upload and accepted-export persistence remain intentionally disabled until an authorized private persistent-storage adapter is implemented, configured and lifecycle-tested. That boundary does not block the public sample demo, but this release must not be represented as a fully hosted own-data production service. All earlier statements below that exact-commit CI, deployment or canonical latency acceptance remained pending are historical and superseded by this closure.

---

# Final Pass 6 closure check — 20 September 2026

**Pass 6 remains open — production latency gate not yet proven.** This section supersedes older statements that corrected CI, Docker verification or deployment did not exist. Hosted own-data remains a separate intentionally blocked gate.

Local and remote `main` were confirmed at **03bb1affbe8448849725ad34c939de9601e2dc67**. [Verify planning MVP 35493689224](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35493689224), job **106032834212**, succeeded for that exact checkout: **209 backend tests (803.23 s), 26 browser tests (4.2 min)**, host/container HiGHS smoke, reproducible contracts, production build, Docker build/start/health, forecast, complete/compact planning, authoritative scoped evidence, scenarios, profiling and fixture/full upload/review/accept/export/reopen/reset. The latter uses CI's **local storage driver**, not a hosted private provider. Full results and financial/determinism evidence are in [BUILD_STATUS.md](BUILD_STATUS.md).

Both deployment-ID and canonical-alias lookups confirm **dpl_BHtMKw2mgLGXCksj6aB2GqnYBy27**, **READY**, production, **iad1**, exact **03bb1aff**:

- [Canonical application](https://demand-supply-planning-intelligence.vercel.app)
- [Immutable deployment](https://demand-supply-planning-intelligence-qr2woqqgp.vercel.app)

Runtime inspection for this exact deployment, **2026-09-20 06:15:29–07:09:00 UTC**, found one **GET `/` HTTP 400 at 06:21:59 UTC**, with no cause provided. Separate 5xx, error/fatal and timeout searches returned no entries. Do not turn that into an unrestricted claim of zero errors; a future manual probe still needs its own request-window correlation. The connector supplies no invocation-duration breakdown.

There is **no new qualifying canonical-host timing run**. The user confirmed the current shell's **bom1 → iad1** route, with approximately **9–14 s TLS establishment**, is unsuitable as passing latency evidence. Those failures remain relevant and do not establish an application defect. No automatic deployment, project/environment change, provisioning, push or dispatch was performed. New production health, fixture first/repeat, full first/repeat, capture and detail timings all remain **pending**.

CI container evidence is distinct: complete full first/repeat **6.159 / 2.450 s**, compact **2.329 / 2.444 s**, capture **0.990 / 0.851 s**, detail **2.086 / 2.214 s**. Compact full responses were **1,022,713 / 1,022,711 bytes**, detail **110,149 bytes**. All independent feasibility, commitments/payments/movement expenses, deterministic actions/totals/explanations, size and evidence checks passed. The deterministic constrained policy remains **`feasible_fallback`**, never optimal. Full component profiling still shows live replay and benchmark work; a fast repeat does not prove an instance-cold start or public WAN latency.

The separate manual [production-latency workflow](../.github/workflows/production-latency.yml) runs on `ubuntu-latest`, sends only canonical-host sample requests, and uploads complete timing/correctness evidence even on failure. Its [probe](../scripts/production_latency.py) records cumulative DNS/TCP/TLS, first byte, body drain, total HTTP, bytes, peer/region/request ID, reported engine/status/stages and replay. Fresh sessions and observed reused connections are checked separately. Fixture/full plans, two consecutive full requests, capture and scoped detail retain **10 seconds** and **4.5 MB**; complete replay confirms stock, cash and provenance. Slow first measurements are retained; there is no retry/sleep/redirect or plan cache.

The production latency gate remains pending until the user pushes this workflow and its manually triggered canonical-host run succeeds. Afterward, verify the alias/deployed SHA and exact-deployment runtime logs for that artifact's UTC window. The probe SHA is not automatically the deployed SHA. A hosted Ubuntu runner's region is not fixed by `ubuntu-latest`; inspect job setup and request IDs before describing the route.

Local harness validation passed actionlint and **8 focused regressions**, plus the full **11-request / 105-assertion** sequence against the unchanged local API. The complete local backend rerun passed **217 tests and 10 subtests in 333.69 s**, with two existing warnings. These prove harness behavior only. The existing `verify.yml` remains unchanged; new exact-commit CI is pending for the added probe/workflow. Final local verification details are in BUILD_STATUS.

The canonical session endpoint was checked again (HTTP 200 at **07:06:45 UTC**) and returns **`enabled: false`, `driver: disabled`**. Full hosted own-data cannot close without an authorized real private provider and lifecycle/isolation/workflow verification. It will not alone keep the separate public-sample gate open once that gate is proven. The duplicate **demand-supply-planning-intelligence-hahy** project still exists and remains non-blocking housekeeping; neither project was disconnected or modified.

---

# Final focused Pass 6 correction — 20 September 2026

Current reviewed baseline is **055eb0a4f6ee78c77f697569a5acbd044a2f5c53**. [CI 35491100761](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35491100761), job **106026056837**, completed successfully: 197 backend tests, 26 browser tests, contracts/build, Docker, solver, complete/compact planning, evidence, scenarios and own-data workflow smokes. Those results certify the baseline only. The new local changes have no new remote run or deployment.

The canonical deployed baseline is **dpl_vPgb8yq7ivQ7FxDqgAZGkpmotE6n**, immutable alias `demand-supply-planning-intelligence-10cys4089.vercel.app`, **iad1**, exact **055eb0a**, serving `https://demand-supply-planning-intelligence.vercel.app`. The separate `demand-supply-planning-intelligence-hahy` deployment check remains project housekeeping; it was not disconnected, deleted or reconfigured.

New serial canonical-baseline measurements: full first/repeat **12.290 / 9.240 s HTTP**, **7,536.7 / 7,737.1 ms reported calculation**, **1,022,713 / 1,022,712 bytes**; first byte **11.516 / 8.535 s**, body drain **0.774 / 0.705 s**. Fixture plan/capture/detail were **5.424 / 2.543 / 2.397 s**, with correct 280-row scoped evidence and matching cash/provenance. Health took **2.813 s**. The first full request fails the retained ten-second gate. Earlier independent user measurements of 19.79–25.74 s full HTTP and 13.38 / 13.61 s fixture capture/detail remain relevant failures, not superseded by one faster repeat.

Available runtime logs expose successful invocation paths/statuses but no platform duration or startup details. The large variable pre-header residual cannot yet be fully attributed. DNS/connect/TLS, client first-byte/body times and reported engine time are separately recorded in BUILD_STATUS; none proves a new Vercel instance or measures invocation start. No corrected-host timing is claimed.

The correction defers Excel/NumPy and accepted-file imports to file workflows, and reuses only deterministic forecast preparation for at most two exact registered bundled samples. Eligibility requires the complete unchanged dataset hash; keys include engine/schema, forecast and preparation versions. A single-construction lock keeps concurrent first catalog/forecast requests on the same registered sample object. Mutated or unregistered uploaded/reviewed copies miss; returned buffers/traces/arrays are independent copies with fresh trace UUIDs. Scenario/action checks and independent replay remain live. No complete recommendation, ledger, API response or private state is cached. External contracts, frontend source, planning semantics, solver budgets and deployment settings are unchanged.

Opt-in `PLANNING_DIAGNOSTICS=1` now records fixed-name startup and full ASGI-boundary phases, including actual response-field validation and serialization. Startup durations describe process setup, not extra time to add to each warm request; nested phase times are inclusive. `response_ready` starts when ASGI receives the request and excludes platform work before application dispatch. `asgi_ms` ends after the application sends its body; it cannot establish that the client received it. Application code cannot establish the Vercel invocation start without platform telemetry. Metric names are allowlisted; logs contain numeric durations/counts and no data, IDs, credentials or stack traces. No remote environment variable was set.

Private metadata commit now survives subsequent blob-cleanup failure: the new reference returns, the old reference stays invalid, and durable tombstones remain until successful sweep. Cleanup logs one bounded count; explicit sweep still fails when work remains queued. Delete/reset and upload-finalization cleanup share this behavior; original pre-commit/validation failures remain errors. See PRIVATE_STORAGE for provider contracts and regression scope.

## Local before/after request boundary

Measured serially on macOS arm64 / Python 3.14.4, single-worker Uvicorn, with the same compiled frontend. The baseline backend/scripts were extracted from 055eb0a into an isolated temporary directory; baseline port 8031 was stopped before measuring corrected port 8030. Both pages were checked with agent-browser. Browser verification requested fixture forecasts only; each **first full plan is the first full sample/preparation request in its fresh server process**. This does not establish Vercel instance-cold behavior, and HTTP excludes server-process startup before listening. Measurements completed before the broad test suites ran.

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

The first uncached full request **did not materially improve**: 2.832 → 2.940 s locally; registering and verifying the complete forecast-reuse identity has a small first-miss cost. Repeat full planning, capture and evidence improve substantially. Do not describe a fast cache hit as proof of cold-start or hosted acceptance. Both sizes retain their exact actions, totals, explanations, scoped 280-row stock, cash and provenance; the independent complete replay was fetched separately for equality checks. Responses remain about 1.02 MB full compact, 0.33 MB fixture compact, 0.11 MB scoped detail and 3.75 MB full complete.

Final actual response-boundary phases for full first / repeat (milliseconds, inclusive where nested):

| Phase | First ms | Repeat ms |
|---|---:|---:|
| request_body | 0.004 | 0.004 |
| sample_construction | 303.112 | 0.000 |
| dataset_validation | 402.098 | 0.000 |
| sample_input | 787.748 | 0.000 |
| dataset_context | 866.355 | 79.550 |
| forecast_identity | 78.655 | 78.803 |
| network_forecast | 1,398.331 | 81.017 |
| forecast_reuse | 0.000 | 2.187 |
| benchmark | 393.225 | 400.098 |
| independent_replay | 125.490 | 104.152 |
| explanations | 33.986 | 33.587 |
| planning | 2,057.361 | 729.816 |
| review_attachment | 0.024 | 0.011 |
| response_validation | 0.004 | 0.008 |
| response_serialization | 2.193 | 2.184 |
| response_ready | 2,928.543 | 814.315 |

Absent first/miss or repeat/hit phases are zero in this table. `dataset_context` includes sample creation/validation and provenance on a miss; `planning` includes forecasts, benchmark, replay and explanations; neither set should be summed twice. Response validation and JSON serialization are the actual installed FastAPI/Pydantic response-field calls, not a separate estimator. First-response headers and body-drain measurements are retained in `artifacts/final6-boundary-final.json`. Application import was **172.506 ms**, route setup **6.818 ms**, workflow-module import **29.639 ms**, and ASGI lifespan startup **0.009 ms** in this process. These startup metrics are not repeated work on every request. Platform invocation start, interpreter setup before application import and WAN transfer remain separate unknowns until deployment telemetry is available.

## Final component and correctness verification

A separate serial `scripts.planning_profile` comparison against isolated 055eb0a confirms the repeated work eliminated (seconds; inclusive components are not additive):

| Full component | Before first / repeat | After first / repeat |
|---|---:|---:|
| Route before final serialization | 2.826 / 2.051 | 2.962 / 0.798 |
| Sample construction/validation/registration | 0.741 / <0.001 | 0.802 / <0.001 |
| Forecast preparation, including identity check | 1.338 / 1.330 | 1.438 / 0.081 |
| Independent replay, three calls | 0.129 / 0.105 | 0.107 / 0.105 |
| Benchmark construction | 0.392 / 0.395 | 0.396 / 0.394 |
| Explanation generation | 0.033 / 0.033 | 0.033 / 0.032 |
| Complete JSON serialization | 0.0113 / 0.0114 | 0.0114 / 0.0112 |

Full joint construction/solve remains unattempted. Fixture route was **2.511 / 2.391 → 2.537 / 2.196 s**, retaining its two-second challenger. This is a targeted repeated-forecast reduction, not evidence that the hosted pre-header residual has been fixed.

Three interleaved **fresh subprocess API imports** measured baseline **0.306 / 0.206 / 0.206 s** and correction **0.160 / 0.153 / 0.175 s** (median **0.206 → 0.160 s**). Every baseline loaded NumPy, openpyxl and accepted-file code; no corrected import loaded those modules. The fresh-import regression additionally excludes SciPy, private-storage composition and unittest.mock. OS filesystem caches were not flushed; these are fresh Python processes, not proven Vercel instance-cold starts. Removing roughly 47 ms of median local imports does not explain all previously observed multi-second hosted residuals.

Final verification: **209 backend tests, 26 browser tests**, solver smoke, exact contract regeneration, production build, forecast/complete-plan/compact-plan/scenario/workflow smokes, release trace, dependencies, compilation and diff checks passed. All four offline fixture/full policy runs passed and repeated files were byte-identical. Private cleanup coverage includes six injected failure/concurrency/API regressions; fourteen provider conformance tests also passed within the complete suite. Cache miss/hit evidence, full-precision calculations, independent replay, scenario identities, stale review rejection and financial reconciliation remain covered. BUILD_STATUS records commands and all four final complete planning measurements. No new Docker or remote verification was possible in this correction.

**Public sample readiness remains open** pending green CI for the exact new correction and a separately authorized canonical deployment passing fixture/full planning, two consecutive full requests, capture and scoped evidence under ten seconds with unchanged payload and reconciliation gates. Docker-compatible tools are unavailable locally. **Full hosted own-data remains blocked**: the actual host reports `enabled: false`, `driver: disabled`; no authorized blob and transactional metadata provider, credentials or real-provider transport/lifecycle verification exists. Neither successful deployment builds nor local speed establishes these release gates.

No push, merge, deployment, paid provisioning or Vercel project-setting change was performed. The instruction prohibiting those actions prevents obtaining a new remote workflow/deployment during this local correction. After separate authorization, verify the exact deployed SHA and correlate diagnostic ASGI phases with Vercel invocation duration and serial client measurements. Keep the duplicate project housekeeping separate from the canonical release check.

---

# Pass 6 focused release correction — 20 September 2026

Started from clean `e51af6fc1dc5338e4f9d54380fe7acceca55edd1`. This section supersedes older release-readiness statements; historical evidence below is retained.

**Exact baseline CI is green:** [GitHub Actions 35464690297](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35464690297), job `105954779663`, completed successfully for `e51af6f`. It passed 173 backend tests (655.28 s), 26 browser tests (5.8 min), solver smoke, reproducible contracts, production build, Docker build/start, container solver, forecast/planning/scenario smokes, container component profiling and upload/review/accept/export/reopen. Fixture planning HTTP was 3.506 / 3.564 s; full was 9.162 / 9.304 s (engine 8,946.4 / 9,085.4 ms), with deterministic, financially reconciled, independently replayed fallback results. This is baseline evidence, **not CI for these uncommitted changes**.

The canonical Vercel deployment was confirmed at **e51af6f**, deployment `dpl_EjnDRZ4PWPW9qu3HvjctMyHpBvLM`, project `prj_9wUSzLP3zKbvVinWCeNvmyDelVh5`, `iad1`, immutable alias `demand-supply-planning-intelligence-f7633owp1.vercel.app`, production alias `demand-supply-planning-intelligence.vercel.app`. A serial baseline full request in this correction took **19.567 s HTTP / 11,446.3 ms engine / 3,753,044 bytes**, with first byte at 17.997 s. Independent replay passed and status remained `feasible_fallback`. This is another failed baseline runtime observation, not a cold-start claim. The host still reports storage `enabled: false`, `driver: disabled`. No corrected deployment exists and no Vercel settings were changed.

## Implemented correction

- Reuse identical fixed-origin weekday pools while keeping the same arithmetic, date-specific events, ranging and fallbacks. Cache only the pure Riyadh-midnight date conversion, with a bounded cache independent of datasets.
- Replace the benchmark's repeated opposing-transfer scan with set membership, seeded with the same existing/locked records and updated after each actual new line. Allocation ordering, calendars and financial constraints are unchanged.
- Reuse serialization of unchanged Dataset fields within one network-forecast request. Every dynamic history/settings projection retains the **exact original Pydantic JSON SHA-256**; no forecast or complete-plan response is cached. Per-series method selection, buffers, full-precision values and provenance remain unchanged.
- Project the main plan/review/scenario-draft response after full replay and private draft persistence. `stock_detail: on_demand` explicitly identifies the omitted stock table and `stock_row_count` reports its full dimension; all actions, summary/cash/service/explanation records remain. The existing scoped evidence service supplies the selected SKU's authoritative 56-day stock at all related locations, needed for donor/receiver traceability. Complete ledgers remain available with `include_stock=true` for verification and remain inside accepted exports. OpenAPI and generated TypeScript were updated reproducibly.
- Preserve exact snapshot/dataset/scenario/action hashes on public evidence. Private evidence additionally validates the expected plan run and returns the review reference, revision and run ID. Deleted/consumed references fail; stale review evidence requires regeneration. The UI loads stock only when requested and retains its request cancellation and review guards.
- Keep the original 10-second, full-dimensional `planning_smoke` assertions intact by requesting the complete ledger explicitly. Add `planning_transport_smoke` as a separate CI gate comparing default compact responses, full replay and deterministic scoped evidence. No assertion, solver budget or failure exit was relaxed.
- Add opt-in `PLANNING_DIAGNOSTICS=1` timing headers and more detailed standalone/container profiling. Fixed phase names contain no inputs or secrets. Nested forecast/buffer/contract timings are inclusive and must not be summed twice. Fresh-process import, sample construction/validation, protection paths, replay, explanations, contract validation, serialization and HTTP first-byte/body timing are recorded separately.
- Add a provider-neutral `PrivateStorage` composition over private blob operations and transactional metadata, including upload sealing, verified parser finalization, ownership/hash/expiry, quotas, durable cleanup tombstones and atomic replacement. Local review mutations now use the same replacement boundary rather than depending on a process lock. Hosted activation remains deliberately disabled; no provider or credentials were available. See [PRIVATE_STORAGE.md](PRIVATE_STORAGE.md) for concrete interfaces, conformance scope, required resources, settings and remaining transport integration.
- Correct the offline policy evaluator to carry transfer acquisition value across weekly origins instead of repricing in-transit units at the donor's later average. Retain received transfer IDs for linked unpaid obligations and respect product active dates. Add daily acquisition-value conservation, including blocked/reserved stock: the next origin book cost aggregates all on-hand units, preventing value creation when unavailable units have a different cost. These changes are confined to the offline evaluator; runtime planning valuation is unchanged.

## Verification status

### Measured bottleneck and correction

The full sample never attempts a joint solve under the retained policy. Baseline Ubuntu/container profiling for **e51af6f** measured full route **11.748 / 9.263 s**, forecast preparation **6.184 / 6.259 s**, benchmark **2.218 / 2.189 s**, independent replay **0.290 / 0.287 s**, explanations **0.090 / 0.091 s** and serialization **0.0245 / 0.0245 s**. First sample preparation was **2.536 s**. Forecast processing and nested benchmark scans dominate computation; solver research would not address this path. Repeated per-series serialization of unchanged Dataset fields was another measured forecast cost (approximately 0.495 s locally before the request-local identity correction).

The baseline hosted request spent **1.570 s** draining its response after the first byte, in addition to **11.446 s** in the engine. The remaining pre-first-byte overhead was not attributed precisely; it must not be called cold initialization without platform evidence. The 16,800-row ledger materially increases transfer volume. The correction removes that table only from the initial decision response, preserving full replay and on-demand evidence.

Comparable serial **local macOS arm64 / Python 3.14.4** component measurements (seconds):

| Component | Before first / repeat | After first / repeat |
|---|---:|---:|
| Complete route, excluding final JSON serialization | 3.994 / 3.257 | 2.824 / 2.042 |
| Sample preparation | 0.750 / cached | 0.748 / cached |
| Forecast preparation | 2.168 / 2.200 | 1.321 / 1.325 |
| Benchmark construction | 0.721 / 0.720 | 0.394 / 0.392 |
| Independent replay (three calls) | 0.130 / 0.106 | 0.130 / 0.104 |
| Explanations | 0.037 / 0.034 | 0.034 / 0.033 |
| Complete JSON serialization | 0.0117 / 0.0113 | 0.0113 / 0.0113 |
| Compact JSON serialization | unavailable | 0.0021 / 0.0021 |

Final first full sample construction/validation split: **0.339 / 0.409 s**. Inclusive forecast details: protection paths **0.00320 s**, buffer calculation **0.00094 s**, per-series result construction **0.00411 s**, all series forecasting **1.186 s**. Unchanged-field serialization/hash work is still included in total forecast preparation; it has not been omitted from timing. Plan contract validation measured **0.000003 s**. Fresh-process API import was **0.212 s** and separate optimizer import **0.232 s**. These are local process measurements, not Vercel cold-instance evidence. No Linux/container runtime is installed here, so there are no corrected container measurements.

### Production HTTP measurements

Single-worker production startup on local port 8020; all requests serial and successful. Forecast smoke preceded these planning checks, so “first” is a request-order label, not a cold sample or instance claim. Engine timings include the complete calculation; HTTP includes transport. Complete-ledger smoke retains its original dimensions, replay, money, response-size, deterministic action/total/explanation and **10-second** assertions.

| Dataset / request | Complete HTTP s | Engine ms | Complete bytes | Default compact HTTP s | Compact bytes |
|---|---:|---:|---:|---:|---:|
| Fixture first | 2.431 | 2,405.5 | 786,692 | 2.400 | 331,544 |
| Fixture repeat | 2.397 | 2,380.7 | 786,692 | 2.397 | 331,543 |
| Full first | 2.193 | 2,094.2 | 3,753,093 | 2.102 | 1,022,713 |
| Full repeat | 2.104 | 2,005.8 | 3,753,092 | 2.042 | 1,022,712 |

Default full transfer is **72.75% smaller** than the approximately 3.75 MB baseline. Complete responses grow only by the explicit presentation metadata. Compact full engine times were **2,012.7 / 1,953.7 ms**; first byte **2.101 / 2.041 s**, body drain approximately **0.00075 / 0.00070 s** over local loopback. Local transfer time does not predict hosted WAN time. Scoped selected-SKU detail retains **280 stock rows** across related locations (approximately **113 kB**) and agrees exactly with full authoritative replay; repeat detail is deterministic. No full ledger is duplicated in scenario summaries.

Fixture retains 24 purchases / 311 movements, commitments **SAR 91,606**, payments **SAR 97,746**. Full retains 31 purchases / 607 movements, commitments **SAR 92,550**, payments **SAR 99,050**. Independent replay and funding reconciliation passed for every request; first/repeat actions, summaries and explanations matched. Both honestly report `feasible_fallback`: fixture challenger `visible_must_stock:time_limit` under the unchanged two-second budget; full `joint_model:not_attempted` under the unchanged zero budget, both selecting the validated benchmark.

### Equivalence, offline audit and external gates

Regression hashes captured from e51af6f match every sample forecast quantity and every policy action, stock/cash/service row and explanation at full precision. All 280 series input identities match the original Pydantic serialization byte-for-byte, including independent dataset mutations. Tests retain missing/censored/future-truth isolation, review conflicts and authoritative accepted exports. Private-provider conformance uses explicit test doubles; actual provider IAM, persistent transactions and signed transport remain unverified.

Fixture and full offline policy reports each ran twice and matched byte-for-byte, including the new acquisition-value conservation evidence. Proposed and benchmark releases remain identical: fixture realized fill **48.0418%**, unmet **9,154**, commitments/payments **32,612 / 19,146 SAR**; full fill **39.8934%**, unmet **62,717**, commitments/payments **32,550 / 19,275 SAR**. No service improvement or savings claim is supported. Unit/transit/value conservation, carried receipt identities and dated unpaid obligations reconcile.

Final local verification passed **197 backend tests** (329.24 s; two existing deprecation warnings), **26 browser tests** (2.9 min), seven explicit policy replay tests, solver smoke, reproducible OpenAPI/TypeScript, production build, dependency checks, Python compilation, workflow YAML/gate checks and `git diff --check`. Commands and harness corrections are recorded in [BUILD_STATUS.md](BUILD_STATUS.md). The local sample runtime gate passes. **Pass 6 remains open:** the exact corrected commit still needs green Ubuntu/container CI and separately authorized canonical deployment with two serial full requests under ten seconds. Hosted own-data additionally needs authorized private objects plus transactional metadata, concrete adapter/transport integration and real-provider lifecycle/isolation/workflow verification. No corrected hosted result is claimed; the e51af6f host remains the measured failing baseline.

---

# Pass 6 release evidence — 19–20 September 2026

Reviewed baseline: `599554c3ad4e44c47b0461eff3fac921318ea606`, initially clean. [GitHub Actions 35461717511](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35461717511), job `105946650205`, completed successfully on Ubuntu 24.04.5: 168 backend tests, 26 browser tests, solver, reproducible contracts, production build, Docker build/start, forecast/planning/scenario smokes, container profiling and private workflow smoke. **Pass 5 is closed for that commit.** These results do not certify the new Pass 6 worktree.

The canonical [public sample application](https://demand-supply-planning-intelligence.vercel.app) was independently verified through Vercel deployment metadata: project `prj_9wUSzLP3zKbvVinWCeNvmyDelVh5`, deployment `dpl_FDjfTcpkSijxKDgpnJRHf5owkojH`, production alias, `iad1`, commit `599554c`. The second `-hahy` project was not treated as canonical. No push, merge, deployment or project-setting change was performed.

## Verdict and release boundaries

- Pass 5: **closed**, based on successful exact-commit CI above.
- Pass 6: local audit and focused correction implemented; **release gate blocked** by hosted full-sample latency, hosted private storage and unverified corrected-commit CI/deployment.
- Public sample demo: working forecast, planning and scenarios verified; **not release-ready against the retained 10-second planning gate**. Full-sample HTTP took 17.022 / 14.929 seconds. Do not market it as meeting that limit.
- Full hosted own-data workflow: **blocked**. The server reports storage disabled, and no private hosted adapter exists. Local upload/review/accept/export/reopen passed; that is a different environment.

## Calculation trace

Reproduce against the single-worker production process:

```sh
.venv/bin/python -m scripts.release_trace --url http://127.0.0.1:8012 --output artifacts/pass6-local-trace.json
.venv/bin/python -m scripts.release_trace --url https://demand-supply-planning-intelligence.vercel.app --output artifacts/pass6-hosted-trace.json
```

The trace uses real HTTP results, checks action/cash arithmetic, and checks the accepted XLSX and portable snapshot locally. Hosted storage absence is explicitly reported; review is not attempted there. Full raw results and request timings remain in the ignored `artifacts/pass6-*` files. The scripts fail nonzero on request, malformed-response or reconciliation errors.

**Forecast:** fixture SKU001/S1, planning date 2026-09-14. The unchanged engine filters observations by strict availability before the Riyadh midnight origin; previous censor estimates never become scored actuals. Eight earlier disjoint selection origins precede the held-out period; 7 complete windows and 223/224 scored days are available. Seasonal-naive quantity MAE is 10.4285714; selected recency-weighted MAE is 7.4761905. API improvement remains 28.3105023%; displayed MAEs 10.4 / 7.5 produce the displayed 28%. Selected pooled bias is +0.1666667 units / +0.0079139%, displayed `<0.1%`. The held-out final check has 27/28 known days, so complete-period quantity MAE remains unavailable; selected pooled WAPE is 16.2681%, versus baseline 23.9130%. It does not select the method. The refitted visible forecast is 281.0666667 units, displayed 281.1. Trace: `forecasting/engine.py` → `ForecastResult` → `Demand.tsx` / `Evaluation.tsx`; API-backed browser assertions cover product/store changes and recalculation.

**Purchase:** `P-OFFER008-0`, 130 units SKU008 at SAR 11, total **SAR 1,430**. OFFER008 is valid 2025-07-21 through 2026-11-08, case 10, MOQ 20, supplier minimum SAR 500, every-day order/dispatch calendars, 14-day lead time. Order and dispatch 14 September; receipt at DC on 28 September. The S3 evidence target is the earliest reachable store shortage on 2 October; it is a demand context, not a dedicated purchase destination. DC inventory is pooled and every allocation is independently replayed. No purchase-to-store reservation is fabricated.

**Store transfer:** `T-SKU001-S2-S1-0`, 10 units. On 14 September S2 opens with 320, receives zero, serves 12, dispatches 10 and closes at **298**, above its origin-known next-seven-day reserve of **84**. Two-day lane transit places the 10-unit receipt at S1 on 16 September. S1 opens with 68.6, receives 10, serves 8.7 and closes at 69.9. The `S2-S1-2026-09-14` fee group has one **SAR 20** payment regardless of SKU count. Transfer changes stock location and adds a movement expense; it creates no purchase commitment.

**Cash:** the purchase above deposits **SAR 715 on 14 September**, with **SAR 715 balance on 28 October**, 30 days after receipt. Week 14 September has SAR 1,430 commitments against 1,500 authority, leaving 70. Payments are 715 deposit + 680 grouped movement fees = **1,395**, leaving **2,605** against the 4,000 ceiling; transfer headroom is 120 against an 800 allowance. Whole-plan commitments **91,606**, payments **97,746**, movement expense **2,740**, and opening unpaid obligations **3,400** reconcile: 91,606 + 2,740 + 3,400 = 97,746. Payment headroom is an allowance, not a bank-balance forecast. Day-56 inventory value **18,303.42** is a separate stock measure; projected visible fill **52.7191%** and unmet **7,567.4417 units** are separate service measures.

**Scenario:** increase first-week commitment allowance from 1,500 to 2,000 and payment ceiling from 4,000 to 4,500. Original and frozen actions/outcomes are identical and feasible. The validated replan has +50 visible fulfilled units, −50 visible unmet units, +0.312397 percentage points fill, −50 total commitments, −30 total payments, +20 movement expense and −540.74 ending inventory value, but **+4.8667 tail unmet units**. All deltas equal authoritative after-minus-before fields. Increased authority changes action timing; it is not proof of commercial savings. The separate combined promotion/disruption/commitment smoke retains unavailable metrics/deltas for infeasible frozen actions. Same changed-assumption hashes are required for frozen and replanned policies.

**Review/export:** change the 130-unit purchase to **120 units**. Decision marks the old plan stale; regeneration creates a distinct replacement reference and independently validated result; acceptance is possible only after the current result loads and remaining shortfalls are acknowledged. Accepted line value is **SAR 1,320**, identical in API, portable snapshot and PurchaseActions XLSX. Revised total commitments **91,496**, payments **97,696**, movement expense **2,800**, ending inventory value **18,257.82** and projected unmet **7,577.4417** match exported Summary values. Existing workbook floats are lossless decimal text; the trace parses that documented representation instead of treating text as a numeric-cell defect. Action identities and canonical provenance survive regeneration/export; reopening is read-only and a new draft requires explicit regeneration. No order is executed.

## Offline weekly policy evaluation

This missing build-plan evidence is now implemented in `scripts/policy_replay.py`, outside the runtime application. Reproduce both datasets:

```sh
.venv/bin/python -m scripts.policy_replay --size fixture --output artifacts/pass6-policy-fixture.json
.venv/bin/python -m scripts.policy_replay --size full --output artifacts/pass6-policy-full.json
```

Dataset IDs `sample-v1-fixture-97` and `sample-v1-full-97`; seed 97. Four weekly origins **14, 21, 28 September and 5 October 2026** evaluate **14 September–11 October**, entirely in the generator's withheld future period. Each origin retains the 56-day model, 28-day visible window and seven-day release window. Both policies start with the same runtime input snapshot. After each release, each policy carries its own realized stock, transit, confirmed orders, received IDs and outstanding installments into the next origin. Only realized *sales* become observations with next-day 01:00 Riyadh availability; unmet oracle demand is never inserted into forecast history. A stockout remains censored, distinct from a known zero.

The evaluator fixes three extra funding weeks **before** evaluation at the last declared caps (15,000 commitment / 18,000 payment / 800 transfer), solely to cover later origins' 90-day payment ledgers. Existing dates, offers, supplier capacity and all forecasts remain unchanged. No future labels select a method, buffer or action. No tuning on this period was performed. Generated truth hash, input hashes, actions, cash headrooms and weekly results are saved for reproduction.

Complete origin policies first pass the separate production feasibility replay. The realized execution simulator then receives withheld demand: receipt → serve → dispatch → close. It conserves on-hand plus transit and checks receiving space and dated cash. If observed stock cannot support a new transfer while preserving the **origin forecast** donor reserve, the whole transfer is cancelled and reported; it never consults tomorrow's truth to choose the dispatch. No cancellations occurred in these measured samples. The simulator is an evaluation assumption, not an order execution system.

| 28-day realized measure | Fixture, each policy | Full sample, each policy |
|---|---:|---:|
| True demand, units | 17,618 | 104,343 |
| Fulfilled units | 8,464 | 41,626 |
| Unmet units | 9,154 | 62,717 |
| Unit fill | 48.0418% | 39.8934% |
| Average daily closing network inventory incl. transit, units | 1,858.4643 | 9,211.8571 |
| New purchase commitments, SAR | 32,612 | 32,550 |
| Payments within evaluation dates, SAR | 19,146 | 19,275 |
| Movement expense, included in payments, SAR | 1,640 | 1,800 |
| Remaining installments after evaluation, SAR | 18,506 | 18,475 |
| Dated funding, stock conservation, independent origin replay | Passed | Passed |

**Proposed and benchmark releases are identical at every origin.** Both datasets were run twice; complete JSON reports matched byte-for-byte, including actions, input hashes, cash and explanations of execution deviations. There is no measured proposed-policy advantage. Funding feasibility coexists with substantial unmet demand, especially in the full sample. Paid-plus-outstanding reconciles to new commitments + movement fees + initial SAR 3,400 obligations. Inventory is reported in base units, not as a cash saving. The four-week ending boundary does not erase remaining payables or penalize/credit future service.

Five regression tests cover hand-calculated realized service/inventory, censored-history carry-forward, future-truth isolation, deposit/balance/received-ID carry-forward, whole-line transfer cancellation and missing-oracle failure. These complement the existing independent replay, leakage, solver and review tests; no production calculation engine or contract changed.

## Hosted and local runtime evidence

First/repeat below means first/repeat in the audit process. It does **not** establish a fresh Vercel instance or cold import. All planning responses passed independent replay, financial checks, exact action/summary/explanation repeat comparison and the 4,500,000-byte limit. All were honestly labeled `feasible_fallback`; the fixture challenger kept two seconds and the full challenger stayed unattempted.

| Environment | Fixture first / repeat, HTTP s | Full first / repeat, HTTP s | Largest response, bytes |
|---|---:|---:|---:|
| Local macOS, production port 8012 | 2.739 / 2.549 | 3.273 / 3.255 | 3,753,044 |
| Exact baseline CI, Ubuntu Docker | 3.534 / 3.560 | 9.179 / 9.268 | 3,753,043 |
| Hosted canonical Vercel | 8.230 / 5.473 | **17.022 / 14.929 — FAIL 10 s gate** | 3,753,044 |

Hosted engine times: fixture 3,998.0 / 4,096.9 ms; full 11,775.5 / 11,949.9 ms. The full challenger used zero seconds, so its solve cannot explain the overrun. The exact-commit container profile isolates full first/repeat forecast work at **6.188 / 6.273 s**, benchmark at **2.172 / 2.149 s**, independent replay at **0.280 / 0.275 s**, explanation at **0.090 / 0.090 s**, serialization at **0.023 / 0.023 s**; first input creation adds **2.496 s**. The complete cold container route is **11.648 s** despite passing warm HTTP smoke. Local profile likewise shows forecasts dominate, but cannot substitute for hosted per-stage profiling. No runtime gate, solver budget, sample size or objective was changed. Target-host phase/memory measurement and a focused forecast-preparation performance correction remain required; neither cache entire plans nor reopen exact-optimizer research.

Hosted forecast first/repeat: fixture **0.687 / 0.636 s**, full **5.244 / 1.135 s**. Live selected results, held-out coverage and 56-day quantities passed. Hosted combined scenario first/repeat: fixture **6.793 / 6.363 s** on the completed serial run; full **20.283 / 18.141 s**, largest comparison **921,568 bytes**. Full scoped detail **12.395 s / 113,556 bytes**; full future-path delay comparison **27.489 s / 1,035,200 bytes**. All serial scenario gates passed below 30 seconds and 4.5 MB. The separate funding/payment-ceiling trace passed at **6.137 s / 348,988 bytes** with the exact deltas above.

An overlapping hosted calculation received explicit HTTP 429; the initial scenario script failed nonzero. A serial rerun passed. This is evidence of the documented single-instance busy gate, not an invisible retry or relaxed assertion. Vercel runtime-error lookup returned no error clusters in the selected one-hour range; that does not prove zero errors outside that range or establish memory consumption.

Browser inspection verified canonical initial load, relative same-domain session/catalog/forecast/planning/capture/detail requests, real purchase evidence, and 390px mobile Plan Review with all four navigation controls in bounds and no page overflow. Captured screenshots are real browser output, not mockups. Agent-browser sessions later lost their page (`about:blank`); these were not counted as passing checks. The final single-session `scripts/hosted_browser.mjs` run **passed** desktop demand/plan, full forecast product/store/recalculate, actual store-transfer evidence, mobile combined scenario controls, baseline reset, mobile/desktop Data navigation, disabled uploads and blank-template download. All observed API responses were same-domain HTTP 200; page/console errors were empty. Harness setup errors were corrected to use accessible combobox roles and funding-date identities before the successful run. This is actual hosted browser evidence for 599554c, not local UI evidence for the new correction.

## Hosted own-data prerequisite

Actual hosted `GET /api/workflow/session`: **enabled false**, driver disabled. Only `LocalStorage` exists in `backend/app/data/storage.py`; `configuration()` deliberately rejects it on Vercel. The existing `Storage`, `ObjectReference` and `UploadAuthorization` types are provider-neutral preparation, not a completed adapter. No authorized private provider/resource/access was found or provisioned.

Implementation still required: select an authorized private object store; add narrowly scoped upload authorization and verified upload finalization; bind opaque references to server-verified session owner/type/size/content/hash/expiry; store review revisions with atomic replacement semantics across instances; implement private download transport for large accepted files; implement deletion, expiry and abandoned-upload cleanup. Extend the existing storage conformance tests against that real provider, including cross-session rejection, expired/unknown refs, content and archive limits, unsuccessful uploads and concurrent revision races. Only then change the fail-closed configuration and verify full hosted import → plan/scenarios → edit/regenerate → accept → download → reopen/new-draft. The current protocol and bounded implementation checklist are retained; choosing and fabricating an unconfigured provider would not resolve this gate. Browser Dataset JSON, public URLs and serverless temp files are prohibited substitutes.

Local synthetic own-data smoke passed fixture/full parsing, deliberately wrong browser size labels, authoritative provenance, regenerated evidence, final acceptance, financial reconciliation, deterministic snapshot bytes, unique external IDs, portable read-only reopen and session deletion. Fixture upload/plan/regenerate/accept/export: **1.397 / 2.762 / 2.777 / 0.854 / 0.113 s**. Full: **10.797 / 5.790 / 6.169 / 6.810 / 0.863 s**; full XLSX **125,251 bytes**, portable **932,865 compressed / 21,292,412 expanded bytes**. These are local file operations. No local Docker executable exists; Docker workflow evidence belongs only to baseline CI.

## Three-minute demo and portfolio copy

Use the fixture for a short public sample demonstration, disclosing the outstanding runtime gate. Use the local production application for review/export.

1. **0:00–0:35:** Demand Review, SKU001/S1. Show live recalculation, 281.1 expected units, 10.4 → 7.5 MAE and 28% displayed improvement. Open the held-out check: only 27/28 known days; future truth is unavailable to the planner.
2. **0:35–1:15:** Plan Review. Show the validated fallback label and 52.7% projected fill, then the 130-unit SKU008 purchase. Trace SAR 715 deposit and 715 later balance. Show the SKU001 S2→S1 transfer and its single grouped fee. Explain that funding-feasible does not mean every service target is met.
3. **1:15–2:00:** Scenarios. Raise first-week commitment/payment allowances to 2,000/4,500. Original preserves the old assumptions, frozen keeps exact actions, replan uses the same changed allowances. Show +50 visible served units alongside slightly worse tail unmet demand. Do not describe this synthetic comparison as customer savings.
4. **2:00–3:00, locally:** Edit SKU008 from 130 to 120. Show stale state and disabled acceptance/export; regenerate, acknowledge shortfalls and accept. Download XLSX and snapshot, reopen read-only, and identify the explicit new-draft path. No order is sent. On the public host, show the disabled own-data explanation instead of claiming this final step works there.

Portfolio copy: “Built an independent retail planning MVP for one DC and four stores, combining evaluated weekday forecasts, constrained purchasing and allocation, dated cash commitments, disruption scenarios and an auditable local review/export workflow. The full synthetic sample covers 60 SKUs and 240 store series. Every proposed plan is independently replayed for stock and funding feasibility. Four-week withheld-demand evaluation found identical proposed and benchmark releases, with 39.9% simulated full-sample fill under tight funding—evidence of an explicit cash/service trade-off, not a claimed optimization gain. Public sample APIs have been exercised; hosted latency and private own-data storage remain release dependencies.”

Disclosures: synthetic Saudi retail inputs, SAR conventions and Riyadh business dates; simulated/forecast service, no customer deployment, executed orders, proven commercial savings or global optimality. Four-week evaluation, one seed and one synthetic setting do not establish generalization. The full live challenger is skipped; a validated fallback can equal the benchmark and retain shortages. Temporary local sessions are not accounts or durable history; accepted files must be downloaded before expiry/reset/restart. Hosted memory and genuine cold starts remain unverified. Scope stays frozen: no new dashboards, scenario types, AI narration, integrations or history system.
