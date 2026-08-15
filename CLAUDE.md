# CLAUDE.md — MGS5 EV Dashboard

This file governs how Claude Code should work in this repo. Read it fully before making changes.

## Project summary

A single-user, local-only web dashboard for monitoring an MG MGS5 EV (Luxury, 64kWh gross /
62.1kWh usable) via the unofficial SAIC/iSmart cloud API. Runs on the owner's Mac, localhost
only, manual + optional scheduled refresh. Monitoring/read-only in v1 — no vehicle control.

Full context lives in `docs/`:
- `docs/planning/requirements.md` — full requirements doc (source of truth for scope)
- `docs/planning/decisions_log.md` — resolved decisions AND open items — **read this before
  assuming anything about scope**
- `docs/planning/soh_methodology.md` — how battery SOH is estimated
- `docs/planning/testing_strategy.md` — what and how to test
- `docs/architecture/api_contract.md` — the backend↔frontend interface contract
- `docs/architecture/data_model.md` — SQLite schema
- `docs/architecture/architecture_and_data_flow.svg` — visual architecture diagram

**Before writing code, check `docs/planning/decisions_log.md` for open items.** If your task
touches an open item (currently: map/location view scope), stop and ask the user rather than
assuming an answer.

## Core behavioral rules (apply always)

1. **Never assume — always clarify.** If a requirement is ambiguous or an open item is touched,
   ask. Don't silently pick a default.
2. **No fabricated APIs/paths/behavior.** If you're not sure a `saic_ismart_client_ng` method
   exists or behaves a certain way, check the library source/docs before writing code that
   depends on it.
3. **Security-first.** No hardcoded secrets. Credentials live in `backend/.env` (gitignored),
   loaded via environment variables. Validate all external input (SAIC API responses are
   unofficial and can change shape — validate before trusting).
4. **Git discipline.** Never auto-commit or push. Always confirm with the user first, every time,
   no exceptions.
5. **Surgical changes.** Touch only what the task requires. Don't refactor adjacent code, don't
   "improve" things that weren't asked for. Match existing style.
6. **Python stack standard:** `uv` for dependency management, `ruff` for linting, `mypy` for
   type checking, `pytest` for tests, latest stable CPython, `src/` layout, `pyproject.toml`
   only (no `setup.py`/`requirements.txt`).
7. **Token/cost discipline over maximum parallelism.** Parallelism (see below) is for genuine
   independent work, not for its own sake. If a task is small, just do it directly.

## Working against the contract, not against guesses

`docs/architecture/api_contract.md` and `docs/architecture/data_model.md` are the shared
source of truth between backend and frontend work. Any subagent (or you, working solo) must:
- Build against what those docs say the interface looks like.
- If implementation reveals the contract needs to change, **update the contract doc first**,
  flag the change clearly in your summary to the user, then proceed. Never let backend and
  frontend silently diverge from each other by each guessing independently.

---

## Subagent workflow (parallel development)

This project uses Claude Code's Task tool to run backend, frontend, and test work as parallel
subagents where the work is genuinely independent. Use this workflow for any non-trivial
feature (i.e. not one-line fixes).

### When to parallelize vs. not

Parallelize when subagents can work from a **fixed contract** without needing each other's
in-progress output:
- Backend implementing an endpoint + frontend building the UI that will call it — both can work
  from `api_contract.md` simultaneously.
- Writing tests for a module that's already spec'd (even before implementation exists, if the
  contract is clear enough — tests can be written against the intended interface).

Do NOT parallelize when:
- The contract itself is still undecided (resolve that first, sequentially, possibly by asking
  the user).
- One piece of work genuinely depends on seeing the other's actual output (not just its
  contract) — e.g. debugging an integration issue between two already-built pieces.

### Standard task breakdown for a new feature

1. **Planning step (you, not a subagent):** confirm the feature against `decisions_log.md` and
   `api_contract.md`. If the contract needs a new endpoint/field, propose the addition, update
   the contract doc, and get user confirmation if it touches an open item or changes existing
   contract shape.
