import { useEffect, useState } from "react";
import type { HistoryParams, HistorySnapshot } from "../lib/types";
import * as api from "../lib/api";
import { ApiRequestError } from "../lib/api";

export interface UseHistoryResult {
  snapshots: HistorySnapshot[];
  isLoading: boolean;
  error: string | null;
}

/**
 * History hook backed by GET /api/history. Feeds the trend charts on the
 * main Dashboard.
 */
export function useHistory(params: HistoryParams = {}): UseHistoryResult {
  const [snapshots, setSnapshots] = useState<HistorySnapshot[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { from, to, limit } = params;

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    api
      .getHistory({ from, to, limit })
      .then((result) => {
        if (!cancelled) setSnapshots(result.snapshots);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiRequestError ? err.detail : "Failed to load history.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [from, to, limit]);

  return { snapshots, isLoading, error };
}
