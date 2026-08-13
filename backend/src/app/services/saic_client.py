"""Wrapper around saic_ismart_client_ng for fetching a single vehicle's status.

Field mapping notes: the raw SAIC field names and scaling factors used here were
verified two ways before writing this code (per CLAUDE.md rule "no fabricated
APIs/paths/behavior"):
  1. Directly reading the installed saic_ismart_client_ng==0.9.3 dataclasses
     (api/vehicle/schema.py, api/vehicle_charging/schema.py) for the real field
     names and the library's own decoded_current/decoded_voltage properties.
  2. Cross-checking scaling factors against SAIC-iSmart-API/saic-python-mqtt-gateway
     (same GitHub org, built on this exact client library) source, which contains
     confirmed decode logic for SOC, mileage, tyre pressure, battery voltage, and
     electric range.

One field is a judgment call, not independently confirmed -- see range_imcu_km below.
"""

from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import dataclass

from saic_ismart_client_ng import SaicApi
from saic_ismart_client_ng.api.vehicle import BasicVehicleStatus, VehicleStatusResp
from saic_ismart_client_ng.api.vehicle_charging import ChrgMgmtDataResp
from saic_ismart_client_ng.exceptions import SaicApiException, SaicLogoutException
from saic_ismart_client_ng.model import SaicApiConfiguration

from app.config import Settings

logger = logging.getLogger(__name__)

SnapshotFields = dict[str, float | bool | str | None]


class SaicClientError(Exception):
    """Raised when the live SAIC API call fails.

    `error` and `detail` are BOTH sent to the client in the 502 response body
    (see api_contract.md's {error, detail} shape) -- `error` must always be a
    short, static, safe-to-expose code, never raw exception text. The full
    underlying exception is logged server-side (via `logger`) instead, never
    folded into `error`.
    """

    def __init__(self, error: str, detail: str) -> None:
        super().__init__(error)
        self.error = error
        self.detail = detail


@dataclass(frozen=True)
class FetchedSnapshot:
    fields: SnapshotFields
    raw_json: str


def _in_range(value: int | None, low: float, high: float) -> bool:
    return value is not None and low <= value <= high


def _int_to_bool(value: int | None) -> bool | None:
    """`value > 0` means true (locked / open) -- None stays None.

    Confirmed against SAIC-iSmart-API/saic-python-mqtt-gateway's `int_to_bool` decode
    logic and Home Assistant `device_class` mappings for lock/door/window entities.
    """
    return None if value is None else value > 0


def _compute_doors(basic: BasicVehicleStatus | None) -> dict[str, bool | None] | None:
    """Build the `doors` object from `basicVehicleStatus` per api_contract.md.

    Whole object is None if `basicVehicleStatus` itself is missing; each sub-field
    is independently None if its raw value is None.
    """
    if basic is None:
        return None
    return {
        "locked": _int_to_bool(basic.lockStatus),
        "driver_door_open": _int_to_bool(basic.driverDoor),
        "passenger_door_open": _int_to_bool(basic.passengerDoor),
        "rear_left_door_open": _int_to_bool(basic.rearLeftDoor),
        "rear_right_door_open": _int_to_bool(basic.rearRightDoor),
        "bonnet_open": _int_to_bool(basic.bonnetStatus),
        "boot_open": _int_to_bool(basic.bootStatus),
        "driver_window_open": _int_to_bool(basic.driverWindow),
        "passenger_window_open": _int_to_bool(basic.passengerWindow),
        "rear_left_window_open": _int_to_bool(basic.rearLeftWindow),
        "rear_right_window_open": _int_to_bool(basic.rearRightWindow),
        "sunroof_open": _int_to_bool(basic.sunroofStatus),
    }


def _extract_soc_pct(
    charging: ChrgMgmtDataResp, vehicle: VehicleStatusResp
) -> float | None:
    # Mirrors saic-python-mqtt-gateway's extract_soc(): prefer the BMS pack SOC
    # (bmsPackSOCDsp, raw value is percent x10), fall back to
    # basicVehicleStatus.extendedData1 (already 0-100, no scaling) if the
    # charge-management SOC is unavailable.
    chrg = charging.chrgMgmtData
    if chrg is not None and chrg.bmsPackSOCDsp is not None:
        scaled = chrg.bmsPackSOCDsp / 10.0
        if 0 <= scaled <= 100:
            return scaled
    basic = vehicle.basicVehicleStatus
    if basic is not None and basic.extendedData1 is not None:
        raw = float(basic.extendedData1)
        if 0 <= raw <= 100:
            return raw
    return None


