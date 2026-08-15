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
| 2026-08-15 | Secondary iSmart account | Confirmed created and active — live refreshes against the real SAIC API have been working end-to-end since. Dashboard's `.env` credentials point to this secondary account, never the owner's primary daily-driver account. |
| 2026-08-15 | Battery-usage vehicle-reported fields are unreliable for this account | `rvsChargeStatus.powerUsageOfDay`/`powerUsageSinceLastCharge`/`lastChargeEndingPower`/`totalBatteryCapacity` are confirmed `null` in every stored snapshot since account setup, including while actively charging — a live test of the SAIC API's alternate `get_vehicle_charging_status` endpoint failed outright rather than supplying the missing data. Treated as a genuine SAIC-backend gap for this vehicle/market, not a decode bug. Fix: `GET /api/latest/battery-usage` falls back to estimating these fields from `car_snapshot` history (see `api_contract.md`'s 2026-08-15 correction), flagged via the response's `estimated_fields` list. |
| 2026-08-15 | SOH kWh-delivered method | The originally-documented v1 fallback (SOC delta scaled by the nameplate constant) is mathematically circular — it always yields ~100% SOH regardless of real battery condition. Caught before implementation. Fixed method: use the delta in the vehicle's own `current_energy_kwh` (`realtimePower`) between a cycle's start/end snapshots instead — see `soh_methodology.md`'s 2026-08-15 correction and `backend/src/app/services/soh.py`. |
| 2026-08-15 | Default dev ports | Backend defaults to 8000 (unchanged). Frontend's default changed from Vite's own default (5173) to **8001**, set consistently in three places so no path silently disagrees: `scripts/lib.sh`'s `FRONTEND_PORT` default, `frontend/vite.config.ts`'s `server.port` (so even a bare `npm run dev` with no flags lands on 8001), and `backend/src/app/config.py`'s `FRONTEND_PORT` fallback (so CORS is correct even without `scripts/start.sh`). Both ports remain overridable via `BACKEND_PORT`/`FRONTEND_PORT` env vars — see README's "Custom ports". |
| 2026-08-16 | `range_bms_km` vs `range_imcu_km` meaning confirmed | Owner reported the dashboard's BMS range (600 km) didn't match the MG app's displayed range (460-480 km), which instead matched our IMCU figure (461 km) almost exactly, at the same SOC. Not a decode bug: `range_bms_km` (`bmsEstdElecRng`) is a rated/theoretical range at current SOC, not adjusted for actual driving (implied ~10.3 kWh/100km); `range_imcu_km` (`imcuVehElecRng`) is the IMCU's adaptive, real-world estimate (~13.3 kWh/100km) and is the one that matches what MG's app/dash typically show — a documented MG/SAIC community-known divergence, not unique to this vehicle. This confirmation also resolves `imcuVehElecRng`'s previously-unverified scaling judgment call (see `saic_client.py`). Fix: `RangeCard` relabeled "BMS (rated)" / "IMCU (real-world)" with an explanatory line, since both were previously shown as equally-weighted numbers with no indication one runs consistently higher. |

## Open — do not assume, ask first

Nothing currently blocking. The only deferred item is the map/location view above (v2, not
open — already resolved as "not in v1").

### How to create the secondary iSmart account (reference)
1. Log out of the iSmart app (Profile → Settings → Log out).
2. Register a brand-new account (own email + phone number, separate from primary).
3. Log out of that new account.
4. Log back into the **primary** account → Profile → Secondary Account → "+" → enter the new account's details → set as Permanent.
5. Ensure the secondary account is never logged into a phone/device — it should only ever be used by this dashboard's backend.
