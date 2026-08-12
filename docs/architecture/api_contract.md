# API Contract — Backend ↔ Frontend

**Purpose:** This is the single source of truth for the interface between backend and frontend.
Both the backend subagent and frontend subagent must build against this document, not against
each other's in-progress code. If reality diverges from this contract during implementation,
update this file first (or flag it for the user to confirm), then proceed — don't let the two
sides silently drift apart.

Base URL: `http://localhost:8000` (dev)

---

## POST /api/refresh

Triggers a refresh. Returns cached data if the minimum refresh gap (30 min, see `app_settings.min_refresh_gap_minutes`) hasn't elapsed since the last real API call; otherwise calls the SAIC API live.

**Request body:** none

**Response 200:**
```json
{
  "source": "live" | "cached",
  "fetched_at": "2026-08-12T14:30:00Z",
  "snapshot": { "...": "see Snapshot object below" }
}
```

**Response 502:** SAIC API call failed (auth error, network error, unexpected schema). Body:
```json
{ "error": "string description", "detail": "string, safe to show user" }
```

---

## GET /api/latest

Returns the most recent snapshot from SQLite. No external API call. Used on page load.

**Response 200:**
```json
{ "fetched_at": "2026-08-12T14:30:00Z", "snapshot": { "...": "Snapshot object" } }
```

**Response 404:** No snapshot exists yet (first run, before any refresh).

---

## GET /api/history?from=<ISO8601>&to=<ISO8601>&limit=<int>

Returns snapshot history for trend charts. All query params optional; defaults to last 30 days, limit 500.

**Response 200:**
```json
{ "snapshots": [ { "...": "Snapshot object" }, "..." ] }
```

---

## GET /api/soh

Returns the derived SOH estimate trend (see `docs/planning/soh_methodology.md`).

**Response 200:**
```json
{
  "estimates": [
    { "computed_at": "2026-08-01T00:00:00Z", "soh_pct": 98.2, "usable_kwh_estimate": 60.9, "basis": "full_charge_cycle" }
  ],
  "nameplate_usable_kwh": 62.1
}
```

If no full-charge cycle has been observed yet, `estimates` is an empty array — frontend must handle this (show "not enough data yet", not an error).

---

## GET /api/settings

**Response 200:**
```json
{
  "schedule_enabled": false,
  "schedule_interval_minutes": 120,
  "min_refresh_gap_minutes": 30,
  "battery_nameplate_kwh": 62.1
}
```

## PUT /api/settings

**Request body:** partial or full object matching GET response shape above.
**Response 200:** the updated full settings object.
**Response 400:** validation error (e.g. `schedule_interval_minutes` below `min_refresh_gap_minutes`).

---

## Shared object: Snapshot

This exact shape is returned by `/api/refresh`, `/api/latest`, and appears in the `snapshots` array of `/api/history`. Field names are final — do not rename independently in backend or frontend.

```json
{
  "soc_pct": 78.0,
  "range_bms_km": 310.0,
  "range_imcu_km": 295.0,
  "is_charging": false,
  "charging_current": null,
  "plug_status": "unplugged",
  "battery_12v_voltage": 12.6,
  "odometer_km": 4210.5,
  "cabin_temp_c": 21.0,
  "tyre_pressure_fl": 2.4,
  "tyre_pressure_fr": 2.4,
  "tyre_pressure_rl": 2.3,
  "tyre_pressure_rr": 2.3,
  "latitude": null,
  "longitude": null
}
```

Notes:
- Any field can be `null` if the SAIC API didn't return it — frontend must render a "—" or similar placeholder, never crash or show `null`/`undefined` literally.
- `raw_json` (full raw API response) is stored in SQLite for debugging but is **not** included in API responses to the frontend — keep payloads lean.
- Units: km, °C, bar (tyre pressure), volts, percent. Do not convert units in the backend — frontend owns display formatting.

---

## Error handling contract

- All error responses use `{ "error": string, "detail": string }` shape.
- Frontend shows `detail` to the user; `error` is for logs/debugging only.
- Backend never leaks raw exception tracebacks or credential values in error responses.

## Rate-limit contract

- The 30-minute floor is enforced **only** in the backend. Frontend must not implement its own
  gating logic beyond disabling the refresh button while a request is in flight — the backend's
  `source: "cached"` response is the actual source of truth for whether a live call happened.
