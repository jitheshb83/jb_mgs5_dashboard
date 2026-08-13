import type { RefreshSource } from "../lib/types";
import { formatDateTime } from "../lib/format";

interface RefreshButtonProps {
  onRefresh: () => Promise<void>;
  isRefreshing: boolean;
  source: RefreshSource | null;
  fetchedAt: string | null;
  error?: string | null;
}

/**
 * Refresh trigger + status display. Per api_contract.md's rate-limit contract,
 * this component implements NO client-side gating of its own — it only
 * disables while a request is in flight, and displays whatever `source`
 * ("live" | "cached") and `fetched_at` the backend response reports.
 */
export function RefreshButton({ onRefresh, isRefreshing, source, fetchedAt, error }: RefreshButtonProps) {
  return (
    <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm text-slate-500">
          Last updated: <span className="text-slate-700">{formatDateTime(fetchedAt)}</span>
          {source ? (
            <span
              className={`ml-2 rounded-full px-2 py-0.5 text-xs font-medium ${
                source === "live" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
              }`}
            >
              {source}
            </span>
          ) : null}
        </p>
        {error ? <p className="mt-1 text-sm text-red-600">{error}</p> : null}
      </div>
      <button
        type="button"
        onClick={() => {
          void onRefresh();
        }}
        disabled={isRefreshing}
        className="rounded-full bg-slate-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {isRefreshing ? "Refreshing…" : "Refresh"}
      </button>
    </div>
  );
}
