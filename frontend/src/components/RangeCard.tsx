import { formatNumber } from "../lib/format";
import { GaugeIcon } from "./icons";

interface RangeCardProps {
  rangeBmsKm: number | null;
  rangeImcuKm: number | null;
}

/**
 * Shows BMS- and IMCU-based range estimates together, since they can diverge (requirements.md
 * 4.4) -- often significantly. BMS is the vehicle's rated/theoretical range at the current SOC
 * (a standard-cycle-style figure, not adjusted for your actual driving); IMCU is adaptive,
 * learned from real driving/climate/conditions, and is the one that tends to match what MG's
 * own iSmart app and dash display show day to day. Confirmed against a real MGS5's data
 * 2026-08-16 -- see docs/planning/decisions_log.md.
 */
export function RangeCard({ rangeBmsKm, rangeImcuKm }: RangeCardProps) {
  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-900/5">
      <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">
        <span className="text-slate-400">
          <GaugeIcon />
        </span>
        Estimated Range
      </p>
      <div className="mt-2 flex items-baseline gap-6">
        <div>
          <p className="text-2xl font-semibold text-slate-900">
            {formatNumber(rangeBmsKm, { decimals: 0, unit: " km" })}
          </p>
          <p className="text-xs text-slate-400">BMS (rated)</p>
        </div>
        <div>
          <p className="text-2xl font-semibold text-slate-900">
            {formatNumber(rangeImcuKm, { decimals: 0, unit: " km" })}
          </p>
          <p className="text-xs text-slate-400">IMCU (real-world)</p>
        </div>
      </div>
      <p className="mt-2 text-xs text-slate-400">
        BMS is a rated estimate; IMCU adapts to your driving and usually matches the MG app.
      </p>
    </div>
  );
}
