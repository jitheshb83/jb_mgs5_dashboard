import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, renderHook } from "@testing-library/react";
import { AdvancedInfoPage } from "../src/components/AdvancedInfoPage";
import { useAdvancedInfo } from "../src/hooks/useAdvancedInfo";
import * as api from "../src/lib/api";

// Mock the fetch-based api client so the test never hits a real network/backend.
vi.mock("../src/lib/api", async () => {
  const actual = await vi.importActual<typeof import("../src/lib/api")>("../src/lib/api");
  return { ...actual, getAdvanced: vi.fn() };
});

describe("AdvancedInfoPage", () => {
  beforeEach(() => {
    vi.mocked(api.getAdvanced).mockReset();
  });

  it("renders decoded fields and a distinct raw/undecoded section", async () => {
    vi.mocked(api.getAdvanced).mockResolvedValue({
      fetched_at: "2026-08-12T14:30:00Z",
      advanced: {
        engine_running: true,
        remote_climate_state: "off",
        alarm_active: false,
        latitude: 59.91,
        raw_undecoded: {
          someUnknownSaicField: 42,
        },
      },
    });

    render(<AdvancedInfoPage />);

    await waitFor(() => {
      expect(screen.getByText("Engine Running")).toBeTruthy();
    });

    expect(screen.getByText("Yes")).toBeTruthy();
    expect(screen.getByText("Remote Climate State")).toBeTruthy();
    expect(screen.getByText("off")).toBeTruthy();
    expect(screen.getByText("Alarm Active")).toBeTruthy();
    expect(screen.getByText("No")).toBeTruthy();
    expect(screen.getByText("59.91")).toBeTruthy();

    // Raw/undecoded section renders with a human-readable label (fallback
    // camelCase split, since this key has no entry in RAW_FIELD_LABELS) AND
    // the original raw SAIC field name (for cross-referencing), plus the
    // untouched raw value.
    expect(screen.getByText("Raw / undecoded values")).toBeTruthy();
    expect(screen.getByText("Some Unknown Saic Field")).toBeTruthy();
    expect(screen.getByText("(someUnknownSaicField)")).toBeTruthy();
    expect(screen.getByText("42")).toBeTruthy();
  });

  it("renders an object-valued decoded field as readable key/value pairs, not raw JSON", async () => {
    // Regression test: scheduled_charging/obc_ac_input/hv_battery are structs, not
    // scalars -- formatValue() must not dump raw JSON (unreadable, and long
    // JSON previously overflowed/overlapped the stacked label+value layout).
    vi.mocked(api.getAdvanced).mockResolvedValue({
      fetched_at: "2026-08-12T14:30:00Z",
      advanced: {
        scheduled_charging: { mode: "DISABLED", start_time: "22:00", end_time: "06:00" },
      },
    });

    render(<AdvancedInfoPage />);

    await waitFor(() => {
      expect(screen.getByText("Scheduled Charging")).toBeTruthy();
    });
    expect(screen.getByText("Mode: DISABLED · Start Time: 22:00 · End Time: 06:00")).toBeTruthy();
    expect(screen.queryByText(/\{"mode"/)).toBeNull();
  });

  it("uses a known human-readable label for a mapped raw field, not just the fallback split", async () => {
    vi.mocked(api.getAdvanced).mockResolvedValue({
      fetched_at: "2026-08-12T14:30:00Z",
      advanced: {
        raw_undecoded: {
          canBusActive: 1,
          alertDataSum: [0, 0, 1, 0],
        },
      },
    });

    render(<AdvancedInfoPage />);

    await waitFor(() => {
      expect(screen.getByText("CAN Bus Active")).toBeTruthy();
    });
    expect(screen.getByText("(canBusActive)")).toBeTruthy();
    expect(screen.getByText("Vehicle Alert Codes (raw)")).toBeTruthy();
    // Array values are summarized, not dumped inline, per the honesty-without-
    // clutter approach -- exact contents remain available via the tooltip.
    expect(screen.getByText("4 values, 1 non-zero")).toBeTruthy();
  });

  it("renders without crashing on an empty/null-heavy advanced object", async () => {
    vi.mocked(api.getAdvanced).mockResolvedValue({
      fetched_at: "2026-08-12T14:30:00Z",
      advanced: {
        engine_running: null,
        alarm_active: null,
      },
    });

    render(<AdvancedInfoPage />);

    await waitFor(() => {
      expect(screen.getByText("Engine Running")).toBeTruthy();
    });

    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    expect(screen.queryByText(/^null$/i)).toBeNull();
    expect(screen.queryByText(/^undefined$/i)).toBeNull();
    // No raw_undecoded key was present, so that section should not render.
    expect(screen.queryByText("Raw / undecoded values")).toBeNull();
  });

  it("treats a 404 (no snapshot yet) as a no-data state, not an error", async () => {
    vi.mocked(api.getAdvanced).mockRejectedValue(
      new api.ApiRequestError(404, { error: "no_snapshot", detail: "No snapshot exists yet." }),
    );

    render(<AdvancedInfoPage />);

    await waitFor(() => {
      expect(screen.getByText(/no advanced info available yet/i)).toBeTruthy();
    });
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("refetches when refreshKey changes (e.g. the global Refresh button pulled a new snapshot)", async () => {
    vi.mocked(api.getAdvanced).mockResolvedValue({
      fetched_at: "2026-08-12T14:30:00Z",
      advanced: { engine_running: false },
    });

    const { rerender } = renderHook(({ refreshKey }: { refreshKey: string | null }) => useAdvancedInfo(refreshKey), {
      initialProps: { refreshKey: null as string | null },
    });

    await waitFor(() => expect(api.getAdvanced).toHaveBeenCalledTimes(1));

    rerender({ refreshKey: "2026-08-12T15:00:00Z" });
    await waitFor(() => expect(api.getAdvanced).toHaveBeenCalledTimes(2));

    // Re-rendering with the SAME refreshKey must not trigger another fetch.
    rerender({ refreshKey: "2026-08-12T15:00:00Z" });
    expect(api.getAdvanced).toHaveBeenCalledTimes(2);
  });
});
