import type { ReactNode } from "react";
import { COLORS } from "../lib/colors";

interface ChartCardProps {
  title: string;
  className?: string;
  children: ReactNode;
}

/** Card chrome for a trend chart -- matches the app's existing card style (rounded-2xl/shadow/ring), with the chart plotting area on the dedicated chart-surface token. */
export function ChartCard({ title, className = "", children }: ChartCardProps) {
  return (
    <div className={`rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-900/5 ${className}`}>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{title}</p>
      <div className="mt-3 rounded-lg" style={{ background: COLORS.surface }}>
        {children}
      </div>
    </div>
  );
}