def map_to_snapshot_fields(
    vehicle: VehicleStatusResp, charging: ChrgMgmtDataResp
) -> SnapshotFields:
    """Map raw SAIC dataclasses onto the Snapshot shape in api_contract.md.

    Any field that can't be confidently derived from the raw response is left
    None per the task brief, rather than invented.
    """
    basic = vehicle.basicVehicleStatus
    chrg = charging.chrgMgmtData
    rvs = charging.rvsChargeStatus

    fields: SnapshotFields = {
        "soc_pct": _extract_soc_pct(charging, vehicle),
        "range_bms_km": None,
        "range_imcu_km": None,
        "is_charging": None,
        "charging_current": None,
        "plug_status": None,
        "battery_12v_voltage": None,
        "odometer_km": None,
        "cabin_temp_c": None,
        "tyre_pressure_fl": None,
        "tyre_pressure_fr": None,
        "tyre_pressure_rl": None,
        "tyre_pressure_rr": None,
        # Location view is deferred to v2 (docs/planning/decisions_log.md): these
        # are always null in v1 API responses, even though the raw SAIC response
        # may include GPS data (which is still preserved in raw_json below).
        "latitude": None,
        "longitude": None,
        "doors_json": None,
    }

    doors = _compute_doors(basic)
    if doors is not None:
        fields["doors_json"] = json.dumps(doors)

    if chrg is not None:
        # bmsEstdElecRng (BMS range) is published by saic-python-mqtt-gateway
        # without any /10 scaling (raw value validated directly as 0-2046 km).
        if _in_range(chrg.bmsEstdElecRng, 0, 2046):
            fields["range_bms_km"] = float(chrg.bmsEstdElecRng)  # type: ignore[arg-type]
        # imcuVehElecRng (IMCU range) is NOT used by saic-python-mqtt-gateway, so
        # its scaling isn't independently confirmed. Judgment call: treated the
        # same as its sibling field bmsEstdElecRng (same dataclass, same "*ElecRng"
        # naming convention) -- i.e. already in km, no extra scaling. Flagged in
        # the implementation report; verify once live vehicle testing is possible.
        if _in_range(chrg.imcuVehElecRng, 0, 2046):
            fields["range_imcu_km"] = float(chrg.imcuVehElecRng)  # type: ignore[arg-type]

        fields["is_charging"] = chrg.is_bms_charging

        is_valid_current = (
            chrg.bmsPackCrntV != 1
            and _in_range(chrg.bmsPackCrnt, 0, 65535)
            and chrg.decoded_current is not None
        )
        if is_valid_current and chrg.decoded_current is not None:
            fields["charging_current"] = round(chrg.decoded_current, 3)

    if rvs is not None and rvs.chargingGunState is not None:
        fields["plug_status"] = "plugged" if rvs.chargingGunState > 0 else "unplugged"

    if basic is not None:
        if _in_range(basic.batteryVoltage, 1, 65535) and basic.batteryVoltage is not None:
            fields["battery_12v_voltage"] = round(basic.batteryVoltage / 10.0, 2)
        if _in_range(basic.mileage, 1, 2_147_483_647) and basic.mileage is not None:
            fields["odometer_km"] = round(basic.mileage / 10.0, 1)
        interior_temp = basic.interiorTemperature
        if interior_temp is not None and -127 <= interior_temp <= 127 and interior_temp != 87:
            fields["cabin_temp_c"] = float(interior_temp)
        for field_name, raw in (
            ("tyre_pressure_fl", basic.frontLeftTyrePressure),
            ("tyre_pressure_fr", basic.frontRightTyrePressure),
            ("tyre_pressure_rl", basic.rearLeftTyrePressure),
            ("tyre_pressure_rr", basic.rearRightTyrePressure),
        ):
            if _in_range(raw, 1, 255) and raw is not None:
                fields[field_name] = round(raw * 0.04, 2)

    return fields


class SaicClient:
    """Thin wrapper: login, find the vehicle, fetch status + charging data."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def fetch_snapshot(self) -> FetchedSnapshot:
        if not self._settings.saic_username or not self._settings.saic_password:
            raise SaicClientError(
                error="SAIC_USERNAME/SAIC_PASSWORD not configured",
                detail="SAIC account credentials are not configured on the server.",
            )

        config = SaicApiConfiguration(
            username=self._settings.saic_username,
            password=self._settings.saic_password,
            region=self._settings.saic_region,
        )
        api = SaicApi(config)

        try:
            await api.login()
            vehicle_list = await api.vehicle_list()
            if not vehicle_list.vinList:
                raise SaicClientError(
                    error="No vehicles returned by vehicle_list()",
                    detail="No vehicle is registered on this iSmart account.",
                )
            vin = vehicle_list.vinList[0].vin
            if not vin:
                raise SaicClientError(
                    error="Vehicle entry missing VIN",
                    detail="The SAIC API returned a vehicle without a VIN.",
                )

            vehicle_status = await api.get_vehicle_status(vin)
            charging_status = await api.get_vehicle_charging_management_data(vin)

            fields = map_to_snapshot_fields(vehicle_status, charging_status)
            raw_json = json.dumps(
                {
                    "vehicle_status": dataclasses.asdict(vehicle_status),
                    "charging_management_data": dataclasses.asdict(charging_status),
                },
                default=str,
            )
        except SaicClientError:
            raise
        except SaicLogoutException as exc:
            logger.warning("SAIC authentication failure", exc_info=exc)
            raise SaicClientError(
                error="saic_authentication_failure",
                detail=(
                    "Authentication with the SAIC API failed. Check SAIC_USERNAME/"
                    "SAIC_PASSWORD in backend/.env."
                ),
            ) from exc
        except SaicApiException as exc:
            logger.warning("SAIC API call failed", exc_info=exc)
            raise SaicClientError(
                error="saic_api_error",
                detail="The SAIC API returned an error. Please try again later.",
            ) from exc
        except Exception as exc:  # network failures, unexpected schema, etc.
            logger.warning("Unexpected error calling SAIC API", exc_info=exc)
            raise SaicClientError(
                error="saic_unexpected_error",
                detail="Could not reach the SAIC API, or it returned unexpected data.",
            ) from exc

        return FetchedSnapshot(fields=fields, raw_json=raw_json)
