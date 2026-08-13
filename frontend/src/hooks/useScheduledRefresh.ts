import { useEffect } from "react";

/**
 * Drives the optional scheduled-refresh feature (docs/planning/decisions_log.md:
 * "Optional scheduled refresh, off by default, frontend-timer-driven only --
 * stops when tab closes"). A plain setInterval naturally satisfies the
 * "stops when tab closes" requirement, and cleans up on every
 * enabled/interval change so stale timers never stack up.
 *
 * The server-side 30-minute floor (services/rate_limit.py) is still the real
 * enforcement point -- this timer only decides when to *ask* for a refresh;
 * the backend's cached-vs-live response is the source of truth either way.
 */
export function useScheduledRefresh(
  enabled: boolean,
  intervalMinutes: number,
  refresh: () => void | Promise<void>,
): void {
  useEffect(() => {
    if (!enabled || intervalMinutes <= 0) return undefined;
    const id = setInterval(() => {
      void refresh();
    }, intervalMinutes * 60_000);
    return () => clearInterval(id);
  }, [enabled, intervalMinutes, refresh]);
}
