# Pass 1 deployment assessment

Checked on 16 September 2026. No service was purchased, no paid infrastructure was provisioned, and no public deployment was created.

## Available environment and selected shape

The repository began without any deployment configuration. The connected Vercel account was inspected read-only and exposes a **Hobby** team. The local environment has macOS arm64, Python 3.14.4, Node 25.6.1 and npm 11.9.0. Docker, uv and the Vercel CLI were not installed. No container-host account or deployment target was provided.

The default deployment skeleton is one Linux container: Node 24 builds the React bundle; Python 3.14-slim serves static assets and FastAPI through Uvicorn as a non-root user. The service has a health check, configurable `PORT`, one worker and no user-data persistence. This matches the build plan's preferred single service. [FastAPI container deployment guidance](https://fastapi.tiangolo.com/deployment/docker/)

A single worker makes the in-process concurrency guard meaningful. Scaling workers/replicas requires a deliberate memory/concurrency budget in a later pass. Forecast requests are dimension- and body-bounded. Planned CPU-heavy SciPy/HiGHS work must remain in a Python runtime, not a browser or edge runtime. SciPy's `milp` supports integer decisions, statuses and a time limit; Pass 1 only smoke-tests its availability, not the future planning formulation. [SciPy MILP reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html)

## Vercel compatibility result

Vercel's current Python runtime supports Python 3.12–3.14 and a standard 500 MB uncompressed Python function bundle. Its documented Hobby Fluid limits include 2 GB/1 vCPU and a 300-second duration. These are compatible in principle with bounded forecasting and the installed SciPy dependencies, but do not establish the Pass 2 full-plan runtime target. [Python runtime](https://vercel.com/docs/functions/runtimes/python), [function limits](https://vercel.com/docs/functions/limitations)

There is a concrete contract mismatch: Vercel Functions' documented request/response limit is **4.5 MB**; the generated full normalized sample is **17,475,067 bytes** (fixture: 2,684,842 bytes). A tiny server-generated sample request would fit, but the full normalized-data POST would not. This is why no Vercel configuration is presented as a verified deployment. Supporting it would need an explicitly designed transport/upload approach and hosted package/runtime checks, or choosing a container-capable host. Do not silently reduce the sample or add a second deployment. [Payload limit](https://vercel.com/docs/functions/limitations#request-body-size)

Local installed SciPy and NumPy occupy approximately 99 MB and 34 MB respectively. Linux wheel sizes and total function bundle size were not measured.

## Actual smoke evidence and remaining checks

The compiled frontend and live fixture/full-sample API passed HTTP and browser checks using `scripts/start.sh`. The production app serves both on the same port. Browser verification covered recalculation against captured API responses, launch and zero-demand behavior, four-screen navigation, error/retry behavior and mobile keyboard navigation.

`python -m scripts.solver_smoke` solved an independent one-variable integer problem with the expected `x = 2` and HiGHS status 0. The very first import of SciPy's optimizer on this local environment took **31.154 seconds**; a repeat process took **0.449 seconds**. Solve calls took 0.000–0.006 seconds. The first import must not be hidden in a 30-second end-to-end performance claim. SciPy is not imported in the Pass 1 HTTP request path. Pass 2 should initialize the solver at startup, distinguish readiness from liveness and measure cold/warm planning on the actual target host.

Docker build/run and the Linux runtime **could not be executed because Docker is absent**. `.github/workflows/verify.yml` includes Linux tests, browser tests and container smoke commands, but the workflow has not been run remotely. The local production HTTP smoke is the verified Pass 1 deployment smoke; it is not a claim of container or hosted verification.

Before public deployment: choose an authorized container-capable target (or resolve the Vercel payload mismatch), execute the image build/run and solver smoke on Linux, measure memory/cold startup/full-plan runtime, and verify actual host retention and logging. There are currently no uploads or raw-row logs. No retention or deletion claim is made for an unselected host.
