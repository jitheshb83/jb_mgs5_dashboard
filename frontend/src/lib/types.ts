/**
 * Types matching docs/architecture/api_contract.md exactly.
 * Field names here are final per the contract — do not rename independently.
 */

/**
 * Shared Snapshot object, returned by /api/refresh, /api/latest, and within
 * /api/history's `snapshots` array. Any field can be null if the SAIC API
 * didn't return it for that fetch.
 *
 * Judgment call: the contract's example only shows `plug_status: "unplugged"`
 * and doesn't enumerate the full set of possible values, so it's typed as a
 * plain string (not a union) here rather than guessing the other values.
 */
export interface Snapshot {
  soc_pct: number | null;
  range_bms_km: number | null;
  range_imcu_km: number | null;
  is_charging: boolean | null;
  charging_current: number | null;
  plug_status: string | null;
  battery_12v_voltage: number | null;
  odometer_km: number | null;
  cabin_temp_c: number | null;
  tyre_pressure_fl: number | null;
  tyre_pressure_fr: number | null;
  tyre_pressure_rl: number | null;
  tyre_pressure_rr: number | null;
  latitude: number | null;
  longitude: number | null;
  doors: Doors | null;
}

/**
 * Lock/door/window/bonnet/boot/sunroof state, sourced from `basicVehicleStatus`.
 * The whole object is nullable (if `basicVehicleStatus` is missing) and every
 * field inside is also individually nullable, per api_contract.md.
 */
export interface Doors {
  locked: boolean | null;
  driver_door_open: boolean | null;
  passenger_door_open: boolean | null;
  rear_left_door_open: boolean | null;
  rear_right_door_open: boolean | null;
  bonnet_open: boolean | null;
  boot_open: boolean | null;
  driver_window_open: boolean | null;
  passenger_window_open: boolean | null;
  rear_left_window_open: boolean | null;
  rear_right_window_open: boolean | null;
  sunroof_open: boolean | null;
}

export type RefreshSource = "live" | "cached";

export interface RefreshResponse {
  source: RefreshSource;
  fetched_at: string;
  snapshot: Snapshot;
}

export interface LatestResponse {
  fetched_at: string;
  snapshot: Snapshot;
}

/**
 * One entry in GET /api/history's `snapshots` array. `Snapshot` itself carries
 * no timestamp (it's purely vehicle-state fields), so each history entry wraps
 * it with its own `fetched_at` -- the same `{fetched_at, snapshot}` shape
 * already used by /api/refresh and /api/latest. See api_contract.md's
 * 2026-08-12 correction note on GET /api/history.
 */
export interface HistorySnapshot {
  fetched_at: string;
  snapshot: Snapshot;
}

export interface HistoryResponse {
  snapshots: HistorySnapshot[];
}

export interface HistoryParams {
  from?: string;
  to?: string;
  limit?: number;
}

export interface Settings {
  schedule_enabled: boolean;
  schedule_interval_minutes: number;
  min_refresh_gap_minutes: number;
  battery_nameplate_kwh: number;
}

/**
 * Shape of GET /api/latest/advanced's `advanced` object. Per api_contract.md,
 * the exact field list is still being finalized backend-side, so this is
 * intentionally a loose index signature rather than a fixed field list --
 * the frontend renders whatever keys show up. `raw_undecoded`, if present, is
 * a nested object of raw SAIC field name -> value pairs that couldn't be
 * confidently decoded.
 */
export interface AdvancedInfo {
  raw_undecoded?: Record<string, unknown> | null;
  [key: string]: unknown;
}

export interface AdvancedResponse {
  fetched_at: string;
  advanced: AdvancedInfo;
}

/**
 * Shape of GET /api/latest/battery-usage's `battery_usage` object. Fixed, known field list
 * per api_contract.md.
 *
 * `estimated_fields` lists which of the other field names (by key) were filled by the
 * history-derived fallback rather than the vehicle's own report, per the 2026-08-15 contract
 * correction -- the UI must visibly flag those as estimates, not hide the distinction.
 */
export interface BatteryUsage {
  total_battery_capacity_kwh: number | null;
  power_usage_today_kwh: number | null;
  power_usage_since_last_charge_kwh: number | null;
  last_charge_added_kwh: number | null;
  current_energy_kwh: number | null;
  mileage_today_km: number | null;
  mileage_since_last_charge_km: number | null;
  /** Not vehicle-reported -- server-computed as power_usage / mileage x 100, per
   * api_contract.md's 2026-08-16 addition. Null if either input is null or mileage is 0. */
  efficiency_today_kwh_per_100km: number | null;
  efficiency_since_last_charge_kwh_per_100km: number | null;
  estimated_fields: string[];
}

export interface BatteryUsageResponse {
  fetched_at: string;
  battery_usage: BatteryUsage;
}

/**
 * One entry in GET /api/soh's `estimates` array, most-recent-first (same convention as
 * /api/history) -- see api_contract.md's "implemented 2026-08-15" note. `basis` is currently
 * always "current_energy_kwh_delta" (soh_methodology.md's shipped v1 method).
 */
export interface SohEstimateItem {
  computed_at: string;
  soh_pct: number;
  usable_kwh_estimate: number;
  basis: string;
}

export interface SohResponse {
  estimates: SohEstimateItem[];
  nameplate_usable_kwh: number;
}

/** Error response shape used by all backend error responses (400/404/502/etc). */
export interface ApiErrorBody {
  error: string;
  detail: string;
}
