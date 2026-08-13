"""SYNTHETIC saic_ismart_client_ng response fixtures for tests.

IMPORTANT: These are hand-constructed, plausible-looking values -- NOT a real
captured response from the SAIC API. No live vehicle/account was available
during implementation (per docs/planning/decisions_log.md, the secondary
iSmart account required for live testing was not yet confirmed active), so
per the implementation brief these fixtures were built synthetically instead
of captured and anonymized. If real captured payloads become available later,
prefer replacing these with anonymized real ones per
docs/planning/testing_strategy.md.

Values use the real dataclasses from the installed saic_ismart_client_ng
package so a schema change in that library surfaces as a test failure here.
"""

from __future__ import annotations

from saic_ismart_client_ng.api.schema import GpsPosition
from saic_ismart_client_ng.api.vehicle import (
    BasicVehicleStatus,
    ExtendedVehicleStatus,
    VehicleStatusResp,
)
from saic_ismart_client_ng.api.vehicle_charging import (
    ChrgMgmtData,
    ChrgMgmtDataResp,
    RvsChargeStatus,
)


def synthetic_vehicle_status(
    *,
    mileage: int | None = 42105,
    battery_voltage: int | None = 126,
    interior_temp: int | None = 21,
    front_left_tyre_pressure: int | None = 60,
    front_right_tyre_pressure: int | None = 60,
    rear_left_tyre_pressure: int | None = 58,
    rear_right_tyre_pressure: int | None = 58,
    extended_data1: int | None = None,
    basic_status: str | None = "present",
    with_gps: bool = False,
    status_time: int = 1755000000,
    # doors/locks/windows -- 0 = closed/unlocked, >0 = open/locked (see api_contract.md).
    lock_status: int | None = 1,
    driver_door: int | None = 0,
    passenger_door: int | None = 0,
    rear_left_door: int | None = 0,
    rear_right_door: int | None = 0,
    bonnet_status: int | None = 0,
    boot_status: int | None = 0,
    driver_window: int | None = 0,
    passenger_window: int | None = 0,
    rear_left_window: int | None = 0,
    rear_right_window: int | None = 0,
    sunroof_status: int | None = 0,
    # advanced-info candidate fields (GET /api/latest/advanced).
    engine_status: int | None = 0,
    hand_brake: int | None = 1,
    main_beam_status: int | None = 0,
    dipped_beam_status: int | None = 0,
    side_light_status: int | None = 0,
    exterior_temp: int | None = 19,
    remote_climate_status: int | None = 0,
    rmt_htd_rr_wnd_st: int | None = 0,
    front_left_seat_heat_level: int | None = 0,
    front_right_seat_heat_level: int | None = 0,
    current_journey_id: int | None = None,
    current_journey_distance: int | None = None,
    extended_data2: int | None = None,
    power_mode: int | None = None,
    vehicle_alarm_status: int | None = None,
    wheel_tyre_monitor_status: int | None = None,
    can_bus_active: int | None = None,
    last_key_seen: int | None = None,
    steering_heat_level: int | None = None,
    steering_wheel_heat_failure_reason: int | None = None,
    time_of_last_canbus_activity: int | None = None,
    veh_elec_rng_dsp: int | None = None,
    clstr_dspd_fuel_lvl_sgmt: int | None = None,
    # fossil-fuel fields, meaningless for this BEV but surfaced raw (GET /api/latest/advanced).
    fuel_level_prc: int | None = None,
    fuel_range: int | None = None,
    fuel_range_elec: int | None = None,
    # vehicle alert codes -- see advanced_info.py's _decode_alerts.
    alert_data_sum: list[int] | None = None,
) -> VehicleStatusResp:
    basic: BasicVehicleStatus | None = None
    if basic_status is not None:
        basic = BasicVehicleStatus(
            mileage=mileage,
            batteryVoltage=battery_voltage,
            interiorTemperature=interior_temp,
            frontLeftTyrePressure=front_left_tyre_pressure,
            frontRightTyrePressure=front_right_tyre_pressure,
            rearLeftTyrePressure=rear_left_tyre_pressure,
            rearRightTyrePressure=rear_right_tyre_pressure,
            extendedData1=extended_data1,
            lockStatus=lock_status,
            driverDoor=driver_door,
            passengerDoor=passenger_door,
            rearLeftDoor=rear_left_door,
            rearRightDoor=rear_right_door,
            bonnetStatus=bonnet_status,
            bootStatus=boot_status,
            driverWindow=driver_window,
            passengerWindow=passenger_window,
            rearLeftWindow=rear_left_window,
            rearRightWindow=rear_right_window,
            sunroofStatus=sunroof_status,
            engineStatus=engine_status,
            handBrake=hand_brake,
            mainBeamStatus=main_beam_status,
            dippedBeamStatus=dipped_beam_status,
            sideLightStatus=side_light_status,
            exteriorTemperature=exterior_temp,
            remoteClimateStatus=remote_climate_status,
            rmtHtdRrWndSt=rmt_htd_rr_wnd_st,
            frontLeftSeatHeatLevel=front_left_seat_heat_level,
            frontRightSeatHeatLevel=front_right_seat_heat_level,
            currentJourneyId=current_journey_id,
            currentJourneyDistance=current_journey_distance,
            extendedData2=extended_data2,
            powerMode=power_mode,
            vehicleAlarmStatus=vehicle_alarm_status,
            wheelTyreMonitorStatus=wheel_tyre_monitor_status,
            canBusActive=can_bus_active,
            lastKeySeen=last_key_seen,
            steeringHeatLevel=steering_heat_level,
            steeringWheelHeatFailureReason=steering_wheel_heat_failure_reason,
            timeOfLastCANBUSActivity=time_of_last_canbus_activity,
            vehElecRngDsp=veh_elec_rng_dsp,
            clstrDspdFuelLvlSgmt=clstr_dspd_fuel_lvl_sgmt,
            fuelLevelPrc=fuel_level_prc,
            fuelRange=fuel_range,
            fuelRangeElec=fuel_range_elec,
        )
    gps: GpsPosition | None = None
    if with_gps:
        gps = GpsPosition(
            gpsStatus=3,
            timeStamp=status_time,
            wayPoint=GpsPosition.WayPoint(
                heading=90,
                speed=0,
                satellites=8,
                hdop=1,
                position=GpsPosition.WayPoint.Position(
                    latitude=59_910_000, longitude=10_750_000, altitude=10
                ),
            ),
        )
    extended = ExtendedVehicleStatus(alertDataSum=alert_data_sum or [])
    return VehicleStatusResp(
        basicVehicleStatus=basic,
        extendedVehicleStatus=extended,
        gpsPosition=gps,
        statusTime=status_time,
    )


