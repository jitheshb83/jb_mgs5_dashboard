# Battery SOH Estimation Methodology

## Why this is needed

The SAIC cloud API (used by this dashboard) does not expose a State of Health (SOH) field.
Two range estimates are available instead — BMS-based and IMCU-based — but neither is SOH directly.
A true SOH reading exists via OBD-II dongle + third-party app (e.g. Car Scanner with an
MGS5-specific profile), but that requires physical hardware plugged into the vehicle and is
out of scope for this cloud-API-based web dashboard.

**This estimate is directional, not precise.** The UI must label it clearly as an estimate
(e.g. "Estimated SOH — based on observed charge cycles", with a tooltip explaining the method)
and must never present it as an authoritative/manufacturer-verified figure.

## Method (v1, simple)

1. **Detect a full-charge cycle** from `car_snapshot` history:
   - `plug_status` transitions to "plugged in" / `is_charging` becomes true
   - `soc_pct` starts below a low threshold (default: 30%)
   - `soc_pct` reaches ~100% (default: ≥97%, to allow for API rounding/lag)
   - The cycle is considered complete when charging stops or SOC plateaus at/near 100%

2. **Estimate kWh delivered** during that cycle.

   **2026-08-15 correction:** this section originally proposed two approaches -- a preferred
   current×voltage×time integration, and a fallback using the SOC delta "against the nameplate
   usable capacity as a rough cross-check." That fallback, as literally specified, is
   mathematically circular: substituting `kwh_delivered = soc_delta/100 * nameplate_kwh` into
   step 3's formula makes the `soc_delta` term cancel out entirely, so `usable_kwh_estimate`
   always equals `nameplate_kwh` exactly and `soh_pct` always computes to ~100%, regardless of
   real battery condition. Caught before implementation (during the `/api/latest/battery-usage`
   investigation the same day, which established that `current_energy_kwh` -- decoded from the
   vehicle's own `realtimePower` field -- is reliably reported for this vehicle, unlike the other
   `rvsChargeStatus` stats).

   **Shipped v1 method:** use the delta in `current_energy_kwh` between the cycle's start and end
   snapshots as `kwh_delivered`. This is a genuine, independently vehicle-reported energy
   quantity (not derived from our own nameplate constant), so it can actually detect degradation
   over time. `basis = "current_energy_kwh_delta"` on the stored row records this. If
   `current_energy_kwh` isn't available at the start or end snapshot, the cycle is skipped
   entirely rather than falling back to a method that would reintroduce the circularity above.
   The originally-proposed current×voltage×time integration remains a possible future
   improvement, not attempted in v1.

3. **Compute estimated usable capacity:**
   `usable_kwh_estimate = kwh_delivered / (soc_end - soc_start) * 100`

4. **Compute SOH:**
   `soh_pct = usable_kwh_estimate / nameplate_usable_kwh * 100`
   where `nameplate_usable_kwh = 62.1` (MGS5 Luxury, 64 kWh gross / 62.1 kWh usable — see
   `docs/planning/decisions_log.md`).

5. **Store** as a row in `soh_estimate` (see `docs/architecture/data_model.md`), one row per
   detected full-charge cycle. Do not overwrite history — SOH trend over months/years is the
   whole point. Implemented as a side effect of `POST /api/refresh` (live fetches only) via
   `backend/src/app/services/soh.py` + `app/api/refresh.py`'s `_record_soh_estimates_if_any`,
   deduplicated against already-recorded cycles by `cycle_end_snapshot_id`.

## Known limitations (document these in code comments, not just here)

- A single data point is noise, not signal. Don't display SOH until at least 2-3 full-charge
  cycles have been observed; show "not enough data yet" before that (see API contract, `/api/soh`).
- Partial charges (e.g. 40% → 80%) are not usable for this calculation and must be excluded from
  cycle detection — only genuine low-to-full cycles count.
- Manual/scheduled refresh means charge-cycle data has gaps (a charge could start and finish
  between two refreshes hours apart) — the detection logic must tolerate missing intermediate
  snapshots and should not assume continuous data.
- Ambient temperature affects real-world charge efficiency; this method does not correct for it
  in v1. Worth a note in the UI tooltip, not a blocker for v1.
