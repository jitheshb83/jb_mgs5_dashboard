import { useCallback, useEffect, useState } from "react";
import type { RefreshSource, Snapshot } from "../lib/types";
import * as api from "../lib/api";
import { ApiRequestError } from "../lib/api";

export interface UseLatestSnapshotResult {
  snapshot: Snapshot | null;
  fetchedAt: string | null;
  source: RefreshSource | null;
  isLoading: boolean;
  isRefreshing: boolean;
  error: string | null;
  /** Triggers a live/cached refresh via POST /api/refresh. */
  refresh: () => Promise<void>;
}

/**
 * Data-fetching hook for the dashboard's current snapshot + refresh action.
 *
 * On mount, seeds from GET /api/latest (a 404 just means no snapshot exists
 * yet -- not an error state, so it's swallowed rather than surfaced).
 *
 * Per api_contract.md's rate-limit contract, this hook does NOT implement its
 * own gating logic -- it only tracks in-flight state for the button, and
 * surfaces whatever `source` the backend response reports.
 */
export function useLatestSnapshot(): UseLatestSnapshotResult {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [fetchedAt, setFetchedAt] = useState<string | null>(null);
  const [source, setSource] = useState<RefreshSource | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getLatest()
      .then((result) => {
        if (cancelled) return;
        setSnapshot(result.snapshot);
        setFetchedAt(result.fetched_at);
        setSource("cached");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiRequestError && err.status === 404) return;
        setError(err instanceof ApiRequestError ? err.detail : "Failed to load the latest snapshot.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const result = await api.refresh();
      setSnapshot(result.snapshot);
      setFetchedAt(result.fetched_at);
      setSource(result.source);
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.detail
          : err instanceof Error
            ? err.message
            : "Failed to refresh.",
      );
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  return { snapshot, fetchedAt, source, isLoading, isRefreshing, error, refresh };
}
