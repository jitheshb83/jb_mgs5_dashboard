import { COLORS } from "../lib/colors";

/**
 * Shared building blocks for the three trend charts (SocTrendChart,
 * RangeTrendChart, VoltageTrendChart). Kept here rather than duplicated
 * three times since the "end dot + end label, only on the last real value"
 * pattern repeats for every series across all three charts.
 */

/**
 * Compact axis-tick timestamp: "12 Aug, 14:30". Distinct from lib/format.ts's
 * `formatDateTime` (used for the tooltip's full label and elsewhere in the
 * app) -- axis ticks need to stay short since several render side by side.
 */
export function formatAxisTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Index of the last non-null value for a numeric series, or -1 if all null. */
export function lastValidIndex(values: (number | null)[]): number {
  for (let i = values.length - 1; i >= 0; i -= 1) {
    if (values[i] !== null) return i;
  }
  return -1;
}

interface DotRenderProps {
  cx?: number;
  cy?: number;
  index?: number;
  value?: number | null;
}

/**
 * Builds a recharts `dot` renderer that only draws a marker at the series'
 * last real value -- per the mark spec, dots mark line ends, not every
 * point (which would be noise once history has many snapshots).
 */
export function makeEndDot(color: string, endIndex: number) {
  return (props: DotRenderProps) => {
    const { cx, cy, index } = props;
    // recharts maps dot renderers across every point in the series, and
    // requires a valid (if empty) keyed SVG element back for each one.
    if (index !== endIndex || cx === undefined || cy === undefined) {
      return <g key={`dot-${index}`} />;
    }
    return (
      <circle key={`dot-${index}`} cx={cx} cy={cy} r={4} fill={color} stroke={COLORS.surface} strokeWidth={2} />
    );
  };
}

interface LabelRenderProps {
  x?: number;
  y?: number;
  index?: number;
  value?: number;
}

/**
 * Builds a recharts `label` renderer that draws the value in ink (never the
 * series color, per "text never wears data color") beside the last point
 * only -- selective direct labels, not one per point.
 */
export function makeEndLabel(endIndex: number, formatValue: (v: number) => string, dy = 0) {
  return (props: LabelRenderProps) => {
    const { x, y, index, value } = props;
    if (index !== endIndex || x === undefined || y === undefined || value === undefined) {
      return <g key={`label-${index}`} />;
    }
    return (
      <text
        key={`label-${index}`}
        x={x + 8}
        y={y + dy}
        dy={4}
        fontSize={12}
        fontWeight={600}
        fill={COLORS.inkSecondary}
        textAnchor="start"
      >
        {formatValue(value)}
      </text>
    );
  };
}
