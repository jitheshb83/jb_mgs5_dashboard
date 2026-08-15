import { useMemo } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SohEstimateItem } from "../lib/types";
import { COLORS } from "../lib/colors";
import { formatDateTime } from "../lib/format";
import { ChartEmptyState } from "./ChartEmptyState";
import { formatAxisTime, lastValidIndex, makeEndDot, makeEndLabel } from "./chartHelpers";

interface SohTrendChartProps {
  /** Estimates in chronological (oldest-first) order -- /api/soh itself returns
   * most-recent-first, same convention as /api/history, so the caller reverses it
   * first (see Dashboard.tsx). */
  estimates: SohEstimateItem[];
  isLoading?: boolean;
}

interface SohPoint {
  computedAt: string;
  sohPct: number | null;
}

/**
 * Per docs/planning/soh_methodology.md's known limitations: a single data point is noise, not
 * signal, so this stays in the "not enough data yet" empty state below this many estimates,
 * even once the API starts returning some.
 */
const MIN_ESTIMATES_TO_DISPLAY = 3;

/**
 * Derived battery SOH (State of Health) estimate over time -- one point per detected
 * full-charge cycle, not per refresh (see api_contract.md's GET /api/soh). Directional
 * estimate, not a manufacturer-verified figure -- the tooltip and section copy (Dashboard.tsx)
 * are responsible for saying so, per soh_methodology.md's "must never present as authoritative"
 * rule.
 */
export function SohTrendChart({ estimates, isLoading = false }: SohTrendChartProps) {
  const data = useMemo<SohPoint[]>(
    () => estimates.map((e) => ({ computedAt: e.computed_at, sohPct: e.soh_pct })),
    [estimates],
  );
  const { domainMin, domainMax } = useMemo(() => {
    const values = data.map((d) => d.sohPct).filter((v): v is number => v !== null);
    const dataMin = values.length ? Math.min(...values) : 90;
    const dataMax = values.length ? Math.max(...values) : 100;
    return { domainMin: Math.min(dataMin - 2, 90), domainMax: Math.max(dataMax + 2, 100) };
  }, [data]);
  const endIndex = useMemo(() => lastValidIndex(data.map((d) => d.sohPct)), [data]);

  if (estimates.length < MIN_ESTIMATES_TO_DISPLAY) {
    return <ChartEmptyState label="Battery SOH" isLoading={isLoading} />;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 12, right: 48, bottom: 8, left: 4 }}>
        <CartesianGrid stroke={COLORS.gridline} vertical={false} />
        <XAxis
          dataKey="computedAt"
          tickFormatter={formatAxisTime}
          tickLine={false}
          stroke={COLORS.axis}
          tick={{ fill: COLORS.inkMuted, fontSize: 11 }}
          minTickGap={32}
        />
        <YAxis
          domain={[domainMin, domainMax]}
          tickFormatter={(v: number) => `${v.toFixed(0)}%`}
          tickLine={false}
          stroke={COLORS.axis}
          tick={{ fill: COLORS.inkMuted, fontSize: 11 }}
          width={38}
        />
        <Tooltip
          cursor={{ stroke: COLORS.axis, strokeWidth: 1 }}
          formatter={(value: number) => [`${value.toFixed(1)}%`, "Estimated SOH"]}
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
          dataKey="sohPct"
          stroke={COLORS.blue}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          dot={makeEndDot(COLORS.blue, endIndex)}
          activeDot={{ r: 5, fill: COLORS.blue, stroke: COLORS.surface, strokeWidth: 2 }}
          label={makeEndLabel(endIndex, (v) => `${v.toFixed(1)}%`)}
          connectNulls
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
