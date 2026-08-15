**MGS5 EV Companion Dashboard**

Requirements & Design Document

**Owner:** Jithesh

**Vehicle:** MG MGS5 EV, purchased Feb 2026, Norway

**Status:** Draft v1.1 --- validated against current source repos and
community data, Aug 2026

**Scope:** Single-user, local, manual-refresh monitoring dashboard

1\. Overview

This document defines the requirements and design for a personal web
application to monitor the health, charge status, and telemetry of a
privately owned MG MGS5 EV. The application connects to the unofficial,
reverse-engineered SAIC/iSmart API used by the official MG iSmart mobile
app, since MG does not publish an official public API.

The application is designed for a single user, running locally on a Mac,
accessed only via localhost. There is no remote access, no multi-user
support, and no vehicle control functionality in v1 --- the focus is
read-only monitoring.

2\. Goals and Non-Goals

2.1 Goals

-   Provide a lightweight, visually polished dashboard to check the
    car\'s key stats on demand.

-   Track telemetry history over time (SOC, range, charging events) to
    support long-term trend analysis.

-   Derive a directional battery State of Health (SOH) estimate, since
    no official SOH field is exposed by the API.

-   Protect the vehicle\'s 12V battery from drain caused by excessive or
    automated API polling.

-   Keep the system simple to run and maintain --- no external
    infrastructure dependencies (no Grafana, no cloud, no Home
    Assistant).

2.2 Non-Goals (v1)

-   No remote/away-from-home access --- localhost only.

-   No multi-user accounts or authentication beyond storing the owner\'s
    own SAIC credentials.

-   No vehicle control commands (lock/unlock, climate start, charge
    limit changes) --- monitoring only.

-   No background/always-on polling daemon --- refresh only happens
    while the app is open in a browser tab.

3\. Background: Data Source

MG does not publish an official API. The SAIC iSmart backend (used by
the official iSmart app) has been reverse-engineered by the open-source
community. This project will use the

**saic-python-client-ng** Python library, which wraps this
reverse-engineered API.

3.1 Known constraints

-   Frequent polling can drain the vehicle\'s 12V battery --- community
    guidance suggests a minimum \~600 second cooldown between real API
    calls.

-   Field availability and naming varies by vehicle model/firmware; the
    MGS5 required different field lookups than the MG4/MG5 in community
    testing.

-   No dedicated \"battery health\" or SOH field exists in the cloud
    API. Two range estimates are available instead: BMS-based
    (chemistry/SOC-derived) and IMCU-based
    (driving-history/climate-derived).

-   A genuine SOH figure is obtainable, but only via a separate path
    outside the cloud API: an OBD-II dongle paired with a third-party
    app (e.g. Car Scanner, which has an MGS5-specific profile) reading
    the vehicle\'s local CAN bus. This requires physical hardware
    plugged into the car and is out of scope for a cloud-API-based web
    dashboard, but is noted here since it is the only source of a true
    (non-derived) SOH value confirmed by the MGS5 owner community as of
    early 2026.

-   This is unofficial access under MG\'s iSmart EULA, which technically
    restricts reverse engineering and redistribution. This is a
    personal-use, community-tolerated arrangement, not officially
    sanctioned by MG/SAIC.

4\. Functional Requirements

4.1 Authentication

-   The app stores the user\'s MG iSmart account credentials locally,
    used to authenticate against the SAIC API.

-   Credentials are stored in a local .env file (gitignored), not in
    source control or a database.

-   Session tokens are refreshed automatically as needed by the client
    library; no user action required beyond initial setup.

4.2 Manual Refresh

-   A visible \"Refresh\" button on the dashboard triggers a live pull
    from the SAIC API.

-   The backend enforces a minimum interval between real API calls
    (configurable, default suggested: 15 minutes) regardless of trigger
    source (manual click or scheduled tick).

-   If a refresh is requested before the minimum interval has elapsed,
    the UI shows the cached last-known data with a clear \"last
    updated\" timestamp, and does not call the SAIC API.

4.3 Scheduled Refresh (optional)

-   Off by default.

-   User can enable scheduled refresh via a Settings panel and choose an
    interval (e.g. 1h / 2h / 4h).

-   Scheduled refresh only runs while the browser tab is open
    (implemented as a frontend timer calling the same refresh endpoint)
    --- no background daemon or OS-level scheduler.

-   The same server-side minimum-interval floor applies to scheduled
    ticks as to manual clicks, so misconfiguration cannot cause
    excessive polling.

4.4 Dashboard Data Points

The dashboard displays the following, sourced from the SAIC API:

-   State of Charge (SOC) %

-   Estimated range --- BMS-based and IMCU-based (both shown, since they
    can diverge)

-   Charging status (active/inactive), plug status, charging current

-   12V (auxiliary) battery voltage

-   Tyre pressures (all four)

-   Cabin temperature

-   Odometer reading

-   Vehicle location (map view) --- nice-to-have, not blocking for v1

