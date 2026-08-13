# Data Model (SQLite)

Single file, e.g. `backend/data/mgs5.db`. No external DB server. This file must never be committed
to git — add `backend/data/*.db` to `.gitignore`.

## car_snapshot

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Autoincrement |
| fetched_at | TIMESTAMP NOT NULL | When this snapshot was retrieved |
| soc_pct | REAL | State of charge, % |
| range_bms_km | REAL | BMS-based range estimate |
| range_imcu_km | REAL | IMCU-based range estimate |
| is_charging | BOOLEAN | |
| charging_current | REAL | Nullable — not always reported |
| plug_status | TEXT | e.g. "plugged", "unplugged" |
| battery_12v_voltage | REAL | Auxiliary battery — monitor for drain risk |
| odometer_km | REAL | |
| cabin_temp_c | REAL | |
| tyre_pressure_fl | REAL | |
| tyre_pressure_fr | REAL | |
| tyre_pressure_rl | REAL | |
| tyre_pressure_rr | REAL | |
| latitude | REAL | Nullable, only if location view is in scope |
| longitude | REAL | Nullable |
| doors_json | TEXT | Nullable. JSON-encoded `doors` object (lock + door + window + bonnet/boot/sunroof state) per `api_contract.md`'s Snapshot shape. Decoded from `basicVehicleStatus` at insert time and stored per-snapshot (unlike the advanced-info/battery-usage pages, which decode on demand from `raw_json` and aren't stored separately) so it's available in `/api/history` rows, not just the latest. |
| raw_json | TEXT NOT NULL | Full raw SAIC API response — never dropped, allows re-parsing if field mappings change |

Index: `fetched_at` (for history range queries).

## app_settings

Single-row-per-key config table.

| key | value | Notes |
|---|---|---|
| schedule_enabled | "false" | |
| schedule_interval_minutes | "120" | |
| min_refresh_gap_minutes | "30" | Locked decision — see `docs/planning/decisions_log.md` |
| battery_nameplate_kwh | "62.1" | Locked decision — MGS5 Luxury usable capacity |

Stored as TEXT and cast on read — keeps the table generic, avoids schema migrations for new settings.

## soh_estimate (derived)

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Autoincrement |
| computed_at | TIMESTAMP NOT NULL | When this estimate was calculated |
| cycle_start_snapshot_id | INTEGER FK → car_snapshot.id | Start of the full-charge cycle used |
| cycle_end_snapshot_id | INTEGER FK → car_snapshot.id | End of the full-charge cycle used |
| soh_pct | REAL | Computed estimate |
| usable_kwh_estimate | REAL | Computed estimate |
| basis | TEXT | e.g. "soc_delta_fallback" or "current_integration" — see `soh_methodology.md` |

## Migration approach

v1 has no migration framework — schema is created fresh via `CREATE TABLE IF NOT EXISTS` on
backend startup. If the schema needs to change after real data exists, that's a deliberate
decision point (ask the user), not something to script around silently.
