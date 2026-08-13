"""Decode GET /api/latest/advanced from the stored `raw_json` of the latest snapshot.

Surfaces every other known field from `vehicle_status`/`charging_management_data` that isn't
already part of the core Snapshot or `doors` object. Decoded on demand from the stored
`raw_json` at request time -- no new DB column, no extra live SAIC call, no historical storage
(reflects only the latest snapshot).

Decode conventions confirmed against SAIC-iSmart-API/saic-python-mqtt-gateway source (read
directly, not guessed -- see individual functions below for which file/method), the installed
`saic_ismart_client_ng` library's own `ChrgMgmtData` dataclass properties (`decoded_voltage`,
`decoded_power`, `is_battery_heating`, `charging_port_locked`, `charging_stop_reason`,
`heating_stop_reason`, `bms_charging_status` -- reimplemented as small functions here rather than
reconstructing a `ChrgMgmtData` instance from the stored dict, to match this file's existing
style, but the formulas/enum lookups are copied from those properties' real source), and the
actual ASN.1 wire-protocol schema published in `SAIC-iSmart-API/documentation`
(`ASN.1 schema/v3_0/ApplicationData.asn1`'s `OTAChrgMangDataResp`/`RvsChargingStatus`,
`ASN.1 schema/v2_1/ApplicationData.asn1`'s `RvsBasicStatus25857`) -- the authoritative field
list/types this whole API is generated from, used both to confirm field names/groupings and, for
`canBusActive`/`handBrake`/doors/windows/lock, that they are true wire-protocol `BOOLEAN`s (not
just an `int > 0` convention the client library happens to apply):
  - `src/status_publisher/vehicle/basic_vehicle_status.py`: engine/parked state, hand brake,
    lights, remote climate state, rear window heat, seat heat levels, current journey.
  - `src/utils.py`: `to_remote_climate` (the exact int->string mapping for remoteClimateStatus),
    `is_valid_temperature` (same sentinel convention already used for cabin_temp_c).
  - `src/status_publisher/vehicle/gps_position.py`: GPS lat/long/altitude/heading/speed scaling
    and the FIX_2D/FIX_3d validity gate.
  - `src/status_publisher/charge/chrg_mgmt_data.py`: charging remaining time validity flag,
    scheduled-charging reservation fields (`ScheduledChargingMode` + start/end HH:MM), on-board
    AC charger input current/voltage/power formulas.

Verified against a real live vehicle response on 2026-08-13 (see project session notes): every
field name below was cross-checked against an actual captured `raw_json` payload, not just the
dataclass definitions, to confirm nothing available from the API was silently dropped -- this is
also what caught scheduled-charging and OBC AC-input decodes that a first pass had missed (see
`chrg_mgmt_data.py` above, found on a second, deeper read of the reference project).

Fields with **no** confirmed decode anywhere in the installed library, the reference project, or
the ASN.1 schema are surfaced under `raw_undecoded` with their original SAIC field name, per
CLAUDE.md's "no fabricated behavior" rule, rather than an invented meaning -- the frontend
attaches a human-readable label to each for display (translating known automotive/EV
abbreviations -- BMS, CCU, PTC, FOTA, IMCU, etc. -- into plain English) without claiming to know
what the *value* means; see frontend/src/lib/rawFieldLabels.ts for that lookup and its own
sourcing notes.
"""

from __future__ import annotations

from datetime import UTC, datetime

from saic_ismart_client_ng.api.schema import GpsStatus
from saic_ismart_client_ng.api.vehicle_charging import (
    BmsChargingStatusCode,
    ChargeCurrentLimitCode,
    ChargingStopReason,
    HeatingStopReason,
    ScheduledChargingMode,
    TargetBatteryCode,
)

