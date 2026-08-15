import { describe, it, expect } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { SocTrendChart } from "../../src/charts/SocTrendChart";
import { RangeTrendChart } from "../../src/charts/RangeTrendChart";
import { VoltageTrendChart } from "../../src/charts/VoltageTrendChart";
import { SohTrendChart } from "../../src/charts/SohTrendChart";
import { mockSnapshotAllNull, mockSnapshotRealistic } from "../../src/hooks/mockData";
import type { HistorySnapshot, Snapshot, SohEstimateItem } from "../../src/lib/types";

const BASE_TIME = new Date("2026-08-01T00:00:00Z").getTime();

function wrap(snapshot: Snapshot, hoursAfterBase = 0): HistorySnapshot {
  return { fetched_at: new Date(BASE_TIME + hoursAfterBase * 3_600_000).toISOString(), snapshot };
}

/** Builds N history entries with slowly varying values, for "many history points" tests. */
function buildManySnapshots(count: number): HistorySnapshot[] {
  return Array.from({ length: count }, (_, i) =>
    wrap(
      {
        ...mockSnapshotRealistic,
        soc_pct: 50 + i,
        range_bms_km: 200 + i * 2,
        range_imcu_km: 190 + i * 2,
        battery_12v_voltage: 12.6 - i * 0.05,
      },
      i,
    ),
  );
}

function hoverChart(container: HTMLElement) {
  const surface = container.querySelector(".recharts-surface");
  if (surface) {
    fireEvent.mouseOver(surface);
    fireEvent.mouseMove(surface, { clientX: 50, clientY: 50 });
  }
}

describe("SocTrendChart", () => {
  it("shows a not-enough-data empty state with 0 points", () => {
    render(<SocTrendChart snapshots={[]} />);
    expect(screen.getByText(/not enough data yet/i)).toBeTruthy();
  });

  it("renders without crashing with exactly 1 point", () => {
    const { container } = render(<SocTrendChart snapshots={[wrap(mockSnapshotRealistic)]} />);
    expect(container.querySelector(".recharts-surface")).toBeTruthy();
  });

  it("renders without crashing with many points, and hover doesn't crash", () => {
    const { container } = render(<SocTrendChart snapshots={buildManySnapshots(20)} />);
    expect(container.querySelector(".recharts-surface")).toBeTruthy();
    expect(() => hoverChart(container)).not.toThrow();
  });

  it("handles an all-null snapshot without crashing", () => {
    const { container } = render(<SocTrendChart snapshots={[wrap(mockSnapshotAllNull)]} />);
    expect(container.querySelector(".recharts-surface")).toBeTruthy();
  });
});

describe("RangeTrendChart", () => {
  it("shows a not-enough-data empty state with 0 points", () => {
    render(<RangeTrendChart snapshots={[]} />);
    expect(screen.getByText(/not enough data yet/i)).toBeTruthy();
  });

  it("renders without crashing with exactly 1 point", () => {
    const { container } = render(<RangeTrendChart snapshots={[wrap(mockSnapshotRealistic)]} />);
    expect(container.querySelector(".recharts-surface")).toBeTruthy();
  });

  it("renders a legend with both series for many points, and hover doesn't crash", () => {
    const { container } = render(<RangeTrendChart snapshots={buildManySnapshots(20)} />);
    expect(screen.getByText("BMS")).toBeTruthy();
    expect(screen.getByText("IMCU")).toBeTruthy();
    expect(() => hoverChart(container)).not.toThrow();
  });
});

describe("VoltageTrendChart", () => {
  it("shows a not-enough-data empty state with 0 points", () => {
    render(<VoltageTrendChart snapshots={[]} />);
    expect(screen.getByText(/not enough data yet/i)).toBeTruthy();
  });

  it("renders without crashing with exactly 1 point", () => {
    const { container } = render(<VoltageTrendChart snapshots={[wrap(mockSnapshotRealistic)]} />);
    expect(container.querySelector(".recharts-surface")).toBeTruthy();
  });

  it("renders the low-voltage threshold label with many points, and hover doesn't crash", () => {
    const { container } = render(<VoltageTrendChart snapshots={buildManySnapshots(20)} />);
    expect(screen.getByText(/low voltage/i)).toBeTruthy();
    expect(() => hoverChart(container)).not.toThrow();
  });

  it("shows a loading label distinct from the empty state when isLoading is true", () => {
    render(<VoltageTrendChart snapshots={[]} isLoading />);
    expect(screen.getByText(/loading/i)).toBeTruthy();
  });
});

function buildSohEstimates(count: number): SohEstimateItem[] {
  return Array.from({ length: count }, (_, i) => ({
    computed_at: new Date(BASE_TIME + i * 86_400_000).toISOString(),
    soh_pct: 100 - i * 0.5,
    usable_kwh_estimate: 62.1 - i * 0.3,
    basis: "current_energy_kwh_delta",
  }));
}

describe("SohTrendChart", () => {
  it("shows a not-enough-data empty state with 0 estimates", () => {
    render(<SohTrendChart estimates={[]} />);
    expect(screen.getByText(/not enough data yet/i)).toBeTruthy();
  });

  it("shows a not-enough-data empty state below the minimum estimate count (1-2 points)", () => {
    // Per soh_methodology.md's known limitations: a single data point is noise, not signal.
    render(<SohTrendChart estimates={buildSohEstimates(2)} />);
    expect(screen.getByText(/not enough data yet/i)).toBeTruthy();
  });

  it("renders the chart once at least 3 estimates exist, and hover doesn't crash", () => {
    const { container } = render(<SohTrendChart estimates={buildSohEstimates(3)} />);
    expect(container.querySelector(".recharts-surface")).toBeTruthy();
    expect(() => hoverChart(container)).not.toThrow();
  });

  it("renders without crashing with many points", () => {
    const { container } = render(<SohTrendChart estimates={buildSohEstimates(20)} />);
    expect(container.querySelector(".recharts-surface")).toBeTruthy();
  });

  it("shows a loading label distinct from the empty state when isLoading is true", () => {
    render(<SohTrendChart estimates={[]} isLoading />);
    expect(screen.getByText(/loading/i)).toBeTruthy();
  });
});
