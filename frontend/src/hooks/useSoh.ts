import { useEffect, useState } from "react";
import type { SohEstimateItem } from "../lib/types";
import * as api from "../lib/api";
import { ApiRequestError } from "../lib/api";

export interface UseSohResult {
  estimates: SohEstimateItem[];
  nameplateUsableKwh: number | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * SOH trend hook backed by GET /api/soh. Fetches once on mount, same pattern
 * as useHistory.ts (the "Trends" section doesn't currently re-fetch on new
 * refreshes -- not something this hook changes).
 */
export function useSoh(): UseSohResult {
  const [estimates, setEstimates] = useState<SohEstimateItem[]>([]);
  const [nameplateUsableKwh, setNameplateUsableKwh] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getSoh()
      .then((result) => {
        if (cancelled) return;
        setEstimates(result.estimates);
        setNameplateUsableKwh(result.nameplate_usable_kwh);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiRequestError ? err.detail : "Failed to load SOH estimate.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { estimates, nameplateUsableKwh, isLoading, error };
}
