import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string;
  sublabel?: string;
  className?: string;
  /** Small inline SVG icon shown beside the label, for faster visual scanning. */
  icon?: ReactNode;
}

/** Generic single-value stat card. Used directly for simple fields (12V voltage,
 * cabin temp, odometer); composite fields (range, charging, tyres, SOC) get
 * their own small components below since they combine multiple snapshot fields. */
export function StatCard({ label, value, sublabel, className = "", icon }: StatCardProps) {
  return (
    <div className={`rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-900/5 ${className}`}>
      <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-slate-500">
        {icon ? <span className="text-slate-400">{icon}</span> : null}
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold text-slate-900">{value}</p>
      {sublabel ? <p className="mt-1 text-sm text-slate-400">{sublabel}</p> : null}
    </div>
  );
}