2. **Launch parallel subagents** via the Task tool, each with a narrow, contract-bound brief:
   - **Backend subagent:** implement the endpoint(s)/logic in `backend/src/app/`, per
     `api_contract.md` and `data_model.md`. Write unit + integration tests per
     `testing_strategy.md`. Must not touch `frontend/`.
   - **Frontend subagent:** implement the UI component(s) in `frontend/src/`, per
     `api_contract.md`, using mocked contract-shaped data until backend is ready. Write
     component tests. Must not touch `backend/`.
   - **(Optional) Test-review subagent:** once both land, reviews that tests actually assert
     against the contract (not just "does it run"), and checks the two sides agree on field
     names/shapes exactly as written in `api_contract.md`.
3. **Integration step (you, not a subagent):** wire frontend to real backend (swap mocked data
   for real fetch calls), run the full test suite, fix any contract drift by updating the
   contract doc + both sides consistently.
4. **Report to user:** summarize what changed, what was tested, and explicitly call out any
   place where the contract was changed from what was originally documented.

### Example subagent prompt shape (for you to adapt, not copy verbatim)

```
Task: Implement POST /api/refresh per docs/architecture/api_contract.md.
Scope: backend/src/app/ only. Do not modify frontend/ or docs/ (except to flag contract
issues back to the orchestrator).
Requirements:
- Follow the exact request/response shapes in api_contract.md.
- Enforce the 30-minute minimum refresh gap (see decisions_log.md) server-side.
- Use `saic_ismart_client_ng` for the live SAIC call; mock it in tests (never call the real API
  in automated tests).
- Write unit tests for the rate-limit boundary and integration tests for the full round-trip,
  per docs/planning/testing_strategy.md.
- Surgical changes only — don't touch unrelated files.
Return: a summary of files changed, tests added, and any place you deviated from or found gaps
in the contract doc.
```

---

## Repo structure

```
jb_mgs5_dashboard/
├── CLAUDE.md                          (this file)
├── README.md                          (setup + scripts/ quick start)
├── scripts/                           (start.sh / stop.sh / restart.sh -- local dev services)
├── docs/
│   ├── planning/
│   │   ├── requirements.md
│   │   ├── decisions_log.md
│   │   ├── soh_methodology.md
│   │   └── testing_strategy.md
│   └── architecture/
│       ├── api_contract.md
│       ├── data_model.md
│       └── architecture_and_data_flow.svg
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── src/app/
│   │   ├── api/            (FastAPI route handlers: refresh, latest, advanced, battery_usage,
│   │   │                    history, settings, soh)
│   │   ├── services/       (SAIC client wrapper, SOH cycle detection, battery-usage history
│   │   │                    fallback, rate-limit logic)
│   │   ├── models/         (Pydantic schemas matching api_contract.md)
│   │   └── db/              (SQLite access, schema per data_model.md)
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/        (anonymized mock SAIC API responses)
└── frontend/
    ├── package.json
    ├── src/
    │   ├── components/      (dashboard cards, refresh button, settings panel, advanced-info
    │   │                    and battery-usage pages)
    │   ├── pages/
    │   ├── hooks/            (data fetching hooks matching api_contract.md)
    │   ├── lib/               (API client, formatting helpers)
    │   └── charts/           (Recharts trend components, incl. SOH trend)
    └── tests/
```

## Current status / next steps

Live SAIC integration is working end-to-end against the owner's secondary iSmart account (see
`docs/planning/decisions_log.md`'s Resolved table). Implemented: manual + scheduled refresh,
`/api/latest` (+ `/advanced`, `/battery-usage`), `/api/history`, `/api/settings`, and `/api/soh`
(full-charge-cycle SOH estimation, persisted at refresh time). `scripts/start.sh` /
`stop.sh` / `restart.sh` run both services locally for testing (see `README.md`).

See `docs/planning/decisions_log.md`'s "Open" table for what's still blocking full v1 scope —
currently just the map/location view (deferred to v2 regardless).
