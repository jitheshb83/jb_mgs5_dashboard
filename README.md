# MGS5 EV Dashboard

A personal, local-only web dashboard for keeping an eye on an MG MGS5 EV (Luxury, 64kWh gross /
62.1kWh usable) — state of charge, range, charging status, 12V battery health, tyre pressures,
trip/usage stats, and a derived battery State of Health (SOH) trend — without opening the
official MG iSmart app.

It talks to the same unofficial SAIC/iSmart cloud API the official app uses, runs entirely on
your own Mac, and is only reachable at `localhost` — nothing is exposed to the internet, and
there's no vehicle control (lock/unlock, climate, charge limits) in v1, monitoring only.

**Backend:** FastAPI (Python) + SQLite · **Frontend:** React + Vite + Tailwind + Recharts.

---

## What you get

- **At a glance:** SOC %, estimated range (BMS + IMCU), charging/plug status, 12V battery
  voltage, tyre pressures, cabin temperature, odometer, door/lock state.
- **Trends:** SOC, range, and 12V voltage over time, plus a derived SOH estimate once a couple
  of full charge cycles have been observed.
- **Battery Usage:** power used today / since your last charge, energy added by your last
  charge, current usable energy — vehicle-reported where available, transparently flagged as
  an estimate where it isn't (some of these fields aren't reported by every account/vehicle).
- **Advanced Info:** everything else the vehicle reports that doesn't fit the main dashboard —
  useful for digging into raw charging/session data.
- **Settings:** manual refresh (always available) plus an optional scheduled refresh, with a
  server-enforced minimum gap between real calls to the SAIC API so the vehicle's 12V battery
  isn't drained by over-polling.

## Before you start

You'll need:

- **macOS** (this is built to run locally on the owner's Mac; not tested elsewhere).
- **Python 3.12+** and [`uv`](https://docs.astral.sh/uv/) for the backend.
- **Node.js 18+** and `npm` for the frontend.
- **A dedicated *secondary* MG iSmart account** — never your everyday/primary one. Logging a
  second client into your primary account will log the official app out. See
  [`docs/planning/decisions_log.md`](docs/planning/decisions_log.md) for step-by-step
  instructions on creating one.

## First-time setup

Grab the [latest release](https://github.com/jitheshb83/jb_mgs5_dashboard/releases/latest)
(recommended once one exists — a tagged, known-working snapshot) or clone `main` directly:

```bash
git clone https://github.com/jitheshb83/jb_mgs5_dashboard.git
cd jb_mgs5_dashboard
cp backend/.env.example backend/.env
# now edit backend/.env: fill in your SECONDARY account's SAIC_USERNAME/SAIC_PASSWORD
```

That's the only manual step — `scripts/start.sh` (below) installs both the backend's Python
dependencies (`uv sync`) and the frontend's npm packages the first time you run it, so a fresh
clone works without any other setup.

## Running it

The easy way — starts both services in the background, installing dependencies first if this
is a fresh checkout:

```bash
scripts/start.sh
```

- Backend: `http://localhost:8000` (API docs at `/docs`)
- Frontend: `http://localhost:8001` ← **open this in your browser**

```bash
scripts/stop.sh      # stop both
scripts/restart.sh   # stop + start (handy after pulling changes or editing .env)
```

Each of the three also accepts `--backend-only` or `--frontend-only`. Logs land in `.run/`
(gitignored) if something looks wrong — check `.run/backend.log` first for API/credential
issues. Each start/restart prints which port it actually used per service.

**Custom ports** (default 8000 / 8001, e.g. if those are already taken):

```bash
BACKEND_PORT=9000 FRONTEND_PORT=3000 scripts/start.sh
```

Both services are told the other's port automatically (backend's CORS allow-list, frontend's
API base URL), so a non-default port never silently breaks them talking to each other.

<details>
<summary>Running backend/frontend manually instead</summary>

```bash
# backend
cd backend
uv sync
uv run uvicorn app.main:app --app-dir src --port 8000

# frontend, in a second terminal
cd frontend
npm install
npm run dev   # frontend/vite.config.ts defaults this to port 8001 too, no flag needed
```

</details>

## Using the dashboard

1. Open `http://localhost:8001`.
2. Click **Refresh** to pull live data from the vehicle. The backend enforces a 30-minute
   minimum gap between real calls to the SAIC API (protects the 12V battery from drain) — a
   refresh requested sooner just returns the last cached snapshot with its timestamp, no error.
3. Turn on **scheduled refresh** in Settings if you want it to poll automatically on an
   interval — only while the browser tab stays open, no background process.
4. The **SOH trend** chart needs a few genuine low-to-full charge cycles before it shows
   anything; until then it honestly says so instead of guessing.
5. Any field the dashboard can't get a real answer for shows as `—`, never a blank or `null` —
   and anywhere a number is estimated rather than vehicle-reported (see Battery Usage above),
   it's labeled as such.

## Tests

```bash
cd backend && uv run pytest    # + uv run ruff check src tests && uv run mypy src
cd frontend && npm test        # + npx tsc --noEmit
```

## Development

This repo is built contract-first: [`docs/architecture/api_contract.md`](docs/architecture/api_contract.md)
is the source of truth for every backend↔frontend interface, and
[`docs/architecture/data_model.md`](docs/architecture/data_model.md) for the SQLite schema.

- [`CLAUDE.md`](CLAUDE.md) — how this repo is worked on (conventions, workflow, behavioral rules).
- [`docs/planning/requirements.md`](docs/planning/requirements.md) — full requirements & scope.
- [`docs/planning/decisions_log.md`](docs/planning/decisions_log.md) — resolved decisions and
  any open items; check this before assuming anything about scope.
- [`docs/planning/soh_methodology.md`](docs/planning/soh_methodology.md) — how the SOH estimate
  is derived (and why the obvious approach doesn't work).
- [`docs/planning/testing_strategy.md`](docs/planning/testing_strategy.md) — what and how to test.
- [`docs/architecture/architecture_and_data_flow.svg`](docs/architecture/architecture_and_data_flow.svg) —
  visual system overview.