def synthetic_charging_management_data(
    *,
    bms_pack_soc_dsp: int | None = 780,
    bms_estd_elec_rng: int | None = 310,
    imcu_veh_elec_rng: int | None = 295,
    bms_chrg_sts: int | None = 1,
    bms_pack_crnt: int | None = 19_980,
    bms_pack_crnt_v: int | None = 0,
    bms_pack_vol: int | None = 2_400,
    charging_gun_state: int | None = 1,
    chrg_mgmt_data: str | None = "present",
    rvs_charge_status: str | None = "present",
    # target SOC / charge current limit / remaining time (GET /api/latest/advanced).
    bms_on_bd_chrg_trgt_soc_dsp_cmd: int | None = 5,  # TargetBatteryCode.P_80
    bms_altng_chrg_crnt_dsp_cmd: int | None = 3,  # ChargeCurrentLimitCode.C_16A
    chrgng_rmnng_time: int | None = 45,
    chrgng_rmnng_time_v: int | None = 0,
    # rvsChargeStatus statistics (GET /api/latest/battery-usage and /advanced).
    total_battery_capacity: int | None = 618,
    power_usage_of_day: int | None = 420,
    power_usage_since_last_charge: int | None = 1_260,
    last_charge_ending_power: int | None = 3_840,
    realtime_power: int | None = None,
    mileage_of_day: int | None = 213,
    mileage_since_last_charge: int | None = 1_437,
    charging_pile_id: str | None = "PILE-0001",
    charging_pile_supplier: str | None = "ACME Charging",
    charging_type: int | None = 1,
    working_current: int | None = 16,
    working_voltage: int | None = 230,
    # charging port lock / battery heating / charging stop reason (GET /api/latest/advanced).
    # ccuEleccLckCtrlDspCmd default of 2 (NOT 1) deliberately mirrors a real captured
    # vehicle response -- confirms the `== 1` convention (not `> 0`) is actually
    # exercised, per advanced_info.py's _decode_exactly_one.
    ccu_elecc_lck_ctrl_dsp_cmd: int | None = 2,
    bms_ptc_heat_req_dsp_cmd: int | None = None,
    bms_ptc_heat_resp: int | None = None,
    bms_chrg_sp_rsn: int | None = None,
    # scheduled charging reservation (GET /api/latest/advanced's scheduled_charging).
    bms_reser_ctrl_dsp_cmd: int | None = None,
    bms_reser_st_hour_dsp_cmd: int | None = None,
    bms_reser_st_mintue_dsp_cmd: int | None = None,
    bms_reser_sp_hour_dsp_cmd: int | None = None,
    bms_reser_sp_mintue_dsp_cmd: int | None = None,
    # on-board AC charger input (GET /api/latest/advanced's obc_ac_input).
    on_bd_chrgr_altr_crnt_inpt_crnt: int | None = None,
    on_bd_chrgr_altr_crnt_inpt_vol: int | None = None,
) -> ChrgMgmtDataResp:
    chrg: ChrgMgmtData | None = None
    if chrg_mgmt_data is not None:
        chrg = ChrgMgmtData(
            bmsPackSOCDsp=bms_pack_soc_dsp,
            bmsEstdElecRng=bms_estd_elec_rng,
            imcuVehElecRng=imcu_veh_elec_rng,
            bmsChrgSts=bms_chrg_sts,
            bmsPackCrnt=bms_pack_crnt,
            bmsPackCrntV=bms_pack_crnt_v,
            bmsPackVol=bms_pack_vol,
            bmsOnBdChrgTrgtSOCDspCmd=bms_on_bd_chrg_trgt_soc_dsp_cmd,
            bmsAltngChrgCrntDspCmd=bms_altng_chrg_crnt_dsp_cmd,
            chrgngRmnngTime=chrgng_rmnng_time,
            chrgngRmnngTimeV=chrgng_rmnng_time_v,
            ccuEleccLckCtrlDspCmd=ccu_elecc_lck_ctrl_dsp_cmd,
            bmsPTCHeatReqDspCmd=bms_ptc_heat_req_dsp_cmd,
            bmsPTCHeatResp=bms_ptc_heat_resp,
            bmsChrgSpRsn=bms_chrg_sp_rsn,
            bmsReserCtrlDspCmd=bms_reser_ctrl_dsp_cmd,
            bmsReserStHourDspCmd=bms_reser_st_hour_dsp_cmd,
            bmsReserStMintueDspCmd=bms_reser_st_mintue_dsp_cmd,
            bmsReserSpHourDspCmd=bms_reser_sp_hour_dsp_cmd,
            bmsReserSpMintueDspCmd=bms_reser_sp_mintue_dsp_cmd,
            onBdChrgrAltrCrntInptCrnt=on_bd_chrgr_altr_crnt_inpt_crnt,
            onBdChrgrAltrCrntInptVol=on_bd_chrgr_altr_crnt_inpt_vol,
        )
    rvs: RvsChargeStatus | None = None
    if rvs_charge_status is not None:
        rvs = RvsChargeStatus(
            chargingGunState=charging_gun_state,
            fuelRangeElec=3_100,
            totalBatteryCapacity=total_battery_capacity,
            powerUsageOfDay=power_usage_of_day,
            powerUsageSinceLastCharge=power_usage_since_last_charge,
            lastChargeEndingPower=last_charge_ending_power,
            realtimePower=realtime_power,
            mileageOfDay=mileage_of_day,
            mileageSinceLastCharge=mileage_since_last_charge,
            chargingPileID=charging_pile_id,
            chargingPileSupplier=charging_pile_supplier,
            chargingType=charging_type,
            workingCurrent=working_current,
            workingVoltage=working_voltage,
        )
    return ChrgMgmtDataResp(chrgMgmtData=chrg, rvsChargeStatus=rvs)
