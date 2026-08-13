"""Pydantic schemas matching docs/architecture/api_contract.md exactly.

Field names are the contract -- do not rename independently of that document.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_serializer


def _iso_z(value: datetime) -> str:
    """Render a datetime as ISO8601 with a trailing 'Z' (contract examples use this)."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class Doors(BaseModel):
    locked: bool | None = None
    driver_door_open: bool | None = None
    passenger_door_open: bool | None = None
    rear_left_door_open: bool | None = None
    rear_right_door_open: bool | None = None
    bonnet_open: bool | None = None
    boot_open: bool | None = None
    driver_window_open: bool | None = None
    passenger_window_open: bool | None = None
    rear_left_window_open: bool | None = None
    rear_right_window_open: bool | None = None
    sunroof_open: bool | None = None


class Snapshot(BaseModel):
    soc_pct: float | None = None
    range_bms_km: float | None = None
    range_imcu_km: float | None = None
    is_charging: bool | None = None
    charging_current: float | None = None
    plug_status: str | None = None
    battery_12v_voltage: float | None = None
    odometer_km: float | None = None
    cabin_temp_c: float | None = None
    tyre_pressure_fl: float | None = None
    tyre_pressure_fr: float | None = None
    tyre_pressure_rl: float | None = None
    tyre_pressure_rr: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    doors: Doors | None = None


class RefreshResponse(BaseModel):
    source: Literal["live", "cached"]
    fetched_at: datetime
    snapshot: Snapshot

    @field_serializer("fetched_at")
    def _serialize_fetched_at(self, value: datetime) -> str:
        return _iso_z(value)


class LatestResponse(BaseModel):
    fetched_at: datetime
    snapshot: Snapshot

    @field_serializer("fetched_at")
    def _serialize_fetched_at(self, value: datetime) -> str:
        return _iso_z(value)


class HistorySnapshot(BaseModel):
    fetched_at: datetime
    snapshot: Snapshot

    @field_serializer("fetched_at")
    def _serialize_fetched_at(self, value: datetime) -> str:
        return _iso_z(value)


class HistoryResponse(BaseModel):
    snapshots: list[HistorySnapshot]


class ErrorResponse(BaseModel):
    error: str
    detail: str


class SettingsResponse(BaseModel):
    schedule_enabled: bool
    schedule_interval_minutes: int
    min_refresh_gap_minutes: int
    battery_nameplate_kwh: float


class SettingsUpdateRequest(BaseModel):
    """Partial or full update -- unset fields are left unchanged."""

    schedule_enabled: bool | None = None
    schedule_interval_minutes: int | None = Field(default=None, gt=0)
    min_refresh_gap_minutes: int | None = Field(default=None, gt=0)
    battery_nameplate_kwh: float | None = Field(default=None, gt=0)


class CurrentJourney(BaseModel):
    id: int
    distance_km: float


class GpsInfo(BaseModel):
    latitude: float
    longitude: float
    altitude_m: int | None = None
    heading_deg: int | None = None
    speed_kmh: float | None = None


class HvBatteryInfo(BaseModel):
    """Main traction battery pack voltage/power -- distinct from the 12V auxiliary
    battery (Snapshot.battery_12v_voltage)."""

    voltage_v: float | None = None
    power_kw: float | None = None


class BatteryHeatingInfo(BaseModel):
    active: bool | None = None
    stop_reason: str | None = None


class ScheduledChargingInfo(BaseModel):
    mode: str
    start_time: str
    end_time: str


class ObcAcInputInfo(BaseModel):
    """On-board (AC) charger input -- what the wall/EVSE is delivering during
    AC charging, distinct from `hv_battery` (the pack's own state)."""

    current_a: float
    voltage_v: float
    power_single_phase_kw: float
    power_three_phase_kw: float


class AdvancedInfo(BaseModel):
    """See GET /api/latest/advanced in api_contract.md for field provenance."""

    engine_running: bool | None = None
    is_parked: bool | None = None
    hand_brake_on: bool | None = None
    main_beam_on: bool | None = None
    dipped_beam_on: bool | None = None
    side_light_on: bool | None = None
    exterior_temp_c: float | None = None
    remote_climate_status: str | None = None
    rear_window_heat_on: bool | None = None
    front_left_seat_heat_level: int | None = None
    front_right_seat_heat_level: int | None = None
    current_journey: CurrentJourney | None = None
    gps: GpsInfo | None = None
    has_active_alerts: bool | None = None
    vehicle_reported_at: str | None = None
    charging_pile_id: str | None = None
    charging_pile_supplier: str | None = None
    charging_type_raw: int | None = None
    charging_working_voltage_raw: int | None = None
    charging_working_current_raw: int | None = None
    charging_remaining_time_minutes: int | None = None
    charging_port_locked: bool | None = None
    target_soc_pct: int | None = None
    charge_current_limit: str | None = None
    bms_charging_status: str | None = None
    charging_stop_reason: str | None = None
    hv_battery: HvBatteryInfo | None = None
    battery_heating: BatteryHeatingInfo | None = None
    scheduled_charging: ScheduledChargingInfo | None = None
    obc_ac_input: ObcAcInputInfo | None = None
    raw_undecoded: dict[str, int | list[object] | None] = Field(default_factory=dict)


class AdvancedResponse(BaseModel):
    fetched_at: datetime
    advanced: AdvancedInfo

    @field_serializer("fetched_at")
    def _serialize_fetched_at(self, value: datetime) -> str:
        return _iso_z(value)


class BatteryUsage(BaseModel):
    total_battery_capacity_kwh: float | None = None
    power_usage_today_kwh: float | None = None
    power_usage_since_last_charge_kwh: float | None = None
    last_charge_added_kwh: float | None = None
    current_energy_kwh: float | None = None
    mileage_today_km: float | None = None
    mileage_since_last_charge_km: float | None = None


class BatteryUsageResponse(BaseModel):
    fetched_at: datetime
    battery_usage: BatteryUsage

    @field_serializer("fetched_at")
    def _serialize_fetched_at(self, value: datetime) -> str:
        return _iso_z(value)
