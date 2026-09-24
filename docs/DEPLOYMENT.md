# Current deployment status — 24 September 2026

**Status: BLOCKED for Prompt 4 closure.** The public URL works, but it is not the reviewed Prompt 3 candidate or the local closure patch.

## Actual production identity

| Item | Observed value |
|---|---|
| Canonical URL | [demand-supply-planning-intelligence.vercel.app](https://demand-supply-planning-intelligence.vercel.app) |
| Deployment | `dpl_HQDadUAeNA8tyz9Ydh6eFFG85zmb` |
| Immutable URL | [demand-supply-planning-intelligence-6gfzoc1na.vercel.app](https://demand-supply-planning-intelligence-6gfzoc1na.vercel.app) |
| Source SHA | `27eb86c890584102d8fdbfa4f456ba6b926c143e` |
| State / target / region | READY / production / `iad1` |

Vercel resolved the attempted Prompt 3 production deployment as:

| Item | Observed value |
|---|---|
| Deployment | `dpl_99NuyddNXx6PnGL5r6fQcZkKsJCM` |
| Source SHA | `2ec1c06a16f6f0f028c646e3804b802f48a68ee5` |
| State / target / region | ERROR / production / `iad1` |
| Error | `uv lock` rejected the tool-only `pyproject.toml`: no PEP 621 `[project]` table |

The local correction removes that incomplete manifest. Public shell and asset cache headers remain declared in `vercel.json`, and FastAPI retains its own equivalent headers. This correction is not yet committed or deployed.

[Prior-base CI run 35999897102](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35999897102) also failed because its backend phase ran before `frontend/dist` existed. The local correction makes the static integration test phase-aware and repeats it explicitly after the production build. The downstream connection-refused smoke failures in that run were consequences of the stopped pipeline, not production probe results.

## Routing contract

- `/` serves the compiled React shell and must revalidate.
- `/assets/<content-hash>` serves immutable compiled assets.
- `/api/*`, `/docs` and `/openapi.json` remain Python application routes.
- Missing API and asset paths return 404; the SPA must not swallow them.
- Hosted workbook upload, stored reviews and accepted-file downloads remain disabled. Public sample calculations require no account and execute no orders.

Local focused tests prove the route priority and headers in the application. Hosted CDN promotion, HTML delivery without a Python invocation and the current Prompt 3 browser journey require a READY exact-candidate deployment; they are not inferred from configuration.

## Measurement method

The established checks run bounded, serial requests against the canonical alias and record deployment identity, region, request order, response bytes, HTTP time, engine time, status/stages, action counts, replay, financial reconciliation and determinism. “First” means the first measured request in that session; it is not proof of a process-cold or worldwide latency result.

Historical `ff2e42d` probes [35967540536](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35967540536) and [35968872124](https://github.com/esmailshahid-hue/demand-supply-planning-intelligence/actions/runs/35968872124) remain baseline evidence only. They cannot close the current candidate.

## Required authorized release sequence

No push, deployment or project-setting change was performed during Prompt 4. The exact user action is to publish the current closure patch through the existing release process. After that:

1. confirm exact-SHA CI succeeds on Python 3.14 / Node 24, including Docker;
2. resolve the canonical alias to a READY deployment with that same SHA in `iad1`;
3. verify static root/assets, API 404 priority, disabled storage, links, dated fallback explanations, Plan-first loading, lazy evidence and the four scenario controls plus a combination;
4. run the canonical production-latency workflow twice consecutively on the unchanged deployment and retain its artifacts.

Only then change the status to READY. Full earlier deployment chronology is preserved in [history/DEPLOYMENT-through-2ec1c06.txt](history/DEPLOYMENT-through-2ec1c06.txt).