# BasicVehicleStatus fields with no confirmed decode in saic_ismart_client_ng or
# saic-python-mqtt-gateway (checked both -- see module docstring). Surfaced raw rather
# than guessed. fuelLevelPrc/fuelRange/fuelRangeElec are fossil-fuel fields the library
# supports for PHEV/ICE models but that are meaningless (always a sentinel) for this BEV --
# still surfaced raw rather than silently dropped, per "don't miss any data".
_RAW_UNDECODED_BASIC_FIELDS = (
    "lastKeySeen",
    "steeringHeatLevel",
    "steeringWheelHeatFailureReason",
    "timeOfLastCANBUSActivity",
    "vehElecRngDsp",
    "clstrDspdFuelLvlSgmt",
    "extendedData1",
    "extendedData2",
    "powerMode",
    "vehicleAlarmStatus",
    "wheelTyreMonitorStatus",
    "canBusActive",
    "fuelLevelPrc",
    "fuelRange",
    "fuelRangeElec",
)

# ChrgMgmtData fields with no confirmed decode (checked both sources -- see module
# docstring). Mostly charge-scheduling reservation command/response codes and raw
# AC-input/charging-door signals with no independently confirmed meaning.
_RAW_UNDECODED_CHRG_FIELDS = (
    "bmsAdpPubChrgSttnDspCmd",
    "bmsChrgCtrlDspCmd",
    "bmsChrgOtptCrntReq",
    "bmsChrgOtptCrntReqV",
    "bmsPTCHeatSpRsn",
    "ccuOffBdChrgrPlugOn",
    "ccuOnbdChrgrPlugOn",
    "chrgngAddedElecRng",
    "chrgngAddedElecRngV",
    "chrgngDoorOpenCnd",
    "chrgngDoorPosSts",
    "chrgngSpdngTime",
    "chrgngSpdngTimeV",
    "clstrElecRngToEPT",
    "disChrgngRmnngTime",
    "disChrgngRmnngTimeV",
    "imcuChrgngEstdElecRng",
    "imcuChrgngEstdElecRngV",
    "imcuDschrgngEstdElecRng",
    "imcuDschrgngEstdElecRngV",
    "imcuVehElecRngV",
    # bmsReserCtrlDspCmd/bmsReserSp*/bmsReserSt* -> now decoded, see
    # `scheduled_charging`. onBdChrgrAltrCrntInptCrnt/Vol -> now decoded, see
    # `obc_ac_input`.
)

# RvsChargeStatus fields with no confirmed decode, or that duplicate a field already
# captured elsewhere from a different source (rvs.mileage duplicates
# basicVehicleStatus.mileage -- already the Snapshot's odometer_km -- so it's
# intentionally NOT re-surfaced here to avoid a misleading second "mileage" value).
# Prefixed with "rvs" where the bare SAIC name would collide with a
# basicVehicleStatus field already in _RAW_UNDECODED_BASIC_FIELDS (extendedData1/2)
# or a distinct field with the same name on basicVehicleStatus (fuelRangeElec).
_RAW_UNDECODED_RVS_FIELDS = (
    ("rvsChargingDuration", "chargingDuration"),
    ("rvsChargingElectricityPhase", "chargingElectricityPhase"),
    ("rvsEndTime", "endTime"),
    ("rvsExtendedData1", "extendedData1"),
    ("rvsExtendedData2", "extendedData2"),
    ("rvsExtendedData3", "extendedData3"),
    ("rvsExtendedData4", "extendedData4"),
    ("rvsFotaLowestVoltage", "fotaLowestVoltage"),
    ("rvsFuelRangeElec", "fuelRangeElec"),
    ("rvsStartTime", "startTime"),
    ("rvsStaticEnergyConsumption", "staticEnergyConsumption"),
    # realtimePower -> now decoded as current_energy_kwh in
    # GET /api/latest/battery-usage (battery_usage.py), not surfaced raw here.
)


def _get_dict(d: dict[str, object], key: str) -> dict[str, object]:
    value = d.get(key)
    return value if isinstance(value, dict) else {}


def _get_int(d: dict[str, object], key: str) -> int | None:
    value = d.get(key)
    return value if isinstance(value, int) else None


def _get_str(d: dict[str, object], key: str) -> str | None:
    value = d.get(key)
    return value if isinstance(value, str) else None


