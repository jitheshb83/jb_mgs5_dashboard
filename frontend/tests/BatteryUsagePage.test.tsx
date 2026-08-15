import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { BatteryUsagePage } from "../src/components/BatteryUsagePage";
import * as api from "../src/lib/api";

// Mock the fetch-based api client so the test never hits a real network/backend.
vi.mock("../src/lib/api", async () => {
  const actual = await vi.importActual<typeof import("../src/lib/api")>("../src/lib/api");
  return { ...actual, getBatteryUsage: vi.fn() };
});

describe("BatteryUsagePage", () => {
  beforeEach(() => {
    vi.mocked(api.getBatteryUsage).mockReset();
  });

  it("renders a stat card per field with real data", async () => {
    vi.mocked(api.getBatteryUsage).mockResolvedValue({
      fetched_at: "2026-08-12T14:30:00Z",
      battery_usage: {
        total_battery_capacity_kwh: 61.8,
        power_usage_today_kwh: 4.2,
        power_usage_since_last_charge_kwh: 12.6,
        last_charge_added_kwh: 38.4,
        current_energy_kwh: 34.6,
        mileage_today_km: 21.3,
        mileage_since_last_charge_km: 143.7,
        efficiency_today_kwh_per_100km: 19.72,
        efficiency_since_last_charge_kwh_per_100km: 8.77,
        estimated_fields: [],
      },
    });

    render(<BatteryUsagePage />);

    await waitFor(() => {
      expect(screen.getByText("61.8 kWh")).toBeTruthy();
    });

    expect(screen.getByText("4.2 kWh")).toBeTruthy();
    expect(screen.getByText("12.6 kWh")).toBeTruthy();
    expect(screen.getByText("38.4 kWh")).toBeTruthy();
    expect(screen.getByText("34.6 kWh")).toBeTruthy();
    expect(screen.getByText("21.3 km")).toBeTruthy();
    expect(screen.getByText("143.7 km")).toBeTruthy();
    expect(screen.getByText("19.7 kWh/100km")).toBeTruthy();
    expect(screen.getByText("8.8 kWh/100km")).toBeTruthy();
    // Efficiency is never vehicle-reported, so it always carries a note -- but not the
    // "estimated from history" one, since neither input here was estimated.
    expect(screen.queryByText(/estimated from observed history/i)).toBeNull();
    expect(screen.getAllByText(/not vehicle-reported/i).length).toBe(2);
  });

  it("flags history-derived fields as estimates, per the 2026-08-15 contract correction", async () => {
    vi.mocked(api.getBatteryUsage).mockResolvedValue({
      fetched_at: "2026-08-15T18:01:00Z",
      battery_usage: {
        total_battery_capacity_kwh: 62.1,
        power_usage_today_kwh: 0,
        power_usage_since_last_charge_kwh: 6.21,
        last_charge_added_kwh: 37.26,
        current_energy_kwh: null,
        mileage_today_km: 0,
        mileage_since_last_charge_km: 20,
        efficiency_today_kwh_per_100km: null,
        efficiency_since_last_charge_kwh_per_100km: 31.05,
        estimated_fields: [
          "total_battery_capacity_kwh",
          "power_usage_since_last_charge_kwh",
          "last_charge_added_kwh",
          "mileage_since_last_charge_km",
          "efficiency_since_last_charge_kwh_per_100km",
        ],
      },
    });

    render(<BatteryUsagePage />);

    await waitFor(() => {
      expect(screen.getAllByText(/estimated from observed history/i).length).toBe(5);
    });
  });

  it("renders placeholders for an all-null battery_usage response without crashing", async () => {
    vi.mocked(api.getBatteryUsage).mockResolvedValue({
      fetched_at: "2026-08-12T14:30:00Z",
      battery_usage: {
        total_battery_capacity_kwh: null,
        power_usage_today_kwh: null,
        power_usage_since_last_charge_kwh: null,
        last_charge_added_kwh: null,
        current_energy_kwh: null,
        mileage_today_km: null,
        mileage_since_last_charge_km: null,
        efficiency_today_kwh_per_100km: null,
        efficiency_since_last_charge_kwh_per_100km: null,
        estimated_fields: [],
      },
    });

    render(<BatteryUsagePage />);

    await waitFor(() => {
      expect(screen.getAllByText("—").length).toBe(9);
    });
    expect(screen.queryByText(/null/i)).toBeNull();
    expect(screen.queryByText(/undefined/i)).toBeNull();
  });

  it("treats a 404 (no snapshot yet) as a no-data state, not an error", async () => {
    vi.mocked(api.getBatteryUsage).mockRejectedValue(
      new api.ApiRequestError(404, { error: "no_snapshot", detail: "No snapshot exists yet." }),
    );

    render(<BatteryUsagePage />);

    await waitFor(() => {
      expect(screen.getByText(/no battery usage data available yet/i)).toBeTruthy();
    });
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
