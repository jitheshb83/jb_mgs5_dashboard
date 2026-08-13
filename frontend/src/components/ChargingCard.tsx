import { formatBoolean, formatNumber, formatString } from "../lib/format";
import { PlugIcon } from "./icons";

interface ChargingCardProps {
  isCharging: boolean | null;
  plugStatus: string | null;
  chargingCurrent: number | null;
}

export function ChargingCard({ isCharging, plugStatus, chargingCurrent }: ChargingCardProps) {
  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-900/5">
      <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">
        <span className="text-slate-400">
          <PlugIcon />
        </span>
        Charging
      </p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">
        {formatBoolean(isCharging, { yes: "Charging", no: "Not charging" })}
      </p>
      <div className="mt-3 space-y-1 text-sm text-slate-500">
        <p>
          Plug: <span className="font-medium text-slate-700">{formatString(plugStatus)}</span>
        </p>
        <p>
          Current:{" "}
          <span className="font-medium text-slate-700">
            {formatNumber(chargingCurrent, { decimals: 1, unit: " A" })}
          </span>
        </p>
      </div>
    </div>
  );
}