def _int_to_bool(value: int | None) -> bool | None:
    return None if value is None else value > 0


def _decode_temperature(value: int | None) -> float | None:
    # Same validity/sentinel convention as interiorTemperature in saic_client.py's
    # map_to_snapshot_fields (confirmed via utils.is_valid_temperature).
    if value is None or not (-127 <= value <= 127) or value == 87:
        return None
    return float(value)


def _decode_remote_climate(value: int | None) -> str | None:
    # Confirmed mapping: SAIC-iSmart-API/saic-python-mqtt-gateway src/utils.py's
    # to_remote_climate(). Applied to basicVehicleStatus.remoteClimateStatus (confirmed
    # via src/status_publisher/vehicle/basic_vehicle_status.py's call site).
    if value is None:
        return None
    return {0: "off", 1: "blowingonly", 2: "on", 5: "front"}.get(value, f"unknown ({value})")


def _decode_target_soc(value: int | None) -> int | None:
    # Mirrors ChrgMgmtData.charge_target_soc property, and mqtt-gateway's guard of not
    # attempting the enum lookup for the "ignore" sentinel (0).
    if value is None or value == 0:
        return None
    try:
        return TargetBatteryCode(value).percentage
    except ValueError:
        return None


def _decode_charge_current_limit(value: int | None) -> str | None:
    # Mirrors ChrgMgmtData.charge_current_limit property, same "ignore" sentinel guard.
    if value is None or value == 0:
        return None
    try:
        return ChargeCurrentLimitCode(value).limit
    except ValueError:
        return None


def _decode_current_journey(basic: dict[str, object]) -> dict[str, object] | None:
    journey_id = _get_int(basic, "currentJourneyId")
    journey_distance = _get_int(basic, "currentJourneyDistance")
    if journey_id is None or journey_distance is None:
        return None
    return {"id": journey_id, "distance_km": round(journey_distance / 10.0, 1)}


def _decode_is_parked(engine_status: int | None, hand_brake: int | None) -> bool | None:
    """Mirrors BasicVehicleStatus.is_parked (engineStatus != 1 or handBrake == 1),
    but treats a missing field as "no signal from that source" rather than
    letting `None != 1` (True in Python) force a wrong True when only one of
    the two raw fields is present.
    """
    engine_signal = None if engine_status is None else engine_status != 1
    hand_brake_signal = None if hand_brake is None else hand_brake == 1
    if engine_signal is None:
        return hand_brake_signal
    if hand_brake_signal is None:
        return engine_signal
    return engine_signal or hand_brake_signal


def _decode_hv_battery(chrg: dict[str, object]) -> dict[str, float | None] | None:
    """HV (main traction) battery pack voltage/power -- distinct from
    battery_12v_voltage (the 12V auxiliary battery). Formulas copied from
    ChrgMgmtData.decoded_voltage/decoded_current/decoded_power's real source
    (bmsPackVol * 0.25; bmsPackCrnt * 0.05 - 1000.0; current * voltage / 1000),
    not guessed -- reimplemented here since this module works from a parsed
    dict, not a live ChrgMgmtData instance.
    """
    raw_voltage = _get_int(chrg, "bmsPackVol")
    raw_current = _get_int(chrg, "bmsPackCrnt")
    if raw_voltage is None:
        return None
    voltage = raw_voltage * 0.25
    result: dict[str, float | None] = {"voltage_v": round(voltage, 2), "power_kw": None}
    if raw_current is not None:
        current = raw_current * 0.05 - 1000.0
        result["power_kw"] = round(current * voltage / 1000.0, 3)
    return result


def _decode_battery_heating(ptc_heat_req: int | None, ptc_heat_resp: int | None) -> dict[str, object]:
    # Mirrors ChrgMgmtData.is_battery_heating (bmsPTCHeatReqDspCmd == 1) and
    # .heating_stop_reason (HeatingStopReason.to_code(bmsPTCHeatResp)). An
    # unrecognized code returns None (not a guessed reason), matching
    # HeatingStopReason.to_code's own None-on-ValueError behavior.
    active = None if ptc_heat_req is None else ptc_heat_req == 1
    stop_reason = None
    if ptc_heat_resp is not None:
        code = HeatingStopReason.to_code(ptc_heat_resp)
        stop_reason = code.name if code is not None else None
    return {"active": active, "stop_reason": stop_reason}


