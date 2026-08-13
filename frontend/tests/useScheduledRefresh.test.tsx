import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useScheduledRefresh } from "../src/hooks/useScheduledRefresh";

describe("useScheduledRefresh", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("does not call refresh when disabled", () => {
    const refresh = vi.fn();
    renderHook(() => useScheduledRefresh(false, 30, refresh));

    vi.advanceTimersByTime(60 * 60_000);
    expect(refresh).not.toHaveBeenCalled();
  });

  it("calls refresh once per interval when enabled", () => {
    const refresh = vi.fn();
    renderHook(() => useScheduledRefresh(true, 30, refresh));

    vi.advanceTimersByTime(30 * 60_000);
    expect(refresh).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(30 * 60_000);
    expect(refresh).toHaveBeenCalledTimes(2);
  });

  it("stops firing once unmounted (matches the 'stops when tab closes' decision)", () => {
    const refresh = vi.fn();
    const { unmount } = renderHook(() => useScheduledRefresh(true, 30, refresh));

    unmount();
    vi.advanceTimersByTime(60 * 60_000);
    expect(refresh).not.toHaveBeenCalled();
  });

  it("restarts the timer when re-enabled after being disabled", () => {
    const refresh = vi.fn();
    const { rerender } = renderHook(
      ({ enabled }: { enabled: boolean }) => useScheduledRefresh(enabled, 30, refresh),
      { initialProps: { enabled: false } },
    );

    vi.advanceTimersByTime(30 * 60_000);
    expect(refresh).not.toHaveBeenCalled();

    rerender({ enabled: true });
    vi.advanceTimersByTime(30 * 60_000);
    expect(refresh).toHaveBeenCalledTimes(1);
  });
});
