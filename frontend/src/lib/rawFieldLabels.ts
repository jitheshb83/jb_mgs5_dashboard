/**
 * Human-readable labels for `raw_undecoded`'s field names (GET /api/latest/advanced).
 *
 * IMPORTANT: this maps SAIC field *names* to plain-English descriptions of what
 * the field apparently represents -- it does NOT claim to know what any
 * field's *value* means. The backend already only puts a field here when
 * neither the installed `saic_ismart_client_ng` library, the reference
 * project (`SAIC-iSmart-API/saic-python-mqtt-gateway`), nor the published
 * ASN.1 wire-protocol schema (`SAIC-iSmart-API/documentation`) confirm a
 * value decode for it (see backend/src/app/services/advanced_info.py's
 * module docstring) -- these labels don't change that; the raw integer is
 * still shown as-is, unconverted.
 *
 * Sourcing for each label: automotive/EV abbreviations are expanded using
 * well-established industry terms (BMS = Battery Management System, CCU =
 * Charging Control Unit, OBC = On-Board Charger, PTC = Positive Temperature
 * Coefficient heater, FOTA = Firmware Over The Air, V2X = Vehicle-to-Everything),
 * cross-checked against how the SAME abbreviations are used in already-CONFIRMED
 * sibling fields in this codebase (e.g. "bms" prefixes fields already decoded
 * via `ChrgMgmtData`'s own properties; "ccu"/"obc" prefixes fields with confirmed
 * decode logic in `chrg_mgmt_data.py`). "IMCU" has no confirmed expansion found
 * anywhere (checked the library, the reference project, and the ASN.1 schema) --
 * left as the acronym, same as this project's own docs/planning/requirements.md
 * already does ("IMCU-based" range). "EPT" in `clstrElecRngToEPT` is inferred as
 * "Empty" (range-to-empty is a standard automotive concept) but is not
 * independently confirmed, so its label says "(assumed Empty)".
 *
 * A field with no entry here falls back to a generic camelCase->"Title Case"
 * split in `labelForRawField` below, so a newly-added raw field never renders
 * as a raw, un-spaced identifier even before someone adds a proper label.
 */
export const RAW_FIELD_LABELS: Record<string, string> = {
  // basicVehicleStatus -- misc status/diagnostic codes.
  lastKeySeen: "Last Key Seen",
  steeringHeatLevel: "Steering Wheel Heat Level",
  steeringWheelHeatFailureReason: "Steering Wheel Heat Failure Reason",
  timeOfLastCANBUSActivity: "Time of Last CAN Bus Activity",
  vehElecRngDsp: "Vehicle Electric Range (Instrument Display)",
  clstrDspdFuelLvlSgmt: "Instrument Cluster Fuel Gauge Segment",
  extendedData1: "Extended Data 1 (reserved/undocumented)",
  extendedData2: "Extended Data 2 (reserved/undocumented)",
  powerMode: "Power Mode",
  vehicleAlarmStatus: "Vehicle Alarm Status",
  wheelTyreMonitorStatus: "Tyre Pressure Monitor System Status",
  canBusActive: "CAN Bus Active",
  // Fossil-fuel fields -- part of the shared library/protocol for PHEV/ICE
  // models, always meaningless sentinels for this BEV.
  fuelLevelPrc: "Fuel Level % (not applicable -- BEV)",
  fuelRange: "Fossil Fuel Range (not applicable -- BEV)",
  fuelRangeElec: "Electric Range (Instrument Cluster copy)",

  // ChrgMgmtData -- charging management/BMS command & status codes.
  bmsAdpPubChrgSttnDspCmd: "BMS Adaptive Public Charging Station Command",
  bmsChrgCtrlDspCmd: "BMS Charge Control Command",
  bmsChrgOtptCrntReq: "BMS Charge Output Current Request",
  bmsChrgOtptCrntReqV: "BMS Charge Output Current Request (valid flag)",
  bmsPTCHeatSpRsn: "Battery Heater (PTC) Stop Reason (raw code)",
  ccuOffBdChrgrPlugOn: "Off-Board (DC) Charger Plug Connected",
  ccuOnbdChrgrPlugOn: "On-Board (AC) Charger Plug Connected",
  chrgngAddedElecRng: "Range Added This Charge Session",
  chrgngAddedElecRngV: "Range Added This Charge Session (valid flag)",
  chrgngDoorOpenCnd: "Charging Port Door Open Condition",
  chrgngDoorPosSts: "Charging Port Door Position Status",
  chrgngSpdngTime: "Charging Elapsed Time",
  chrgngSpdngTimeV: "Charging Elapsed Time (valid flag)",
  clstrElecRngToEPT: "Instrument Cluster Range to Empty (assumed \"Empty\")",
  disChrgngRmnngTime: "Discharging (Vehicle-to-Load) Remaining Time",
  disChrgngRmnngTimeV: "Discharging (Vehicle-to-Load) Remaining Time (valid flag)",
  imcuChrgngEstdElecRng: "IMCU Estimated Range While Charging",
  imcuChrgngEstdElecRngV: "IMCU Estimated Range While Charging (valid flag)",
  imcuDschrgngEstdElecRng: "IMCU Estimated Range While Discharging",
  imcuDschrgngEstdElecRngV: "IMCU Estimated Range While Discharging (valid flag)",
  imcuVehElecRngV: "IMCU Vehicle Range (valid flag)",

  // RvsChargeStatus -- charging-session report (prefixed rvs* where the bare
  // SAIC name would collide with an unrelated basicVehicleStatus field).
  rvsChargingDuration: "Charging Session Duration (raw)",
  rvsChargingElectricityPhase: "Charging AC Phase Count",
  rvsEndTime: "Charging Session End Time (raw)",
  rvsExtendedData1: "Charging Session Extended Data 1 (reserved/undocumented)",
  rvsExtendedData2: "Charging Session Extended Data 2 (reserved/undocumented)",
  rvsExtendedData3: "Charging Session Extended Data 3 (reserved/undocumented)",
  rvsExtendedData4: "Charging Session Extended Data 4 (reserved/undocumented)",
  rvsFotaLowestVoltage: "Firmware Update (FOTA) Lowest Cell Voltage",
  rvsFuelRangeElec: "Electric Range (Charging Status copy)",
  rvsStartTime: "Charging Session Start Time (raw)",
  rvsStaticEnergyConsumption: "Standby (Vampire) Energy Consumption",

  // extendedVehicleStatus.
  alertDataSum: "Vehicle Alert Codes (raw)",
};

/**
 * SAIC field name -> display label. Falls back to a generic camelCase split
 * (e.g. `someNewField` -> "Some New Field") for anything not yet in
 * RAW_FIELD_LABELS, so a newly-surfaced raw field is still legible.
 */
export function labelForRawField(saicFieldName: string): string {
  const known = RAW_FIELD_LABELS[saicFieldName];
  if (known) return known;
  return saicFieldName
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/^./, (c) => c.toUpperCase())
    .trim();
}
