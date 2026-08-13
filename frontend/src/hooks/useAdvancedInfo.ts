import { useEffect, useState } from "react";
import type { AdvancedInfo } from "../lib/types";
import * as api from "../lib/api";
import { ApiRequestError } from "../lib/api";

export interface UseAdvancedInfoResult {
  advanced: AdvancedInfo | null;
  fetchedAt: string | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Data-fetching hook for GET /api/latest/advanced, mirroring
 * useLatestSnapshot.ts's mount-time fetch pattern: a 404 just means no
 * snapshot exists yet (not an error state), so it's swallowed rather than
 * surfaced.
 *
 * `refreshKey` should be the same `fetchedAt` App.tsx gets from
 * useLatestSnapshot -- it only changes when a genuinely new snapshot was
 * written (a live refresh, not a cached one), so passing it through here
 * refetches this page's data exactly when the underlying snapshot it's
 * derived from actually changed, even though the global Refresh button
 * lives outside this page.
 */
export function useAdvancedInfo(refreshKey?: string | null): UseAdvancedInfoResult {
  const [advanced, setAdvanced] = useState<AdvancedInfo | null>(null);
  const [fetchedAt, setFetchedAt] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getAdvanced()
      .then((result) => {
        if (cancelled) return;
        setAdvanced(result.advanced);
        setFetchedAt(result.fetched_at);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiRequestError && err.status === 404) return;
        setError(err instanceof ApiRequestError ? err.detail : "Failed to load advanced info.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return { advanced, fetchedAt, isLoading, error };
}
