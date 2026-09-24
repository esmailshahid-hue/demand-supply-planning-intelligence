# Bounded MVP correction — 24 September 2026

Status: local correction verified and ready for review/commit; **exact corrected-commit CI and hosted release proof remain pending publication**. Nothing was committed, pushed, merged or deployed, and no Vercel project settings/connections were changed.

## Identities and root causes

- Reviewed base: `905458262e68275e3b5339061a0932e5d3df6ed8`; the worktree was clean at the start.
- [GitHub run 36002190655](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/36002190655): 233 backend tests + 10 subtests passed, one pre-build static skip; 4 post-build static tests passed; 25 browser tests passed / one failed. The 1440px navigation test exposed review loading owned by an unmounted screen. Docker was skipped; later connection-refused smokes were workflow dependency noise.
- Current canonical Vercel deployment: READY `dpl_7AwN5kDSG3GCsfVW1HWgwniB8Y4A`, immutable host `demand-supply-planning-intelligence-y734osye3.vercel.app`, source `9054582`, production `iad1`. It is not the unpublished correction.
- Historical `2ec1c06` deployment failed at `uv lock` because its tool-only manifest lacked `[project]`; that manifest was already removed in the reviewed base. The old `27eb86c` alias statement is obsolete.
- Existing global middleware prevented automatic application-static promotion. Canonical root/JS still expose Python timing despite cache headers. The corrected build uses root `public/`, not a middleware-wrapped application mount.
- Full v2 funding/stock/lot assumptions still yielded 43.22% withheld fill and 723 movements. Data-only v3 calibration now gives a healthier constrained example; no planning algorithm or forecast selection logic changed.

## Changes

| Area | Files / correction |
|---|---|
| Persistent review owner | `frontend/src/useReviewState.ts`, `App.tsx`, `PlanReview.tsx`, `ReviewControls.tsx`: one review request/state owner above screen mounts, derived safety gate, visible cross-screen retry, abandoned-response suppression, preserved mutation/recovery locks. Scenario rendering also waits for unresolved restored baselines. Invalid calculations retain “Not executable.” |
| Browser regressions | `frontend/e2e/review-readiness.spec.ts`: delayed navigation, failed-request retry, dataset replacement and public no-review plans. `pass5-state.spec.ts`: explicitly reject a below-MOQ v3 edit, then verify a genuine rejected-action mutation changes the captured plan. No timeout increases or sleeps. |
| CI dependency | `.github/workflows/verify.yml`: named `docker_health` outcome gates every Docker-dependent smoke. `!cancelled()` permits independent checks after a planning assertion failure only with a healthy server. No `continue-on-error`. Builds and checks the CDN artifact explicitly. |
| Static delivery | `frontend/package.json`, `vercel.json`, `.gitignore`, `backend/tests/test_static_delivery.py`; root public build, exact root rewrite, immutable assets, HTML revalidation, 60-second API limit unchanged, no Python manifest. `backend/app/main.py` changes only its module description. |
| Calibration and pins | `backend/app/data/sample.py`, `test_sample_assumptions.py`, `test_performance_equivalence.py`, `test_planning.py`: v3 full inputs, deliberate refreshed full hashes, unchanged fixture policy/forecast quantities/history/truth, binding-constraint/response-size checks. |
| Evaluation / hosted checks | `scripts/policy_replay.py` adds the same-simulator no-action comparator and per-series unmet reporting; action execution rules unchanged. `static_delivery_smoke.py` rejects Python timing on root/assets. `hosted_browser.mjs` verifies Plan-first loading and explicitly selects full planning. |
| Documentation | README, this status, DEPLOYMENT, PLANNING, SCENARIOS and new SAMPLE_CALIBRATION distinguish current evidence, old history and pending release gates. |

## Verification

Local runtimes: Python **3.14.4**, Node **25.6.1**, npm **11.9.0**. Exact-SHA CI uses Python 3.14 / Node 24 (base run: Python 3.14.7 / Node 24.21.0). Local checks are not a claim about Ubuntu/Docker or hosted cold starts.