-   Derived battery SOH estimate (see Section 4.6)

4.5 History & Trends

-   Every successful refresh (manual or scheduled) writes a snapshot row
    to local SQLite storage.

-   The dashboard includes trend charts: SOC over time, range over time, 12V battery voltage
    over time, and SOH estimate over time.

-   Raw API responses are stored alongside parsed fields to allow
    re-parsing if field mappings need correction later (the API is
    unofficial and has shown field-naming inconsistencies across
    models/firmware).

4.6 Derived Battery SOH Estimate

-   No official SOH field exists in the cloud API, so SOH is estimated
    from observed data rather than read directly (see Section 3.1
    regarding the OBD-dongle alternative, which is out of scope for this
    app).

-   Approach: detect full-charge cycles (plug connected, SOC rising from
    a low threshold, e.g. below 30%, up to \~100%), estimate kWh
    delivered, and compare against the vehicle\'s nameplate usable
    capacity.

-   The nameplate usable capacity is a one-time configuration value
    based on the owner\'s MGS5 trim (Standard Range vs Long Range).

-   This is a directional estimate, not a precise measurement, and the
    UI should clearly label it as such.

4.7 Settings

-   Toggle scheduled refresh on/off, and set its interval.

-   Configure minimum refresh interval floor (advanced/optional).

-   Configure vehicle nameplate battery capacity (for SOH calculation).

4.8 Advanced Info & Battery Usage (added beyond original v1.1 scope, 2026-08-15)

-   **Advanced Info page** (`GET /api/latest/advanced`): every other decodable field from the
    vehicle's raw status/charging responses not already covered by 4.4's core dashboard --
    doors/locks/windows, tyre-adjacent diagnostics, charging-session raw fields, GPS/journey
    info when present, and a catch-all `raw_undecoded` map for anything not yet given a typed
    field. Added because the raw SAIC responses carry far more than the original core-dashboard
    list, and it was cheap to surface once the decode groundwork existed.
-   **Battery Usage page** (`GET /api/latest/battery-usage`): power-usage-today,
    power-usage-since-last-charge, last-charge-added, current-energy, and mileage-today /
    since-last-charge figures. Primarily the vehicle's own self-reported charging-session
    stats; per the 2026-08-15 correction in `docs/architecture/api_contract.md`, this
    particular vehicle's SAIC account has never reported most of these, so unreported fields
    fall back to a history-derived estimate (flagged via `estimated_fields` in the response) --
    see `docs/planning/decisions_log.md`.

These aren't a scope change to the goals in Section 2 -- still single-user, read-only,
localhost-only monitoring -- just additional surfaced detail. `docs/architecture/api_contract.md`
is the definitive, current interface; treat any conflict between it and this section as this
section being stale, not the contract.

5\. Non-Functional Requirements

  -----------------------------------------------------------------------
  **Category**      **Requirement**
  ----------------- -----------------------------------------------------
  Deployment        Runs locally on the user\'s Mac; no cloud hosting, no
                    Docker requirement (optional)

  Access            localhost only --- no exposed ports, no remote/away
                    access in v1

  Performance       Dashboard loads in under 2 seconds from local cache;
                    refresh call latency bound by SAIC API response time

  Data storage      SQLite single-file database; no external DB server

  Security          Credentials stored in local .env, never logged or
                    transmitted beyond the SAIC API call itself

  Reliability       Rate-limit protection is enforced server-side as a
                    single source of truth, independent of frontend state

  Maintainability   Small, single-repo codebase; Python backend, JS/TS
                    frontend; consistent with Jithesh\'s standard stack
                    (uv, ruff, mypy, pytest)

  UI Design         Modern, lightweight, visually polished --- not a
                    generic grid-of-panels (Grafana) look
  -----------------------------------------------------------------------

6\. System Architecture

The system consists of three components running locally: a React
frontend, a FastAPI backend, and a SQLite database file. The backend is
the only component that talks to the external SAIC API.

  -------------------------------------------------------------------------
  **Step**   **Flow**
  ---------- --------------------------------------------------------------
  1          Browser (localhost) --- React/Vite SPA

  2          REST call to FastAPI backend

  3          Backend calls saic-python-client-ng

  4          Client library calls the external SAIC API

  5          Backend writes/reads SQLite (car_snapshot, app_settings)
  -------------------------------------------------------------------------

6.1 Component Responsibilities

  ---------------------------------------------------------------------------
  **Component**           **Responsibility**
  ----------------------- ---------------------------------------------------
  React/Vite frontend     Dashboard UI, trend charts, settings panel,
                          optional scheduled-refresh timer

  FastAPI backend         Serves REST endpoints, enforces refresh rate
                          limiting, calls SAIC API, reads/writes SQLite,
                          computes SOH estimate

  saic-python-client-ng   Handles SAIC API authentication, session refresh,
                          and raw data retrieval

  SQLite                  Persists snapshot history and app settings in a
                          single local file
  ---------------------------------------------------------------------------

