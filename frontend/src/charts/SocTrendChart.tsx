import { useMemo } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { HistorySnapshot } from "../lib/types";
import { COLORS } from "../lib/colors";
import { formatDateTime } from "../lib/format";
import { ChartEmptyState } from "./ChartEmptyState";
import { formatAxisTime, lastValidIndex, makeEndDot, makeEndLabel } from "./chartHelpers";

interface SocTrendChartProps {
  /** History entries in chronological (oldest-first) order. */
  snapshots: HistorySnapshot[];
  isLoading?: boolean;
}

interface SocPoint {
  fetchedAt: string;
  soc: number | null;
}

/**
 * SOC over time -- single series, no legend (the chart title already names
 * it). Sequential blue per the dataviz pass.
 */
export function SocTrendChart({ snapshots, isLoading = false }: SocTrendChartProps) {
  // Hooks must run unconditionally, so the derived arrays are memoized here,
  // above the empty-state early return below -- avoids re-mapping/re-scanning
  // up to 500 snapshots on every unrelated Dashboard re-render.
  const data = useMemo<SocPoint[]>(
    () => snapshots.map((s) => ({ fetchedAt: s.fetched_at, soc: s.snapshot.soc_pct })),
    [snapshots],
  );
  const endIndex = useMemo(() => lastValidIndex(data.map((d) => d.soc)), [data]);

  if (snapshots.length === 0) {
    return <ChartEmptyState label="State of charge" isLoading={isLoading} />;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 12, right: 48, bottom: 8, left: 4 }}>
        <CartesianGrid stroke={COLORS.gridline} vertical={false} />
        <XAxis
          dataKey="fetchedAt"
          tickFormatter={formatAxisTime}
          tickLine={false}
          stroke={COLORS.axis}
          tick={{ fill: COLORS.inkMuted, fontSize: 11 }}
          minTickGap={32}
        />
        <YAxis
          domain={[0, 100]}
          ticks={[0, 25, 50, 75, 100]}
          tickFormatter={(v: number) => `${v}%`}
          tickLine={false}
          stroke={COLORS.axis}
          tick={{ fill: COLORS.inkMuted, fontSize: 11 }}
          width={38}
        />
        <Tooltip
          cursor={{ stroke: COLORS.axis, strokeWidth: 1 }}
          formatter={(value: number) => [`${value}%`, "SOC"]}
          labelFormatter={(label: string) => formatDateTime(label)}
          contentStyle={{
            background: COLORS.surface,
            border: `1px solid ${COLORS.axis}`,
            borderRadius: 8,
            fontSize: 12,
          }}
          labelStyle={{ color: COLORS.inkSecondary }}
        />
        <Line
          type="monotone"
          dataKey="soc"
          stroke={COLORS.blue}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          dot={makeEndDot(COLORS.blue, endIndex)}
          activeDot={{ r: 5, fill: COLORS.blue, stroke: COLORS.surface, strokeWidth: 2 }}
          label={makeEndLabel(endIndex, (v) => `${v}%`)}
          connectNulls
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
