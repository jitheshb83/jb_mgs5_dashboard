import { formatNumber } from "../lib/format";
import { TyreIcon } from "./icons";

interface TyrePressureCardProps {
  fl: number | null;
  fr: number | null;
  rl: number | null;
  rr: number | null;
}

function TyreValue({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="rounded-lg bg-slate-50 py-2 text-center">
      <p className="text-sm font-semibold text-slate-800">
        {formatNumber(value, { decimals: 1, unit: " bar" })}
      </p>
      <p className="text-[11px] uppercase tracking-wide text-slate-400">{label}</p>
    </div>
  );
}

export function TyrePressureCard({ fl, fr, rl, rr }: TyrePressureCardProps) {
  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-900/5">
      <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">
        <span className="text-slate-400">
          <TyreIcon />
        </span>
        Tyre Pressure
      </p>
      <div className="mt-3 grid grid-cols-2 gap-3">
        <TyreValue label="Front L" value={fl} />
        <TyreValue label="Front R" value={fr} />
        <TyreValue label="Rear L" value={rl} />
        <TyreValue label="Rear R" value={rr} />
      </div>
    </div>
  );
}