7\. Data Model (SQLite)

7.1 car_snapshot

  -----------------------------------------------------------------------------
  **Column**                  **Type**      **Notes**
  --------------------------- ------------- -----------------------------------
  id                          INTEGER PK    Autoincrement

  fetched_at                  TIMESTAMP     When this snapshot was retrieved

  soc_pct                     REAL          State of charge, %

  range_bms_km                REAL          BMS-based range estimate

  range_imcu_km               REAL          IMCU-based range estimate

  is_charging                 BOOLEAN       

  charging_current            REAL          

  plug_status                 TEXT          

  battery_12v_voltage         REAL          Auxiliary battery --- monitor for
                                            drain risk

  odometer_km                 REAL          

  cabin_temp_c                REAL          

  tyre_pressure_fl/fr/rl/rr   REAL          Four columns, one per tyre

  latitude / longitude        REAL          Optional, for map view

  raw_json                    TEXT          Full raw API response, for future
                                            re-parsing
  -----------------------------------------------------------------------------

7.2 app_settings

  -------------------------------------------------------------------------
  **Key**                     **Example Value** **Purpose**
  --------------------------- ----------------- ---------------------------
  schedule_enabled            false             Toggle for scheduled
                                                refresh

  schedule_interval_minutes   120               Interval when schedule is
                                                enabled

  min_refresh_gap_minutes     15                Server-enforced floor
                                                between real API calls

  battery_nameplate_kwh       61.1              Used for SOH estimate
                                                calculation
  -------------------------------------------------------------------------

7.3 soh_estimate (derived, optional separate table)

Populated by a backend job that detects completed full-charge cycles
from car_snapshot history and computes an estimated usable capacity,
stored as a trend line separate from raw snapshots.

8\. API Endpoints (Backend)

  --------------------------------------------------------------------------
  **Endpoint**      **Method**   **Description**
  ----------------- ------------ -------------------------------------------
  /api/refresh      POST         Triggers a live SAIC API pull if the
                                 minimum interval has elapsed; otherwise
                                 returns cached data

  /api/latest       GET          Returns the most recent snapshot (cached,
                                 no API call)

  /api/history      GET          Returns snapshot history for trend charts
                                 (supports date range query params)

  /api/soh          GET          Returns the derived SOH estimate trend

  /api/settings     GET/PUT      Reads or updates app_settings
  --------------------------------------------------------------------------

9\. Risks & Mitigations

  -----------------------------------------------------------------------
  **Risk**                        **Mitigation**
  ------------------------------- ---------------------------------------
  Excessive polling drains the    Server-enforced minimum refresh
  12V battery                     interval, applied uniformly to manual
                                  and scheduled triggers

  Unofficial API changes or       Store raw_json alongside parsed fields;
  breaks (field renames, auth     keep saic-python-client-ng updated;
  changes)                        treat SOH as directional, not precise

  Credential exposure             Local .env file only, localhost-only
                                  access, never logged

  SAIC account lockout from       Required, not optional: using the SAIC
  parallel app + dashboard        API from a second client (this
  sessions                        dashboard) while the primary iSmart
                                  mobile app is logged in on the same
                                  account causes the mobile app to be
                                  logged out, per SAIC API behaviour. Use
                                  a dedicated secondary iSmart account
                                  for the dashboard from the start.
  -----------------------------------------------------------------------

10\. Open Items

-   Confirm MGS5 trim (Standard Range vs Long Range) and nameplate
    usable kWh for SOH calculation.

-   Decide default minimum refresh gap (proposed: 15 minutes).

-   Create a dedicated secondary iSmart account for the dashboard before
    first use --- required to avoid logging the primary mobile app out
    (see Section 9).

-   Confirm whether map/location view is in scope for v1 or deferred.

11\. Proposed Technology Stack

  -----------------------------------------------------------------------
  **Layer**        **Choice**                 **Rationale**
  ---------------- -------------------------- ---------------------------
  Backend          FastAPI (Python) +         Matches existing Python
                   saic-python-client-ng      stack; async-friendly;
                                              minimal footprint

  Database         SQLite                     Zero setup, single file,
                                              sufficient for single-user
                                              local history

  Frontend         React + Vite + Tailwind    Fast to build, modern look
                   CSS, Recharts for charts   without heavy design effort

  Packaging        Single repo; uv for        Consistent with standard
                   backend, npm for frontend  Python stack (uv, ruff,
                                              mypy, pytest)

  Secrets          .env file, gitignored      Matches security-first,
                                              no-hardcoded-secrets
                                              standard
  -----------------------------------------------------------------------

12\. Out of Scope for v1 (Future Considerations)

-   Vehicle control commands (lock/unlock, remote climate, charge
    limit/current adjustment)

-   Remote access outside the home network

-   Multi-user support

-   Push/email notifications (e.g. charge complete, low SOC, 12V voltage
    anomaly)

-   Integration with electricity tariff data for smart-charging
    automation
