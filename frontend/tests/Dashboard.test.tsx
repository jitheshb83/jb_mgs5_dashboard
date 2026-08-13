import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { Dashboard } from "../src/components/Dashboard";
import { mockSnapshotRealistic, mockSnapshotAllNull } from "../src/hooks/mockData";
import * as api from "../src/lib/api";

// Dashboard now also renders trend charts backed by useHistory() -> GET
// /api/history. Mock the api client so tests never hit a real network/backend
// (same pattern as BatteryUsagePage.test.tsx) -- an empty history is enough
// for these tests since chart-specific rendering is covered separately in
// tests/charts/TrendCharts.test.tsx.
vi.mock("../src/lib/api", async () => {
  const actual = await vi.importActual<typeof import("../src/lib/api")>("../src/lib/api");
  return { ...actual, getHistory: vi.fn() };
});

describe("Dashboard", () => {
  beforeEach(() => {
    vi.mocked(api.getHistory).mockReset();
    vi.mocked(api.getHistory).mockResolvedValue({ snapshots: [] });
  });

  it("renders stat cards with a realistic snapshot", async () => {
    render(<Dashboard snapshot={mockSnapshotRealistic} />);

    expect(screen.getByText("78%")).toBeTruthy();
    expect(screen.getByText("310 km")).toBeTruthy();
    expect(screen.getByText("295 km")).toBeTruthy();
    expect(screen.getByText("Not charging")).toBeTruthy();
    expect(screen.getByText("12.60 V")).toBeTruthy();
    expect(screen.getByText("21.0°C")).toBeTruthy();
    expect(screen.getByText("4210.5 km")).toBeTruthy();
    expect(screen.getAllByText("2.4 bar").length).toBe(2);
    expect(screen.getByText("Locked")).toBeTruthy();
    // 11 detail-grid items read "Closed" (all doors/windows/bonnet/boot/sunroof
    // closed in the fixture) plus 1 more from the diagram's "Closed" legend swatch.
    expect(screen.getAllByText("Closed").length).toBe(12);
    // The diagram's fixed legend also always shows "Open" and "Unknown" swatches.
    expect(screen.getByText("Open")).toBeTruthy();
    expect(screen.getByText("Unknown")).toBeTruthy();
    expect(screen.getByRole("img", { name: /diagram of the car/i })).toBeTruthy();

    await waitFor(() => expect(api.getHistory).toHaveBeenCalled());
  });

  it("renders placeholders for an all-null snapshot without crashing", async () => {
    render(<Dashboard snapshot={mockSnapshotAllNull} />);

    // Every field is null, so every rendered value should be the placeholder.
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    expect(screen.queryByText(/null/i)).toBeNull();
    expect(screen.queryByText(/undefined/i)).toBeNull();

    await waitFor(() => expect(api.getHistory).toHaveBeenCalled());
  });

  it("renders placeholders without crashing when snapshot itself is null", async () => {
    render(<Dashboard snapshot={null} />);

    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    expect(screen.queryByText(/null/i)).toBeNull();
    expect(screen.queryByText(/undefined/i)).toBeNull();

    await waitFor(() => expect(api.getHistory).toHaveBeenCalled());
  });
});