| Gate | Evidence |
|---|---|
| Focused review race, run first | Initial three timing/error/replacement cases repeated three times: **9/9 passed**, 39.8 s. Final four-case suite (including public no-review ID), repeated three times on frozen v3: **12/12 passed**, 44.1 s. No arbitrary sleeps, timeouts increased, forced Plan Review revisit or removed gate. |
| Complete backend | **235 passed + 10 subtests**, 461.14 s, two existing upstream deprecation warnings. Initial run: 234 passed + 10 subtests, one failure solely because sandbox denied the curl test's localhost bind; complete permitted-localhost rerun passes. Final sample/size/static checks also pass **10/10** after tightening the complete-response ceiling to the actual previous byte count. |
| Complete browser | **30/30 passed**, final rebuilt source including restored-baseline render guard, 3.9 min. Original 1440px failure passes, as do stale/recovery locks, reset, acceptance/export and mobile flows. An earlier run found the below-MOQ test assumption and invalid-result banner priority; both corrected and the complete suite rerun. |
| Static builds/routes | Normal production and `build:vercel` pass; public/dist shell and assets byte-identical. **5 static tests pass**. JS ~309.51 KB / 93.28 KB gzip; no API/private files in public output. Local headers are not CDN execution proof. |
| Solver/contracts | SciPy 1.18.1 import 0.357 s; cold/warm HiGHS integer smoke passes. OpenAPI export + TypeScript generation reproducible; generated TypeScript has no diff. |
| Forecast HTTP | Fixture first/repeat **0.059 / 0.053 s**, engine 29.2 / 28.3 ms; full **1.702 / 0.327 s**, engine 165.9 / 165.1 ms. These are measured requests, not forced-cold proof. |
| Planning HTTP | See table below. Every request passes the unchanged 10-second and 4.5 MB gates, independently replays with no failures, reconciles money and matches repeated actions/totals/explanations. |
| Compact/lazy evidence | Fixture compact **371,874 B**, complete ~827,023 B. Full compact **1,192,244 B**, complete **4,050,395 B**, below previous **4,070,541 B**; complete-size regression pins that previous ceiling. All scoped ledgers/provenance match the complete authority and repeat deterministically. Full detail **98,482 B**, first/repeat **1.568 / 1.386 s**. |
| Scenarios | Fixture combined shock first/repeat **2.942 / 2.908 s**; full **4.223 / 3.794 s**. Frozen is honestly invalid; replan is feasible fallback. B-dependent deltas unavailable; C − A remains numeric and reconciles. Future-path delay and partial first-two-week tighter funds pass without mutating the baseline. Full combined replan: **160 purchases / 536 movements**, SAR **791,400 commitments / 796,220 payments**. |
| Local own-data | Fixture and full upload → plan → exact action lock → regenerate → accept → workbook/snapshot export → read-only reopen → reset pass with exact provenance, deterministic snapshots and reconciled finance. Full HTTP: upload **14.681 s**, plan **4.104 s**, review **4.073 s**, acceptance **5.755 s**, export **1.030 s**. Full accepted snapshot 1,017,419 compressed B. This does not enable hosted storage. |
| Calculation/review trace | Live fixture capture/compare and 130 → 120-unit purchase edit → stale → regenerate → accept → both exports reconcile. Compare **2.404 s / 390,070 B**. Funding expansion to SAR 2,000 / 4,500: B − A zero; C − B = C − A **+0.312397 fill points, −50 unmet units, −SAR 50 commitments, −SAR 30 payments**, +SAR 20 movement fees. Every delta field equals the corresponding summary subtraction. |
| Policy replay | Fixture/full four weekly releases completed. Same proposed/benchmark actions; all origins independently feasible; dated cash and stock/value conservation pass. See realized table and disclosed cancellations below. |
| Dependencies/hygiene | `pip check` passes; production and full `npm audit` each report **0 vulnerabilities**; npm dependency tree resolves. Python vulnerability scanner unavailable (not claimed clean). Python compilation, JS script syntax and `git diff --check` pass. No dependency versions changed. |
| Docker / corrected CI | Docker CLI unavailable locally; container build/start/solver/all smokes and exact corrected-SHA workflow pending publication. |
| Corrected hosted deployment | Pending. Current base is READY, but corrected CDN execution, cold loading, canonical source SHA, mobile/desktop hosted flow and consecutive production probes are not yet proven. |

### Initial 56-day plans (28-day service window)

| Metric | Fixture | Full v3 |
|---|---:|---:|
| Purchases / movements | 24 / 311 | 174 / 559 |
| First / repeat HTTP | 2.535 / 2.745 s | 3.379 / 1.978 s |
| First / repeat engine | 2486.8 / 2712.8 ms | 3156.8 / 1781.9 ms |
| Complete bytes, first / repeat | 827,022 / 827,021 | 4,050,395 / 4,050,396 |
| Commitments / payments, SAR | 91,606 / 97,746 | 892,200 / 897,040 |
| Min commitment / payment / transfer headroom, SAR | 0 / 14 / 120 | 1,000 / 109,100 / 1,000 |
| Status | feasible_fallback | feasible_fallback |
| Challenger / fallback stages | visible_must_stock:time_limit; independent_fallback:benchmark | joint_model:not_attempted; independent_fallback:benchmark |

