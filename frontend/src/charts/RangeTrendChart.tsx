import { useMemo } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { HistorySnapshot } from "../lib/types";
import { COLORS } from "../lib/colors";
import { formatDateTime } from "../lib/format";
import { ChartEmptyState } from "./ChartEmptyState";
import { formatAxisTime, lastValidIndex, makeEndDot, makeEndLabel } from "./chartHelpers";

interface RangeTrendChartProps {
  /** History entries in chronological (oldest-first) order. */
  snapshots: HistorySnapshot[];
  isLoading?: boolean;
}

interface RangePoint {
  fetchedAt: string;
  bms: number | null;
  imcu: number | null;
}

const formatKm = (v: number) => `${Math.round(v)} km`;

/**
 * Estimated range over time -- two series (BMS vs IMCU), same unit/scale so
 * one shared y-axis is correct (never dual-axis). Categorical slot 1 (blue)
 * for BMS, slot 2 (orange) for IMCU -- fixed order, always present with a
 * legend since there are 2+ series, plus direct end labels for clarity.
 */
export function RangeTrendChart({ snapshots, isLoading = false }: RangeTrendChartProps) {
  // Hooks must run unconditionally -- memoized above the empty-state early
  // return below, same reasoning as SocTrendChart.
  const data = useMemo<RangePoint[]>(
    () =>
      snapshots.map((s) => ({
        fetchedAt: s.fetched_at,
        bms: s.snapshot.range_bms_km,
        imcu: s.snapshot.range_imcu_km,
      })),
    [snapshots],
  );
  const bmsEndIndex = useMemo(() => lastValidIndex(data.map((d) => d.bms)), [data]);
  const imcuEndIndex = useMemo(() => lastValidIndex(data.map((d) => d.imcu)), [data]);

  if (snapshots.length === 0) {
    return <ChartEmptyState label="Range" isLoading={isLoading} />;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data} margin={{ top: 12, right: 72, bottom: 8, left: 4 }}>
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
          tickFormatter={(v: number) => `${v}`}
          tickLine={false}
          stroke={COLORS.axis}
          tick={{ fill: COLORS.inkMuted, fontSize: 11 }}
          width={42}
          label={{
            value: "km",
            angle: -90,
            position: "insideLeft",
            fill: COLORS.inkMuted,
            fontSize: 11,
          }}
        />
        <Tooltip
          cursor={{ stroke: COLORS.axis, strokeWidth: 1 }}
          formatter={(value: number, name: string) => [formatKm(value), name]}
          labelFormatter={(label: string) => formatDateTime(label)}
          contentStyle={{
            background: COLORS.surface,
            border: `1px solid ${COLORS.axis}`,
            borderRadius: 8,
            fontSize: 12,
          }}
          labelStyle={{ color: COLORS.inkSecondary }}
        />
        <Legend
          verticalAlign="top"
          height={28}
          formatter={(value: string) => <span style={{ color: COLORS.inkSecondary, fontSize: 12 }}>{value}</span>}
        />
        <Line
          type="monotone"
          dataKey="bms"
          name="BMS"
          stroke={COLORS.blue}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          dot={makeEndDot(COLORS.blue, bmsEndIndex)}
          activeDot={{ r: 5, fill: COLORS.blue, stroke: COLORS.surface, strokeWidth: 2 }}
          label={makeEndLabel(bmsEndIndex, formatKm, -6)}
          connectNulls
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="imcu"
          name="IMCU"
          stroke={COLORS.orange}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          dot={makeEndDot(COLORS.orange, imcuEndIndex)}
          activeDot={{ r: 5, fill: COLORS.orange, stroke: COLORS.surface, strokeWidth: 2 }}
          label={makeEndLabel(imcuEndIndex, formatKm, 14)}
          connectNulls
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
