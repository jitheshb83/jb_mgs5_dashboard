import type { ReactNode } from "react";
import { COLORS } from "../lib/colors";

interface ChartCardProps {
  title: string;
  /** Optional caveat/context line under the title -- e.g. SOH's "directional estimate, not
   * manufacturer-verified" disclosure (soh_methodology.md's "must never present as
   * authoritative" rule). */
  description?: string;
  className?: string;
  children: ReactNode;
}

/** Card chrome for a trend chart -- matches the app's existing card style (rounded-2xl/shadow/ring), with the chart plotting area on the dedicated chart-surface token. */
export function ChartCard({ title, description, className = "", children }: ChartCardProps) {
  return (
    <div className={`rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-900/5 ${className}`}>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{title}</p>
      {description ? <p className="mt-1 text-xs text-slate-400">{description}</p> : null}
      <div className="mt-3 rounded-lg" style={{ background: COLORS.surface }}>
        {children}
      </div>
    </div>
  );
}
