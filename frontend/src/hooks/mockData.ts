/**
 * Mock, contract-shaped fixtures used by tests/ (not by any hook at runtime --
 * every hook calls the real backend via lib/api.ts). Two Snapshot variants
 * are provided:
 *  - mockSnapshotRealistic: plausible values for normal dashboard rendering.
 *  - mockSnapshotAllNull: every field null, for exercising placeholder
 *    rendering / edge cases (per testing_strategy.md).
 */

import type { Doors, Settings, Snapshot } from "../lib/types";

export const mockDoorsRealistic: Doors = {
  locked: true,
  driver_door_open: false,
  passenger_door_open: false,
  rear_left_door_open: false,
  rear_right_door_open: false,
  bonnet_open: false,
  boot_open: false,
  driver_window_open: false,
  passenger_window_open: false,
  rear_left_window_open: false,
  rear_right_window_open: false,
  sunroof_open: false,
};

export const mockDoorsAllNull: Doors = {
  locked: null,
  driver_door_open: null,
  passenger_door_open: null,
  rear_left_door_open: null,
  rear_right_door_open: null,
  bonnet_open: null,
  boot_open: null,
  driver_window_open: null,
  passenger_window_open: null,
  rear_left_window_open: null,
  rear_right_window_open: null,
  sunroof_open: null,
};

export const mockSnapshotRealistic: Snapshot = {
  soc_pct: 78.0,
  range_bms_km: 310.0,
  range_imcu_km: 295.0,
  is_charging: false,
  charging_current: null,
  plug_status: "unplugged",
  battery_12v_voltage: 12.6,
  odometer_km: 4210.5,
  cabin_temp_c: 21.0,
  tyre_pressure_fl: 2.4,
  tyre_pressure_fr: 2.4,
  tyre_pressure_rl: 2.3,
  tyre_pressure_rr: 2.3,
  latitude: null,
  longitude: null,
  doors: mockDoorsRealistic,
};

export const mockSnapshotCharging: Snapshot = {
  ...mockSnapshotRealistic,
  soc_pct: 54.0,
  is_charging: true,
  charging_current: 16.0,
  plug_status: "charging",
};

export const mockSnapshotAllNull: Snapshot = {
  soc_pct: null,
  range_bms_km: null,
  range_imcu_km: null,
  is_charging: null,
  charging_current: null,
  plug_status: null,
  battery_12v_voltage: null,
  odometer_km: null,
  cabin_temp_c: null,
  tyre_pressure_fl: null,
  tyre_pressure_fr: null,
  tyre_pressure_rl: null,
  tyre_pressure_rr: null,
  latitude: null,
  longitude: null,
  doors: mockDoorsAllNull,
};

export const mockSettings: Settings = {
  schedule_enabled: false,
  schedule_interval_minutes: 120,
  min_refresh_gap_minutes: 30,
  battery_nameplate_kwh: 62.1,
};

export const mockHistory: Snapshot[] = [mockSnapshotRealistic, mockSnapshotCharging];

export function mockDelay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
