interface ChartEmptyStateProps {
  label: string;
  isLoading?: boolean;
}

/**
 * Friendly empty state for a trend chart with no history points yet, in the
 * same honest "not enough data yet" tone used elsewhere in this app (see
 * docs/planning/soh_methodology.md's SOH empty state).
 */
export function ChartEmptyState({ label, isLoading = false }: ChartEmptyStateProps) {
  return (
    <div className="flex h-[220px] flex-col items-center justify-center gap-1 px-4 text-center">
      <p className="text-sm font-medium text-slate-600">
        {isLoading ? `Loading ${label.toLowerCase()} trend…` : "Not enough data yet"}
      </p>
      {isLoading ? null : (
        <p className="text-xs text-slate-400">
          Refresh a few more times to start building a {label.toLowerCase()} trend.
        </p>
      )}
    </div>
  );
}
