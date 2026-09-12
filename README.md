# Forge — Distributed Job Queue Engine

A from-scratch background job/workflow queue built on Postgres — durable task submission, safe concurrent workers, exponential-backoff retries, dead-lettering, and a live operations console. Built to demonstrate distributed-systems fundamentals (safe concurrency, retry semantics, observability) rather than wrapping an existing queue library.

**Live demo:** [forge-dashboard-eta.vercel.app](https://forge-dashboard-eta.vercel.app)
**API + docs:** [forge-api-3ob1.onrender.com/docs](https://forge-api-3ob1.onrender.com/docs)

> Note: the API runs on Render's free tier and spins down after 15 minutes of inactivity — the first request after idle time can take 30-60 seconds to respond. This is a known, deliberate trade-off of the free deployment tier, not a bug.

## The problem

Every backend eventually needs to run work outside the request/response cycle — sending emails, processing uploads, retrying failed calls to a third-party API. Most tutorials wrap Celery or RQ and call it done; this project builds the actual mechanism from first principles to understand (and be able to explain) what those libraries are doing underneath.

## What it does

- Accepts tasks via a REST API and stores them durably in Postgres
- Multiple workers can poll for work concurrently **without double-processing the same task** (`SELECT ... FOR UPDATE SKIP LOCKED`)
- Failed tasks retry automatically with exponential backoff, then move to a dedicated `dead_letters` table after exhausting retries
- Idempotency keys prevent duplicate submissions from creating duplicate work
- A live operations console (Next.js) shows real-time task counts and a task ledger, polling the API every few seconds

## Architecture

┌─────────────────┐ ┌──────────────────┐ ┌─────────────────┐
│ Next.js Console │─────▶│ FastAPI API │─────▶│ PostgreSQL │
│ (Vercel) │◀─────│ (Render, free) │◀─────│ (Neon, free) │
└─────────────────┘ └────────┬─────────┘ └────────▲────────┘
│ embedded worker thread │
└───────────────────────────┘


**Design decision — embedded worker:** Render's free tier only covers Web Services, not Background Workers. Rather than pay for a separate worker process, the worker's polling loop runs as a background thread inside the same free API process in production. Locally (via Docker Compose), the API and worker run as genuinely separate containers — the split still exists in the codebase and is demonstrated locally; only the free deployment collapses them into one process. This trade-off is intentional and documented here rather than hidden.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| API | FastAPI | async-friendly, automatic OpenAPI docs |
| DB / Queue | PostgreSQL (Neon free tier) | `FOR UPDATE SKIP LOCKED` gives durable, safe concurrent queueing without adding Redis/Kafka — simpler and equally correct at this scale |
| ORM / Migrations | SQLAlchemy 2.0 + Alembic | schema-as-code, reviewable migrations |
| Rate limiting | slowapi | protects submission endpoint from abuse |
| Logging | structlog | structured JSON logs, not print statements |
| Frontend | Next.js (App Router) + TypeScript | live-polling operations console |
| CI | GitHub Actions | runs the full test suite + Docker build on every push |
| Deployment | Render (API) + Vercel (dashboard) + Neon (DB) | genuinely free, no credit card required for any of the three |


## Running locally

```bash
git clone https://github.com/Abdul-Rahman16/forge-job-queue.git
cd forge-job-queue
docker compose up --build
```

Then visit `http://localhost:8000/docs` for the API, or run the dashboard separately (see `forge-dashboard` repo).

## Tests

```bash
pip install -r requirements.txt
pytest tests/unit -v
```

7 unit tests cover task submission, idempotency, claiming, completion, and retry/dead-letter transitions.

## Repository structure
api/ FastAPI routes, request/response schemas
core/ config, DB session, logging, rate limiter, notifications
domain/ framework-agnostic business logic (queue claim/retry logic, models)
workers/ background worker entrypoint
tests/ unit tests
alembic/ database migrations


`domain/` never imports from `api/` or FastAPI — this is what makes the queue logic unit-testable in isolation from any web framework.