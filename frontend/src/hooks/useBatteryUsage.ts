import { useEffect, useState } from "react";
import type { BatteryUsage } from "../lib/types";
import * as api from "../lib/api";
import { ApiRequestError } from "../lib/api";

export interface UseBatteryUsageResult {
  batteryUsage: BatteryUsage | null;
  fetchedAt: string | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Data-fetching hook for GET /api/latest/battery-usage, mirroring
 * useLatestSnapshot.ts's mount-time fetch pattern: a 404 just means no
 * snapshot exists yet (not an error state), so it's swallowed rather than
 * surfaced.
 *
 * `refreshKey` should be the same `fetchedAt` App.tsx gets from
 * useLatestSnapshot -- see useAdvancedInfo.ts's docstring for why.
 */
export function useBatteryUsage(refreshKey?: string | null): UseBatteryUsageResult {
  const [batteryUsage, setBatteryUsage] = useState<BatteryUsage | null>(null);
  const [fetchedAt, setFetchedAt] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getBatteryUsage()
      .then((result) => {
        if (cancelled) return;
        setBatteryUsage(result.battery_usage);
        setFetchedAt(result.fetched_at);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiRequestError && err.status === 404) return;
        setError(err instanceof ApiRequestError ? err.detail : "Failed to load battery usage.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return { batteryUsage, fetchedAt, isLoading, error };
}
