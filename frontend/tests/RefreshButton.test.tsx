import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { RefreshButton } from "../src/components/RefreshButton";
import { useLatestSnapshot } from "../src/hooks/useLatestSnapshot";
import * as api from "../src/lib/api";
import { mockSnapshotRealistic } from "../src/hooks/mockData";

// The hook now calls the real fetch-based api client (see lib/api.ts). Mock
// it here so the test exercises the in-flight/re-enable state transition
// deterministically, without hitting a real network/backend.
vi.mock("../src/lib/api", async () => {
  const actual = await vi.importActual<typeof import("../src/lib/api")>("../src/lib/api");
  return { ...actual, getLatest: vi.fn(), refresh: vi.fn() };
});

/** Thin harness wiring RefreshButton to the real hook, so the test exercises
 * the actual in-flight state transition rather than a hand-rolled stand-in. */
function Harness() {
  const { isRefreshing, source, fetchedAt, refresh } = useLatestSnapshot();
  return (
    <RefreshButton
      onRefresh={refresh}
      isRefreshing={isRefreshing}
      source={source}
      fetchedAt={fetchedAt}
    />
  );
}

describe("RefreshButton", () => {
  beforeEach(() => {
    // Mount-time GET /api/latest: simulate "no snapshot yet" (404), which the
    // hook treats as a non-error state.
    vi.mocked(api.getLatest).mockRejectedValue(
      new api.ApiRequestError(404, { error: "no_snapshot", detail: "No snapshot exists yet." }),
    );
  });

  it("disables while a refresh is in flight and re-enables once it settles", async () => {
    let resolveRefresh!: (value: Awaited<ReturnType<typeof api.refresh>>) => void;
    vi.mocked(api.refresh).mockReturnValue(
      new Promise((resolve) => {
        resolveRefresh = resolve;
      }),
    );

    render(<Harness />);
    const button = screen.getByRole("button", { name: /refresh/i }) as HTMLButtonElement;

    expect(button.disabled).toBe(false);

    fireEvent.click(button);

    await waitFor(() => {
      expect(button.disabled).toBe(true);
    });

    resolveRefresh({
      source: "live",
      fetched_at: new Date().toISOString(),
      snapshot: mockSnapshotRealistic,
    });

    await waitFor(() => {
      expect(button.disabled).toBe(false);
    });
  });
});