def _decode_exactly_one(value: int | None) -> bool | None:
    """For fields whose only confirmed convention is an exact `== 1` check
    (not the `>0` convention `_int_to_bool` uses for doors/lights/etc.):
    ChrgMgmtData.charging_port_locked (`ccuEleccLckCtrlDspCmd == 1`) and
    BasicVehicleStatus.is_parked's own use of `handBrake == 1`. Using `>0`
    here would misreport any other nonzero code as True -- confirmed wrong
    for ccuEleccLckCtrlDspCmd against a real vehicle (captured value 2).
    """
    return None if value is None else value == 1


def _decode_charging_stop_reason(value: int | None) -> str | None:
    # Mirrors ChrgMgmtData.charging_stop_reason (ChargingStopReason.to_code, which
    # always returns a valid member -- falls back to OTHER_REASON on an
    # unrecognized code rather than None).
    if value is None:
        return None
    return ChargingStopReason.to_code(value).name


def _decode_bms_charging_status(value: int | None) -> str | None:
    # Mirrors ChrgMgmtData.bms_charging_status (BmsChargingStatusCode.to_code) --
    # a more granular status than the core Snapshot's boolean is_charging (e.g.
    # distinguishes "charge done" / "fault" / "unplugged", not just on/off).
    if value is None:
        return None
    code = BmsChargingStatusCode.to_code(value)
    return code.name if code is not None else None


def _decode_alerts(vehicle_status: dict[str, object]) -> tuple[bool | None, list[object] | None]:
    """Returns (has_active_alerts, raw_alert_data_array)."""
    extended = _get_dict(vehicle_status, "extendedVehicleStatus")
    alert_data = extended.get("alertDataSum")
    if not isinstance(alert_data, list):
        return None, None
    # Individual index meanings are not confirmed anywhere -- only a safe
    # "is anything non-zero" check is derived; the raw array is also kept so
    # nothing is lost even though we can't label each entry.
    has_active = any(isinstance(v, int) and v != 0 for v in alert_data)
    return has_active, alert_data


def _decode_vehicle_reported_at(status_time: int | None) -> str | None:
    # statusTime is epoch seconds (confirmed by cross-checking a real captured
    # value against the known fetch time it was captured at -- not documented
    # in either source, but the unit was directly verified this way).
    if status_time is None or status_time <= 0:
        return None
    try:
        return datetime.fromtimestamp(status_time, tz=UTC).isoformat().replace("+00:00", "Z")
    except (ValueError, OSError, OverflowError):
        return None


def _decode_scheduled_charging(chrg: dict[str, object]) -> dict[str, object] | None:
    """Mirrors chrg_mgmt_data.py's __publish_charging_schedule exactly: `null`
    unless all five reservation fields are present; `mode` via
    `ScheduledChargingMode(bmsReserCtrlDspCmd)` (DISABLED/UNTIL_CONFIGURED_SOC/
    UNTIL_CONFIGURED_TIME); start/end are `HH:MM` built from the paired
    hour/minute fields (bmsReserSt* = start, bmsReserSp* = end -- confirmed by
    reading which variable each feeds into in the reference source, not
    guessed from the field names alone, which don't make "Sp" = end obvious).
    """
    start_hour = _get_int(chrg, "bmsReserStHourDspCmd")
    start_minute = _get_int(chrg, "bmsReserStMintueDspCmd")
    end_hour = _get_int(chrg, "bmsReserSpHourDspCmd")
    end_minute = _get_int(chrg, "bmsReserSpMintueDspCmd")
    mode_raw = _get_int(chrg, "bmsReserCtrlDspCmd")
    if (
        start_hour is None
        or start_minute is None
        or end_hour is None
        or end_minute is None
        or mode_raw is None
        or mode_raw == 0
    ):
        return None
    try:
        mode = ScheduledChargingMode(mode_raw)
    except ValueError:
        return None
    return {
        "mode": mode.name,
        "start_time": f"{start_hour:02d}:{start_minute:02d}",
        "end_time": f"{end_hour:02d}:{end_minute:02d}",
    }


