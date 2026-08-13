import { useCallback, useEffect, useState } from "react";
import type { Settings } from "../lib/types";
import * as api from "../lib/api";
import { ApiRequestError } from "../lib/api";

// Mirrors the defaults app_settings is seeded with on backend startup (see
// data_model.md) -- only used as a placeholder until GET /api/settings resolves.
const FALLBACK_SETTINGS: Settings = {
  schedule_enabled: false,
  schedule_interval_minutes: 120,
  min_refresh_gap_minutes: 30,
  battery_nameplate_kwh: 62.1,
};

export interface UseSettingsResult {
  settings: Settings;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  /** Submits a partial settings update via PUT /api/settings. Throws on failure. */
  updateSettings: (partial: Partial<Settings>) => Promise<Settings>;
}

/**
 * Settings hook, backed by GET/PUT /api/settings.
 *
 * Note: this hook does not itself enforce the contract's validation rule
 * (schedule_interval_minutes >= min_refresh_gap_minutes) -- that's done
 * client-side in the SettingsPanel form before calling updateSettings, as a
 * courtesy (fewer round trips). The backend's 400 response remains the
 * source of truth and is surfaced via `error` if it fires anyway.
 */
export function useSettings(): UseSettingsResult {
  const [settings, setSettings] = useState<Settings>(FALLBACK_SETTINGS);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .getSettings()
      .then((result) => {
        if (!cancelled) setSettings(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiRequestError ? err.detail : "Failed to load settings.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const updateSettings = useCallback(async (partial: Partial<Settings>) => {
    setIsSaving(true);
    setError(null);
    try {
      const updated = await api.updateSettings(partial);
      setSettings(updated);
      return updated;
    } catch (err) {
      const message =
        err instanceof ApiRequestError
          ? err.detail
          : err instanceof Error
            ? err.message
            : "Failed to update settings.";
      setError(message);
      throw err;
    } finally {
      setIsSaving(false);
    }
  }, []);

  return { settings, isLoading, isSaving, error, updateSettings };
}
