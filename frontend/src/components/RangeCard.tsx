import { formatNumber } from "../lib/format";
import { GaugeIcon } from "./icons";

interface RangeCardProps {
  rangeBmsKm: number | null;
  rangeImcuKm: number | null;
}

/** Shows BMS- and IMCU-based range estimates together, since they can diverge (requirements.md 4.4). */
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
          <p className="text-xs text-slate-400">BMS</p>
        </div>
        <div>
          <p className="text-2xl font-semibold text-slate-900">
            {formatNumber(rangeImcuKm, { decimals: 0, unit: " km" })}
          </p>
          <p className="text-xs text-slate-400">IMCU</p>
        </div>
      </div>
    </div>
  );
}