def _decode_obc_ac_input(chrg: dict[str, object]) -> dict[str, float] | None:
    """On-board (AC) charger input current/voltage/power -- what the wall/EVSE
    is delivering during AC charging (distinct from `hv_battery`, the pack's
    own state). Formulas copied verbatim from chrg_mgmt_data.py's
    __publish_obc_data -- current_a and voltage_v computed the same way the
    reference computes its OBC_CURRENT/OBC_VOLTAGE topics; the two power
    figures computed directly from the raw pair exactly as the reference's
    OBC_POWER_SINGLE_PHASE/OBC_POWER_THREE_PHASE topics are (NOT simply
    voltage_v * current_a * sqrt(3) -- verified numerically against the
    reference's own formula, which are not algebraically equivalent to that
    naive expansion; the three-phase figure is exactly 1/3 of it), then
    converted from the reference's native watts to kW to match `hv_battery`'s
    units on this same page.
    """
    raw_current = _get_int(chrg, "onBdChrgrAltrCrntInptCrnt")
    raw_voltage = _get_int(chrg, "onBdChrgrAltrCrntInptVol")
    if raw_current is None or raw_voltage is None:
        return None
    single_phase_w = 2.0 * raw_voltage * raw_current / 5.0
    three_phase_w = 3**0.5 * 2.0 * raw_voltage * raw_current / 15.0
    return {
        "current_a": round(raw_current / 5.0, 1),
        "voltage_v": round(2.0 * raw_voltage, 1),
        "power_single_phase_kw": round(single_phase_w / 1000.0, 3),
        "power_three_phase_kw": round(three_phase_w / 1000.0, 3),
    }


def _decode_gps(vehicle_status: dict[str, object]) -> dict[str, object] | None:
    gps_position = _get_dict(vehicle_status, "gpsPosition")
    if not gps_position:
        return None
    gps_status = _get_int(gps_position, "gpsStatus")
    if gps_status not in (GpsStatus.FIX_2D.value, GpsStatus.FIX_3d.value):
        return None
    way_point = _get_dict(gps_position, "wayPoint")
    position = _get_dict(way_point, "position")
    raw_lat = _get_int(position, "latitude")
    raw_long = _get_int(position, "longitude")
    if raw_lat is None or raw_long is None:
        return None
    latitude = raw_lat / 1_000_000.0
    longitude = raw_long / 1_000_000.0
    if not (abs(latitude) <= 90 and abs(longitude) <= 180):
        return None
    raw_speed = _get_int(way_point, "speed")
    return {
        "latitude": round(latitude, 6),
        "longitude": round(longitude, 6),
        "altitude_m": _get_int(position, "altitude"),
        "heading_deg": _get_int(way_point, "heading"),
        "speed_kmh": round(raw_speed / 10.0, 1) if raw_speed is not None else None,
    }


