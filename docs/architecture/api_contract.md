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
Ordered most-recent-first (matches `/api/latest`'s ordering; frontend reverses for
chronological chart rendering).

**Response 200:**
```json
{
  "snapshots": [
    { "fetched_at": "2026-08-12T14:30:00Z", "snapshot": { "...": "Snapshot object" } },
    "..."
  ]
}
```

Each entry wraps a `Snapshot` with its own `fetched_at`, the same `{fetched_at, snapshot}` shape
already used by `/api/refresh` and `/api/latest` -- necessary since `Snapshot` itself carries no
timestamp (it's purely the vehicle-state fields; when it was fetched is wrapper metadata, same
design as the other two endpoints). **Correction, 2026-08-12:** this endpoint originally shipped
returning a bare `Snapshot[]` with no per-item timestamp -- discovered as a gap when the frontend
tried to build trend charts with a real time axis and found nothing to plot it against. Fixed by
wrapping each entry, consistent with the existing pattern, rather than adding `fetched_at` onto
`Snapshot` itself (which would leave `/api/refresh`/`/api/latest` with a redundant duplicate field).

---

## GET /api/soh

**Status: implemented 2026-08-15.** Returns the derived SOH estimate trend (see
`docs/planning/soh_methodology.md`, including that same day's correction to the fallback
formula -- the originally-documented SOC-delta-against-nameplate method was mathematically
circular and would always report ~100% regardless of actual battery condition; the shipped
method uses the delta in `current_energy_kwh` between a cycle's start/end snapshots instead,
per `backend/src/app/services/soh.py`'s docstring).

Read-only: new estimates are detected and persisted as a side effect of `POST /api/refresh`
(only on a live fetch, not a cache hit -- see `app/api/refresh.py`'s
`_record_soh_estimates_if_any`), by scanning `car_snapshot` history for newly-completed
full-charge cycles not already in `soh_estimate`. This route just reads what's stored.

**Response 200:**
```json
{
  "estimates": [
    { "computed_at": "2026-08-01T00:00:00Z", "soh_pct": 98.2, "usable_kwh_estimate": 60.9, "basis": "current_energy_kwh_delta" }
  ],
  "nameplate_usable_kwh": 62.1
}
```

`estimates` is ordered most-recent-first (`computed_at` descending), same convention as
`/api/history` -- the frontend reverses it to chronological order for charting, same as it
already does for `/api/history`'s snapshots.

If no full-charge cycle has been observed yet, `estimates` is an empty array — frontend must
handle this (show "not enough data yet", not an error). Per `soh_methodology.md`'s known
limitations, the frontend should also treat fewer than 2-3 estimates as "not enough data yet"
even once `estimates` is non-empty, since a single data point is noise, not signal -- this
gating is a frontend display decision, not something the API suppresses.

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

## GET /api/latest/advanced

Returns every known field from the latest snapshot's raw vehicle-status/charging-management
response that is **not** already part of the core `Snapshot` object or `doors`. Decoded
server-side from the stored `raw_json` at request time (no extra live SAIC call, no historical
storage -- reflects only the latest snapshot). Every field individually nullable.

Implemented in `backend/src/app/services/advanced_info.py`. Decode conventions confirmed
against the installed `saic_ismart_client_ng` source and
`SAIC-iSmart-API/saic-python-mqtt-gateway` (same method already used for the core Snapshot and
`doors` fields in `saic_client.py`) -- see that module's docstring for exactly which reference
file backs each field. Fields with **no** confirmed decode anywhere in either source are
surfaced raw under `raw_undecoded` with their original SAIC field name, per CLAUDE.md's "no
fabricated behavior" rule, rather than an invented meaning.

**Validated against a real vehicle, 2026-08-13.** Once live API access was confirmed working,
every field name in a real captured `raw_json` payload was cross-checked against this endpoint's
output to find anything silently dropped -- this caught and fixed two things: (1) ~50 raw fields
that existed in the real response but weren't surfaced anywhere (fossil-fuel fields meaningless
for this BEV, charge-scheduling reservation codes, HV battery pack voltage/power, vehicle alert
codes, several charging-session diagnostic fields) -- now added, either as newly-confirmed
decoded fields or under `raw_undecoded`; (2) a real decode bug in `charging_port_locked`, which
used the wrong truthiness convention (`> 0` instead of the confirmed `== 1`) and would have
misreported a real captured value of `2` as "locked". `raw_undecoded`'s exact field list is
long (~50 entries) and evolves as more gets confirmed -- see `advanced_info.py`'s
`_RAW_UNDECODED_*_FIELDS` tuples for the definitive, current list rather than duplicating it here.

