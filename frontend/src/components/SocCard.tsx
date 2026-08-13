import { formatNumber } from "../lib/format";
import { COLORS } from "../lib/colors";
import { BatteryIcon } from "./icons";

interface SocCardProps {
  socPct: number | null;
}

/**
 * Hero card for State of Charge (the dashboard's one hero figure — ≥48px,
 * exactly one per view). The meter's fill is the accent blue with an
 * unfilled track a lighter step of the same ramp, so state reads across the
 * whole bar rather than a generic gray track.
 */
export function SocCard({ socPct }: SocCardProps) {
  const pct = socPct === null || socPct === undefined ? 0 : Math.min(Math.max(socPct, 0), 100);
  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-900/5 sm:col-span-2">
      <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">
        <span className="text-slate-400">
          <BatteryIcon />
        </span>
        State of Charge
      </p>
      <p className="mt-2 text-4xl font-semibold text-slate-900">
        {formatNumber(socPct, { decimals: 0, unit: "%" })}
      </p>
      <div className="mt-4 h-2.5 w-full overflow-hidden rounded-full" style={{ background: COLORS.blueLight }}>
        <div
          className="h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: COLORS.blue }}
        />
      </div>
    </div>
  );
}