def decode_advanced_info(raw: dict[str, object]) -> dict[str, object]:
    """Decode advanced/diagnostic fields from a parsed `raw_json` dict.

    `raw` is `json.loads(car_snapshot.raw_json)`, i.e.
    `{"vehicle_status": {...}, "charging_management_data": {...}}`.
    """
    vehicle_status = _get_dict(raw, "vehicle_status")
    basic = _get_dict(vehicle_status, "basicVehicleStatus")
    charging_management_data = _get_dict(raw, "charging_management_data")
    chrg = _get_dict(charging_management_data, "chrgMgmtData")
    rvs = _get_dict(charging_management_data, "rvsChargeStatus")

    engine_status = _get_int(basic, "engineStatus")
    hand_brake = _get_int(basic, "handBrake")
    engine_running = None if engine_status is None else engine_status == 1
    is_parked = _decode_is_parked(engine_status, hand_brake)

    remaining_time_raw = _get_int(chrg, "chrgngRmnngTime")
    remaining_time_valid_flag = _get_int(chrg, "chrgngRmnngTimeV")
    charging_remaining_time_minutes = (
        remaining_time_raw if remaining_time_valid_flag != 1 else None
    )

    raw_undecoded: dict[str, int | list[object] | None] = {
        field: _get_int(basic, field) for field in _RAW_UNDECODED_BASIC_FIELDS
    }
    raw_undecoded.update({field: _get_int(chrg, field) for field in _RAW_UNDECODED_CHRG_FIELDS})
    raw_undecoded.update(
        {out_name: _get_int(rvs, src_name) for out_name, src_name in _RAW_UNDECODED_RVS_FIELDS}
    )

    has_active_alerts, alert_data_raw = _decode_alerts(vehicle_status)
    raw_undecoded["alertDataSum"] = alert_data_raw

    return {
        "engine_running": engine_running,
        "is_parked": is_parked,
        "hand_brake_on": _decode_exactly_one(hand_brake),
        "main_beam_on": _int_to_bool(_get_int(basic, "mainBeamStatus")),
        "dipped_beam_on": _int_to_bool(_get_int(basic, "dippedBeamStatus")),
        "side_light_on": _int_to_bool(_get_int(basic, "sideLightStatus")),
        "exterior_temp_c": _decode_temperature(_get_int(basic, "exteriorTemperature")),
        "remote_climate_status": _decode_remote_climate(_get_int(basic, "remoteClimateStatus")),
        "rear_window_heat_on": _int_to_bool(_get_int(basic, "rmtHtdRrWndSt")),
        "front_left_seat_heat_level": _get_int(basic, "frontLeftSeatHeatLevel"),
        "front_right_seat_heat_level": _get_int(basic, "frontRightSeatHeatLevel"),
        "current_journey": _decode_current_journey(basic),
        "gps": _decode_gps(vehicle_status),
        "has_active_alerts": has_active_alerts,
        "vehicle_reported_at": _decode_vehicle_reported_at(_get_int(vehicle_status, "statusTime")),
        "charging_pile_id": _get_str(rvs, "chargingPileID"),
        "charging_pile_supplier": _get_str(rvs, "chargingPileSupplier"),
        "charging_type_raw": _get_int(rvs, "chargingType"),
        "charging_working_voltage_raw": _get_int(rvs, "workingVoltage"),
        "charging_working_current_raw": _get_int(rvs, "workingCurrent"),
        "charging_remaining_time_minutes": charging_remaining_time_minutes,
        # NOT _int_to_bool's `>0` convention -- ChrgMgmtData.charging_port_locked is
        # confirmed as an exact `== 1` check (verified against a real vehicle: a
        # captured value of 2 is a DIFFERENT state, not "locked" under `>0`'s looser
        # rule, which would have misreported it).
        "charging_port_locked": _decode_exactly_one(_get_int(chrg, "ccuEleccLckCtrlDspCmd")),
        "target_soc_pct": _decode_target_soc(_get_int(chrg, "bmsOnBdChrgTrgtSOCDspCmd")),
        "charge_current_limit": _decode_charge_current_limit(
            _get_int(chrg, "bmsAltngChrgCrntDspCmd")
        ),
        "bms_charging_status": _decode_bms_charging_status(_get_int(chrg, "bmsChrgSts")),
        "charging_stop_reason": _decode_charging_stop_reason(_get_int(chrg, "bmsChrgSpRsn")),
        "hv_battery": _decode_hv_battery(chrg),
        "battery_heating": _decode_battery_heating(
            _get_int(chrg, "bmsPTCHeatReqDspCmd"), _get_int(chrg, "bmsPTCHeatResp")
        ),
        "scheduled_charging": _decode_scheduled_charging(chrg),
        "obc_ac_input": _decode_obc_ac_input(chrg),
        "raw_undecoded": raw_undecoded,
    }