Both policies match their deterministic benchmark; neither claims optimality or improvement over that identical benchmark. Fixture actions/finance are unchanged. Full modeled visible fill **86.16%** versus **49.28%** no action; 133 / 240 series have visible shortage (v2: 235). Commitment minima, initial supplier unavailability and lane capacity restrict the full plan even though payment headroom is now comfortable. See the [frozen calibration record](SAMPLE_CALIBRATION.md).

### Four-origin withheld execution (14 September–11 October)

| Metric | Fixture | Full v3 |
|---|---:|---:|
| Proposed / no-action fill | 48.0418% / 19.6674% | **85.7451% / 48.2744%** |
| Proposed fulfilled / demand | 8,464 / 17,618 | 89,469 / 104,343 |
| Proposed unmet | 9,154 | **14,874** (v2: 59,241) |
| Released purchases / executed movements | 8 / 187 | 94 / 271 |
| Commitments / paid / future payables, SAR | 32,612 / 19,146 / 18,506 | 474,600 / 239,220 / 239,500 |
| Movement expense, SAR | 1,640 | 720 |
| Observed-stock cancellations | 0 | **2**, disclosed, not counted as executed |

Full weekly fill: **97.36 / 95.67 / 65.77 / 84.09%**. Week three accounts for **8,883 unmet units (59.7%)** as store cover runs out. Some realized shortage remains in 144/240 series: improved and period-concentrated, not eliminated. Two store-to-store lines fail the simulator's observed-stock/origin-reserve guard; [SAMPLE_CALIBRATION](SAMPLE_CALIBRATION.md) records their identities. Proposed and benchmark remain identical, with no truth-based dispatch decisions. Full input hash was frozen before evaluation and never retuned afterward. Larger opening inventory and funding are explicit assumptions, not algorithmic gains or commercial savings.

Local evidence artifacts (ignored, reproducible): `artifacts/final-fixture-policy.json`, `artifacts/final-full-policy.json`, `artifacts/final-calculation-trace.json`, desktop/mobile browser screenshots. Truth hashes in policy files use normal JSON spacing; pinned test truth hashes use compact separators. Both formats are unchanged from their corresponding prior evidence.

## Reproduction and release handoff

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m scripts.solver_smoke
.venv/bin/python -m scripts.export_contracts
npm --prefix frontend run generate:types
git diff --exit-code -- frontend/src/contracts.generated.ts
npm --prefix frontend run build
npm --prefix frontend run build:vercel
.venv/bin/python -m pytest -q backend/tests/test_static_delivery.py
CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e
./scripts/start.sh
# Separate terminal, after health succeeds:
.venv/bin/python -m scripts.smoke
.venv/bin/python -m scripts.planning_smoke
.venv/bin/python -m scripts.planning_transport_smoke
.venv/bin/python -m scripts.scenario_smoke
.venv/bin/python -m scripts.workflow_smoke
.venv/bin/python -m scripts.release_trace --output artifacts/final-calculation-trace.json
.venv/bin/python -m scripts.policy_replay --size fixture --output artifacts/final-fixture-policy.json
.venv/bin/python -m scripts.policy_replay --size full --output artifacts/final-full-policy.json
.venv/bin/python -m pip check
npm --prefix frontend audit --omit=dev
npm --prefix frontend audit
.venv/bin/python -m compileall -q backend scripts
git diff --check
```

The API measurements above use a dedicated local server on port 8001 with `--url http://127.0.0.1:8001`; browser verification uses port 8000. Requests within each smoke are serial; other local test processes may be running, so times are not isolated-machine benchmarks.

Manual next steps: review/commit/publish the correction; require green exact-SHA CI including Docker; verify canonical READY source SHA; run the static/header/cold-load and hosted browser checks plus two consecutive production probes. Separately disconnect the unused `-hahy` project's Git integration only after confirming its ID/domains. Do not change the canonical project's settings. Exact deployment identities, probe commands and cautious optional duplicate deletion are in [DEPLOYMENT.md](DEPLOYMENT.md). Historical records remain in [history](history/README.md).
