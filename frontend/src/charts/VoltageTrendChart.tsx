import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { HistorySnapshot } from "../lib/types";
import { COLORS } from "../lib/colors";
import { formatDateTime } from "../lib/format";
import { ChartEmptyState } from "./ChartEmptyState";
import { formatAxisTime, lastValidIndex, makeEndDot, makeEndLabel } from "./chartHelpers";

interface VoltageTrendChartProps {
  /** History entries in chronological (oldest-first) order. */
  snapshots: HistorySnapshot[];
  isLoading?: boolean;
}

interface VoltagePoint {
  fetchedAt: string;
  voltage: number | null;
}

/** Below this, the 12V battery is at risk of drain -- see data_model.md's column comment on battery_12v_voltage. */
const LOW_VOLTAGE_THRESHOLD = 12.0;

/**
 * 12V battery voltage over time -- single series, no legend. Includes a
 * shaded + labeled warning zone below the healthy-voltage threshold (status
 * "warning" color, always paired with a visible text label -- never color
 * alone).
 */
export function VoltageTrendChart({ snapshots, isLoading = false }: VoltageTrendChartProps) {
  // Hooks must run unconditionally -- memoized above the empty-state early
  // return below, same reasoning as SocTrendChart.
  const data = useMemo<VoltagePoint[]>(
    () =>
      snapshots.map((s) => ({
        fetchedAt: s.fetched_at,
        voltage: s.snapshot.battery_12v_voltage,
      })),
    [snapshots],
  );
  const { domainMin, domainMax } = useMemo(() => {
    const values = data.map((d) => d.voltage).filter((v): v is number => v !== null);
    const dataMin = values.length ? Math.min(...values) : 12.6;
    const dataMax = values.length ? Math.max(...values) : 12.6;
    // Always keep a sliver of the low-voltage zone in view, so the threshold
    // reads as a constant reference rather than only appearing near a fault.
    return { domainMin: Math.min(dataMin - 0.2, 11.8), domainMax: Math.max(dataMax + 0.2, 12.2) };
  }, [data]);
  const endIndex = useMemo(() => lastValidIndex(data.map((d) => d.voltage)), [data]);

  if (snapshots.length === 0) {
    return <ChartEmptyState label="12V battery voltage" isLoading={isLoading} />;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 12, right: 64, bottom: 8, left: 4 }}>
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
          domain={[domainMin, domainMax]}
          tickFormatter={(v: number) => `${v.toFixed(1)}V`}
          tickLine={false}
          stroke={COLORS.axis}
          tick={{ fill: COLORS.inkMuted, fontSize: 11 }}
          width={46}
        />
        <ReferenceArea
          y1={domainMin}
          y2={LOW_VOLTAGE_THRESHOLD}
          fill={COLORS.warning}
          fillOpacity={0.12}
          strokeOpacity={0}
          ifOverflow="hidden"
        />
        <ReferenceLine
          y={LOW_VOLTAGE_THRESHOLD}
          stroke={COLORS.warning}
          strokeWidth={1.5}
          label={{
            value: `Low voltage (< ${LOW_VOLTAGE_THRESHOLD.toFixed(1)}V)`,
            position: "insideBottomLeft",
            fill: COLORS.inkSecondary,
            fontSize: 11,
          }}
        />
        <Tooltip
          cursor={{ stroke: COLORS.axis, strokeWidth: 1 }}
          formatter={(value: number) => [`${value.toFixed(2)}V`, "12V battery"]}
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
          dataKey="voltage"
          stroke={COLORS.blue}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          dot={makeEndDot(COLORS.blue, endIndex)}
          activeDot={{ r: 5, fill: COLORS.blue, stroke: COLORS.surface, strokeWidth: 2 }}
          label={makeEndLabel(endIndex, (v) => `${v.toFixed(2)}V`)}
          connectNulls
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
