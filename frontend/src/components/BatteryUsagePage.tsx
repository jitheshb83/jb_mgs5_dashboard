import { useBatteryUsage } from "../hooks/useBatteryUsage";
import { formatDateTime, formatNumber } from "../lib/format";
import { StatCard } from "./StatCard";

interface BatteryUsagePageProps {
  /** The main dashboard's `fetchedAt` -- triggers a refetch when a new snapshot lands. */
  refreshKey?: string | null;
}

/** Renders GET /api/latest/battery-usage's fixed, known field list as stat cards. */
export function BatteryUsagePage({ refreshKey }: BatteryUsagePageProps) {
  const { batteryUsage, fetchedAt, isLoading, error } = useBatteryUsage(refreshKey);

  if (isLoading) {
    return <p className="text-sm text-slate-500">Loading battery usage…</p>;
  }
  if (error) {
    return (
      <p role="alert" className="text-sm text-red-600">
        {error}
      </p>
    );
  }
  if (!batteryUsage) {
    return (
      <p className="text-sm text-slate-500">
        No battery usage data available yet — refresh to fetch data.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-500">As of {formatDateTime(fetchedAt)}</p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Total Battery Capacity"
          value={formatNumber(batteryUsage.total_battery_capacity_kwh, { decimals: 1, unit: " kWh" })}
        />
        <StatCard
          label="Power Usage Today"
          value={formatNumber(batteryUsage.power_usage_today_kwh, { decimals: 1, unit: " kWh" })}
        />
        <StatCard
          label="Power Usage Since Last Charge"
          value={formatNumber(batteryUsage.power_usage_since_last_charge_kwh, {
            decimals: 1,
            unit: " kWh",
          })}
        />
        <StatCard
          label="Last Charge Added"
          value={formatNumber(batteryUsage.last_charge_added_kwh, { decimals: 1, unit: " kWh" })}
        />
        <StatCard
          label="Current Energy"
          value={formatNumber(batteryUsage.current_energy_kwh, { decimals: 1, unit: " kWh" })}
        />
        <StatCard
          label="Mileage Today"
          value={formatNumber(batteryUsage.mileage_today_km, { decimals: 1, unit: " km" })}
        />
        <StatCard
          label="Mileage Since Last Charge"
          value={formatNumber(batteryUsage.mileage_since_last_charge_km, {
            decimals: 1,
            unit: " km",
          })}
        />
      </div>
    </div>
  );
}