**Response 200:**
```json
{
  "fetched_at": "2026-08-12T14:30:00Z",
  "advanced": {
    "engine_running": false,
    "is_parked": true,
    "hand_brake_on": true,
    "main_beam_on": false,
    "dipped_beam_on": false,
    "side_light_on": false,
    "exterior_temp_c": 19.0,
    "remote_climate_status": "off",
    "rear_window_heat_on": false,
    "front_left_seat_heat_level": 0,
    "front_right_seat_heat_level": 0,
    "current_journey": { "id": 12, "distance_km": 4.2 },
    "gps": {
      "latitude": 59.91,
      "longitude": 10.75,
      "altitude_m": 10,
      "heading_deg": 90,
      "speed_kmh": 0.0
    },
    "has_active_alerts": false,
    "vehicle_reported_at": "2026-08-13T19:09:17Z",
    "charging_pile_id": "PILE-0001",
    "charging_pile_supplier": "ACME Charging",
    "charging_type_raw": 1,
    "charging_working_voltage_raw": 230,
    "charging_working_current_raw": 16,
    "charging_remaining_time_minutes": 45,
    "charging_port_locked": false,
    "target_soc_pct": 80,
    "charge_current_limit": "16A",
    "bms_charging_status": "CHARGING_1",
    "charging_stop_reason": "NO_REASON",
    "hv_battery": { "voltage_v": 387.75, "power_kw": 0.0 },
    "battery_heating": { "active": false, "stop_reason": "NO_REASON" },
    "scheduled_charging": { "mode": "DISABLED", "start_time": "22:00", "end_time": "06:00" },
    "obc_ac_input": {
      "current_a": 16.0,
      "voltage_v": 230.0,
      "power_single_phase_kw": 3.68,
      "power_three_phase_kw": 2.125
    },
    "raw_undecoded": {
      "lastKeySeen": null,
      "steeringHeatLevel": null,
      "steeringWheelHeatFailureReason": null,
      "timeOfLastCANBUSActivity": null,
      "vehElecRngDsp": null,
      "clstrDspdFuelLvlSgmt": null,
      "extendedData1": null,
      "extendedData2": null,
      "powerMode": null,
      "vehicleAlarmStatus": null,
      "wheelTyreMonitorStatus": null,
      "canBusActive": null,
      "...": "~35 more fields -- see advanced_info.py's _RAW_UNDECODED_*_FIELDS for the full list"
    }
  }
}
```

