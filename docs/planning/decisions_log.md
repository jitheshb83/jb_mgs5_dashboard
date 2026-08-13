# Decisions Log

Running log of decisions made during planning, most recent first.
Anything not listed here as "resolved" should be treated as open — ask, don't assume.

## Resolved

| Date | Decision | Detail |
|---|---|---|
| 2026-08-12 | SAIC client package name | Correct PyPI/import name is `saic_ismart_client_ng` (`pip install saic-ismart-client-ng`), from GitHub repo `SAIC-iSmart-API/saic-python-client-ng`. Earlier conversation referred to it loosely as "saic-python-client-ng" — that's the repo name, not the installable package name. Use `saic_ismart_client_ng` in code and dependencies. |
| 2026-08-12 | Battery capacity | MGS5 Luxury trim: 64 kWh gross / **62.1 kWh usable**. Confirmed via multiple independent spec sources (not just owner input) — use 62.1 kWh as `battery_nameplate_kwh` in SOH calculation. |
| 2026-08-12 | Minimum refresh gap | 30 minutes, server-enforced, applies to both manual and scheduled refresh triggers. |
| 2026-08-12 | Repo layout | Monorepo — `/backend` and `/frontend` in one repo (this repo). |
| 2026-08-12 | Parallel development | Claude Code will run backend, frontend, and test-writing as parallel subagents against a shared contract (see `docs/architecture/api_contract.md`), not improvised independently. |
| 2026-08-12 | Stack | FastAPI + `saic-python-client-ng` (backend), SQLite (storage), React + Vite + Tailwind + Recharts (frontend). No Grafana, no Home Assistant, no Docker requirement for v1. |
| 2026-08-12 | Scope | Single-user, localhost-only, monitoring/read-only in v1 (no vehicle control commands). |
| 2026-08-12 | Refresh model | Manual refresh button (primary). Optional scheduled refresh, off by default, frontend-timer-driven only (stops when tab closes) — no background daemon. |
| 2026-08-12 | SOH approach | No SOH field exists in the SAIC cloud API. SOH is a derived/directional estimate from full-charge-cycle tracking, clearly labeled as an estimate in the UI. True SOH requires a separate OBD-II dongle (e.g. Car Scanner app) — out of scope for this project. |
| 2026-08-12 | Map / vehicle location view | Deferred to v2. Not built in v1. `latitude`/`longitude` columns remain in the schema and are returned as null/omitted by the API in the meantime — no rework needed to add the view later. |

## Open — do not assume, ask first

| Item | Status | Notes |
|---|---|---|
| Secondary iSmart account | Instructions provided to owner (see below), not yet confirmed created/active | Dashboard's `.env` credentials must point to a **secondary** iSmart account, never the owner's primary daily-driver account, or the primary mobile app will be logged out. Do not proceed with live API integration testing until this is confirmed done. |

### How to create the secondary iSmart account (reference)
1. Log out of the iSmart app (Profile → Settings → Log out).
2. Register a brand-new account (own email + phone number, separate from primary).
3. Log out of that new account.
4. Log back into the **primary** account → Profile → Secondary Account → "+" → enter the new account's details → set as Permanent.
5. Ensure the secondary account is never logged into a phone/device — it should only ever be used by this dashboard's backend.
