# Current build status — 24 September 2026

**Public sample status: BLOCKED.** Local cleanup verification passes, but the corrected closure patch is not published. The canonical Vercel alias still serves `27eb86c890584102d8fdbfa4f456ba6b926c143e`, while the attempted Prompt 3 deployment for `2ec1c06a16f6f0f028c646e3804b802f48a68ee5` failed before build because its tool-only `pyproject.toml` made `uv lock` require a missing PEP 621 `[project]` table. The working-tree correction removes that manifest and retains the cache rules in `vercel.json`.

## Candidate identity

| Item | Current evidence |
|---|---|
| Reviewed base SHA | `2ec1c06a16f6f0f028c646e3804b802f48a68ee5` (`origin/main` at inspection) |
| Closure patch | Uncommitted: deployment-manifest correction, focused regression update, compact documentation and history archive |
| Data | `sample-v2-fixture-97` and `sample-v2-full-97`; seed 97; planning date 2026-09-14 |
| Local runtimes | Python 3.14.4; Node 25.6.1; npm 11.9.0 |
| Authoritative runtime target | Python 3.14 and Node 24 in `.github/workflows/verify.yml`; exact corrected-candidate CI is pending publication |
| Prior-base CI | [run 35999897102](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35999897102), Python 3.14.7 / Node 24.20.0, failed: the backend phase ran before the frontend build and the new static test assumed `frontend/dist` already existed (233 passed, 1 failed, 10 subtests). The closure patch makes that test phase-aware and repeats it explicitly after the production build. |

`git diff --check` passes. Inspect the final uncommitted file list with `git status --short` and the patch with `git diff --stat && git diff` before publication.

## Verification matrix

| Gate | Result |
|---|---|
| Complete backend suite | Local exact-source content passed 234 tests plus 10 subtests; the only initial local failure was the sandbox denying a localhost bind, and the isolated test passed with local-bind permission. Prior-base CI failed only because its clean checkout had no prebuilt frontend; the corrected test skips that integration in the pre-build phase and the workflow reruns it after build. Exact corrected-candidate CI remains required. |
| Deployment correction regression | `python -m pytest -q backend/tests/test_static_delivery.py`: **4 passed**, two upstream deprecation warnings, 0.31 s. |
| Solver and contracts | `python -m scripts.solver_smoke` passed on the reviewed base. `python -m scripts.export_contracts` followed by `git diff --exit-code -- frontend/src/contracts.generated.ts` passed after the correction. |
| Frontend | Production build passed; complete Playwright suite **26/26 passed** on the exact reviewed source. The closure patch does not change frontend code. |
| Browser sanity | Local production-style page returned 200 at 390×844 with meaningful content, Plan Review present, no error overlay and no captured page/console errors. |
| Forecast smoke | Fixture first/repeat HTTP **0.030 / 0.029 s**, engine **15.8 / 14.6 ms**. Full first/repeat HTTP **0.790 / 0.176 s**, engine **88.5 / 89.3 ms**. These are first measured requests in one local process, not forced-cold evidence. |
| Planning smoke | Fixture first/repeat HTTP **2.377 / 2.324 s**, engine **2348.2 / 2306.9 ms**, ~827 KB complete response, 24 purchases/311 movements. Full first/repeat HTTP **2.446 / 1.808 s**, engine **2343.7 / 1700.0 ms**, ~4.071 MB complete response, 47 purchases/723 movements. All were `feasible_fallback`, independently replayed, deterministic on repeat and below the 10 s / 4.5 MB gates. |
| Compact and lazy evidence | Fixture compact **371,874 B** versus complete **827,021 B**; full compact **1,332,745 B** versus complete **4,070,541 B**. Compact/full actions, totals and explanations matched; requested detail was deterministic and authoritative. |
| Scenario smoke | Fixture combined scenario first/repeat HTTP **2.494 / 2.405 s**; full **2.608 / 2.745 s**. Frozen plans were honestly `invalid_plan`; replans were `feasible_fallback`; dated failures, all four control families, arithmetic, financial reconciliation and repeat determinism passed. |
| Release trace | Reconciled. Forecast 0.029 s/41,650 B; fixture plan 2.348 s/827,064 B; capture 0.068 s/181,305 B; compare 2.423 s/390,069 B. Quantity edit, stale state, regeneration, acceptance, workbook and portable snapshot all matched. |
| Own-data lifecycle | Fixture/full synthetic upload → plan → edit → regenerate → accept → export → reopen/reset passed. Full: upload 9.255 s, plan 3.539 s, review 3.738 s, accept 3.726 s, export 0.597 s; provenance and snapshots matched. |
| Policy replay | `sample-v2` fixture/full passed four weekly releases with no truth leakage, funding failures or cancelled movements. Proposed and benchmark actions were equal. Fixture: 48.04% fill, 9,154 unmet, SAR 32,612 commitments / 19,146 paid / 18,506 future payables. Full: 43.22% fill, 59,241 unmet, SAR 77,736 commitments / 42,068 paid / 41,068 future payables. |
| Dependency consistency/security | `python -m pip check`: no broken requirements. Python vulnerability scanner unavailable locally. `npm audit --omit=dev` and full `npm audit`: **0 vulnerabilities**. No dependency changes made. |
| Compilation/hygiene | `python -m compileall -q backend scripts` and `git diff --check` passed. |
| Docker / exact corrected CI | Docker CLI unavailable locally. Must be proven by the exact corrected-candidate CI after publication. |
| Hosted candidate | **Failed/pending.** See [DEPLOYMENT.md](DEPLOYMENT.md). Static/CDN behavior, current desktop/mobile walkthrough, canonical latency and two consecutive production probes are not proven for the corrected candidate. |

## Exact commands

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest -q backend/tests/test_static_delivery.py
.venv/bin/python -m scripts.solver_smoke
.venv/bin/python -m scripts.export_contracts
git diff --exit-code -- frontend/src/contracts.generated.ts
npm --prefix frontend run build
CHROME_PATH='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' npm --prefix frontend run test:e2e
./scripts/start.sh
.venv/bin/python -m scripts.smoke
.venv/bin/python -m scripts.planning_smoke
.venv/bin/python -m scripts.planning_transport_smoke
.venv/bin/python -m scripts.scenario_smoke
.venv/bin/python -m scripts.workflow_smoke
.venv/bin/python -m scripts.release_trace --output artifacts/calculation-trace.json
.venv/bin/python -m scripts.policy_replay --size fixture --output artifacts/policy-fixture.json
.venv/bin/python -m scripts.policy_replay --size full --output artifacts/policy-full.json
.venv/bin/python -m compileall -q backend scripts
.venv/bin/python -m pip check
npm --prefix frontend audit --omit=dev --audit-level=low
npm --prefix frontend audit --audit-level=low
git diff --check
```

## Remaining closure action

Through the authorized release process, commit and publish this closure patch, then require:

1. successful Python 3.14 / Node 24 CI for that exact SHA, including Docker and solver-in-container;
2. a READY Vercel production deployment whose source SHA matches it;
3. canonical root/asset/API routing and disabled-storage browser verification on desktop and mobile;
4. the established production-latency workflow twice consecutively on the unchanged canonical deployment.

Until those checks pass, do not describe the Prompt 1–4 public sample as closed. Historical chronological logs are retained in [docs/history](history/README.md); calculation and workflow specifications remain authoritative in the linked methodology documents.