Field notes:
- `engine_running` (`basicVehicleStatus.engineStatus` via the library's own `is_engine_running`
  property) / `is_parked` (the library's own `is_parked` property: `engineStatus != 1 or
  handBrake == 1`).
- `hand_brake_on`, `main_beam_on`, `dipped_beam_on`, `side_light_on`, `rear_window_heat_on`
  (from `rmtHtdRrWndSt`) -- all `value > 0` = on, confirmed via
  `basic_vehicle_status.py`'s `int_to_bool` usage.
- `exterior_temp_c` -- same validity/sentinel convention as `cabin_temp_c` (reject outside
  -127..127 or exactly 87).
- `remote_climate_status` (from `remoteClimateStatus`) -- one of `"off"`, `"blowingonly"`,
  `"on"`, `"front"`, or `"unknown (<raw>)"`, per mqtt-gateway's `to_remote_climate`.
- `current_journey` -- `null` unless both `currentJourneyId` and `currentJourneyDistance` are
  present; `distance_km` is raw `currentJourneyDistance / 10.0`.
- `gps` -- `null` unless `gpsPosition.gpsStatus` indicates a 2D or 3D fix; `latitude`/`longitude`
  are raw / 1,000,000 (validated `|lat| <= 90`, `|long| <= 180`); `speed_kmh` is raw wayPoint
  speed / 10.0; `heading_deg`/`altitude_m` are raw, unscaled. Present here even though the map
  *view* is deferred to v2 (`decisions_log.md`) -- that decision was about not building a map
  UI, not about hiding raw GPS text on a diagnostics page.
- `charging_pile_id`/`charging_pile_supplier` (from `rvsChargeStatus`), `charging_type_raw`,
  `charging_working_voltage_raw`/`charging_working_current_raw` (`workingVoltage`/
  `workingCurrent`, raw/unscaled -- no confirmed scaling factor found in either source) are
  passed through as-is.
- `charging_remaining_time_minutes` (from `chrgMgmtData.chrgngRmnngTime`) -- `null` unless the
  paired `chrgngRmnngTimeV` validity flag is not `1`, per mqtt-gateway's validator.
- `target_soc_pct`/`charge_current_limit` -- via `ChrgMgmtData`'s own `charge_target_soc`
  (`.percentage`) / `charge_current_limit` (`.limit`) enum properties; `null` for the raw "0 /
  ignore" sentinel, same guard mqtt-gateway uses before attempting the enum lookup.
- `has_active_alerts` -- `true` if `extendedVehicleStatus.alertDataSum` (a raw array of alert
  codes) contains any nonzero entry, `null` if the array itself wasn't present. Individual index
  meanings are unconfirmed, so only this safe "is anything active" boolean is derived -- the raw
  array itself is kept in `raw_undecoded.alertDataSum` so no information is lost.
- `vehicle_reported_at` -- `vehicle_status.statusTime` (epoch seconds -- unit confirmed by
  cross-checking a real captured value against the known time it was fetched at) converted to
  ISO8601. When the vehicle *itself* last computed this status, distinct from `fetched_at` (when
  *we* pulled it) -- a large gap between the two would mean the car hasn't phoned home recently.
- `charging_port_locked` -- `ccuEleccLckCtrlDspCmd == 1` (confirmed via `ChrgMgmtData
  .charging_port_locked`). **Not** the `> 0` convention used for doors/lights -- confirmed wrong
  for this field against a real vehicle (a captured value of `2` is a different state, not
  "locked").
- `bms_charging_status` -- `BmsChargingStatusCode.to_code(bmsChrgSts)` (e.g. `"CHARGING_1"`,
  `"CHARGE_DONE"`, `"UNPLUGGED"`) -- more granular than the core Snapshot's boolean `is_charging`.
- `charging_stop_reason` -- `ChargingStopReason.to_code(bmsChrgSpRsn)`; always a named reason
  (falls back to `"OTHER_REASON"` for an unrecognized code, per the library's own convention) or
  `null` if the raw field itself is missing.
- `hv_battery` -- the **main traction battery** pack voltage/power, distinct from the core
  Snapshot's `battery_12v_voltage` (the 12V auxiliary battery). `voltage_v` = `bmsPackVol * 0.25`,
  `power_kw` = `decoded_current * voltage_v / 1000` -- both formulas copied from `ChrgMgmtData`'s
  own `decoded_voltage`/`decoded_power` properties.
- `battery_heating` -- `active` = `bmsPTCHeatReqDspCmd == 1`; `stop_reason` =
  `HeatingStopReason.to_code(bmsPTCHeatResp)`'s name, or `null` for an unrecognized code (unlike
  `charging_stop_reason`, `HeatingStopReason.to_code` returns `None` rather than a fallback
  member on an unrecognized code -- both mirror their real library behavior exactly).
- `scheduled_charging` -- `null` unless all five `bmsReser*` reservation fields are present and
  `bmsReserCtrlDspCmd` decodes to a known `ScheduledChargingMode` (`DISABLED` /
  `UNTIL_CONFIGURED_SOC` / `UNTIL_CONFIGURED_TIME`); `start_time`/`end_time` are `HH:MM` built
  from the paired hour/minute fields. Confirmed via `chrg_mgmt_data.py`'s
  `__publish_charging_schedule` -- note `bmsReserSp*` is the **end** time and `bmsReserSt*` is
  the **start** time, confirmed by which local variable each feeds in that source (not obvious
  from the field names alone).
- `obc_ac_input` -- the on-board (AC) charger's input current/voltage/power, i.e. what the
  wall/EVSE is delivering during AC charging -- distinct from `hv_battery` (the pack's own
  state). `null` unless both `onBdChrgrAltrCrntInptCrnt`/`Vol` are present. Formulas copied
  verbatim from `chrg_mgmt_data.py`'s `__publish_obc_data` (current = raw / 5.0 A, voltage = raw
  * 2 V; the two power figures are **not** simply `voltage * current * sqrt(3)` for three-phase
  -- verified numerically against the reference's own formula, not algebraically re-derived, since
  a naive expansion is 3x too high), then converted from the reference's native watts to kW to
  match `hv_battery`'s units on this page.
- `raw_undecoded` -- everything else from `basicVehicleStatus`/`chrgMgmtData`/`rvsChargeStatus`
  with **no** confirmed decode in either the installed `saic_ismart_client_ng` library or
  `saic-python-mqtt-gateway` (verified by grepping a full clone of the reference repo, not just
  its published docs), plus the fossil-fuel fields (`fuelLevelPrc`/`fuelRange`/`fuelRangeElec`)
  that exist in the library for PHEV/ICE models but are meaningless for this BEV, plus the raw
  `alertDataSum` array. `rvsChargeStatus` fields that would collide with a
  `basicVehicleStatus` field of the same name (`extendedData1`/`extendedData2`) or a distinct
  field with the same name (`fuelRangeElec`) are prefixed `rvs*` to disambiguate;
  `rvsChargeStatus.mileage` is intentionally **not** duplicated here since it's redundant with
  the core Snapshot's `odometer_km`. See `advanced_info.py`'s `_RAW_UNDECODED_*_FIELDS` tuples
  for the definitive, current list.

**Response 404:** No snapshot exists yet (same as `/api/latest`).

---

## GET /api/latest/battery-usage

Battery usage statistics primarily sourced from the vehicle's self-reported charging-session
data (`rvsChargeStatus`, part of the charging-management response already fetched every
refresh -- no extra live SAIC call).

**2026-08-15 correction:** in practice, this vehicle's SAIC account has *never* reported
`powerUsageOfDay`, `powerUsageSinceLastCharge`, `lastChargeEndingPower`, or `totalBatteryCapacity`
-- confirmed null across every stored snapshot since account setup, including while actively
charging, and a live test of the SAIC API's alternate `get_vehicle_charging_status` endpoint
(unused elsewhere in this app) failed outright rather than supplying the missing data. This
appears to be a genuine gap in what the SAIC backend pushes for this vehicle/market, not a
decode bug -- see `docs/planning/decisions_log.md`. Each of these fields now has a **history-derived
fallback**, computed from `car_snapshot` history when the vehicle itself reports `null`: a
SOC-delta x capacity estimate, directional not a true independent energy measurement -- the same
*spirit* as the SOH estimate in `soh_methodology.md`, but **not the same technique**. SOH's own
2026-08-15 correction found that exact SOC-delta-against-nameplate formula circular for SOH's
purposes and replaced it with a `current_energy_kwh` delta instead (see `soh.py`); that fix
doesn't apply here since this fallback isn't estimating capacity degradation, just a session's
energy delta against a capacity figure that's already known, so there's no equivalent
circularity. `current_energy_kwh` is the one field confirmed to reliably come from the vehicle
(`realtimePower`) and has no fallback.

**Response 200:**
```json
{
  "fetched_at": "2026-08-12T14:30:00Z",
  "battery_usage": {
    "total_battery_capacity_kwh": 61.8,
    "power_usage_today_kwh": 4.2,
    "power_usage_since_last_charge_kwh": 12.6,
    "last_charge_added_kwh": 38.4,
    "current_energy_kwh": 34.6,
    "mileage_today_km": 21.3,
    "mileage_since_last_charge_km": 143.7,
    "estimated_fields": []
  }
}
```

`total_battery_capacity_kwh` is the vehicle's own self-reported capacity (raw `totalBatteryCapacity`
/ 10.0) -- distinct from `app_settings.battery_nameplate_kwh`, which is the owner-configured
nameplate figure used for the SOH estimate. The kWh fields (`power_usage_*`, `last_charge_added_kwh`,
`current_energy_kwh`) apply the same correction-factor technique as the reference implementation
(`SAIC-iSmart-API/saic-python-mqtt-gateway`): `correction_factor = battery_nameplate_kwh /
total_battery_capacity_kwh` (1.0 if the vehicle doesn't report a capacity, or reports <= 0),
applied as `round((correction_factor * raw_value) / 10.0, 2)` to `powerUsageOfDay`,
`powerUsageSinceLastCharge`, `lastChargeEndingPower`, and `realtimePower`, so the numbers stay
consistent with our own nameplate setting rather than the vehicle's possibly-inaccurate
self-report. `current_energy_kwh` (source: `realtimePower`) is the battery's current usable
energy content -- despite the misleading raw field name, this is confirmed (via
`rvs_charge_status.py`'s `soc_kwh` computation, the identical formula) to be an energy quantity,
not an instantaneous power/rate figure.
`mileage_today_km`/`mileage_since_last_charge_km` are `mileageOfDay`/`mileageSinceLastCharge` raw
/ 10.0, validated `0 <= raw <= 65535` (same inclusive-range pattern already used elsewhere in
`saic_client.py`). Every field individually nullable.

**History-derived fallback** (`backend/src/app/services/battery_usage.py`'s
`compute_derived_battery_usage`, called from `backend/src/app/api/battery_usage.py`): applies
independently to each of `total_battery_capacity_kwh`, `power_usage_today_kwh`,
`power_usage_since_last_charge_kwh`, `last_charge_added_kwh`, `mileage_today_km`, and
`mileage_since_last_charge_km` -- only when the vehicle-reported value for that specific field is
`null`. `current_energy_kwh` never falls back (see above).
- `total_battery_capacity_kwh` falls back to `app_settings.battery_nameplate_kwh` directly.
- `power_usage_today_kwh` sums SOC *decreases* between consecutive `car_snapshot` rows (soc_pct
  column) whose later timestamp falls on the server's local calendar day, x effective capacity.
  Increases (charging) are ignored, not netted -- this approximates "energy used driving today",
  matching the vehicle stat's apparent semantics.
- `mileage_today_km` is the latest known `odometer_km` minus the first `odometer_km` recorded
  on today's local calendar day.
- A "last completed charge cycle" is detected by scanning `car_snapshot.is_charging` for a
  `True -> False` transition; the last `True` row is treated as the charge's end point (odometer
  gaps between refreshes mean the true end SOC may be slightly higher -- same caveat as SOH's
  cycle detection). If no completed cycle exists in the queried window (e.g. still mid-charge,
  as observed 2026-08-15), `last_charge_added_kwh`, `power_usage_since_last_charge_kwh`, and
  `mileage_since_last_charge_km` all stay `null` rather than guessing.
  - `last_charge_added_kwh` = (end SOC - start SOC) x effective capacity, only if positive.
  - `power_usage_since_last_charge_kwh` = summed SOC decreases from the charge's end point to now.
  - `mileage_since_last_charge_km` = latest odometer minus odometer at the charge's end point.
- Effective capacity is `total_battery_capacity_kwh` (after its own fallback above is applied),
  so all derived kWh figures stay internally consistent with each other.
- Queries the last 30 days of `car_snapshot` history (same default window as `/api/history`).

`estimated_fields` lists which field names (from the six above) were filled by the history
fallback rather than the vehicle's own report -- empty when the vehicle reports everything
itself. The frontend must visibly flag any field named here as an estimate (not hide the
distinction), same spirit as the SOH estimate's "must never present as authoritative" rule.

**Response 404:** No snapshot exists yet (same as `/api/latest`).

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
  "longitude": null,
  "doors": {
    "locked": true,
    "driver_door_open": false,
    "passenger_door_open": false,
    "rear_left_door_open": false,
    "rear_right_door_open": false,
    "bonnet_open": false,
    "boot_open": false,
    "driver_window_open": false,
    "passenger_window_open": false,
    "rear_left_window_open": false,
    "rear_right_window_open": false,
    "sunroof_open": false
  }
}
```

`doors` is sourced from `basicVehicleStatus` (already fetched every refresh, no extra live SAIC
call) and is nullable as a whole (if `basicVehicleStatus` is missing) with every field inside also
individually nullable. Decode semantics (`value > 0` -> locked / open) are confirmed against
`SAIC-iSmart-API/saic-python-mqtt-gateway`'s published decode logic and Home Assistant
`device_class` mappings (`lock`: >0 = locked; `door`/`window`: >0 = open) -- not guessed.

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
