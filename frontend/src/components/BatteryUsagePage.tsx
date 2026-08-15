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

  const estimated = new Set(batteryUsage.estimated_fields);
  const estimatedNote = "Estimated from observed history — the vehicle didn't report this directly.";

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-500">As of {formatDateTime(fetchedAt)}</p>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Total Battery Capacity"
          value={formatNumber(batteryUsage.total_battery_capacity_kwh, { decimals: 1, unit: " kWh" })}
          sublabel={estimated.has("total_battery_capacity_kwh") ? estimatedNote : undefined}
        />
        <StatCard
          label="Power Usage Today"
          value={formatNumber(batteryUsage.power_usage_today_kwh, { decimals: 1, unit: " kWh" })}
          sublabel={estimated.has("power_usage_today_kwh") ? estimatedNote : undefined}
        />
        <StatCard
          label="Power Usage Since Last Charge"
          value={formatNumber(batteryUsage.power_usage_since_last_charge_kwh, {
            decimals: 1,
            unit: " kWh",
          })}
          sublabel={estimated.has("power_usage_since_last_charge_kwh") ? estimatedNote : undefined}
        />
        <StatCard
          label="Last Charge Added"
          value={formatNumber(batteryUsage.last_charge_added_kwh, { decimals: 1, unit: " kWh" })}
          sublabel={estimated.has("last_charge_added_kwh") ? estimatedNote : undefined}
        />
        <StatCard
          label="Current Energy"
          value={formatNumber(batteryUsage.current_energy_kwh, { decimals: 1, unit: " kWh" })}
        />
        <StatCard
          label="Mileage Today"
          value={formatNumber(batteryUsage.mileage_today_km, { decimals: 1, unit: " km" })}
          sublabel={estimated.has("mileage_today_km") ? estimatedNote : undefined}
        />
        <StatCard
          label="Mileage Since Last Charge"
          value={formatNumber(batteryUsage.mileage_since_last_charge_km, {
            decimals: 1,
            unit: " km",
          })}
          sublabel={estimated.has("mileage_since_last_charge_km") ? estimatedNote : undefined}
        />
        <StatCard
          label="Efficiency Today"
          value={formatNumber(batteryUsage.efficiency_today_kwh_per_100km, {
            decimals: 1,
            unit: " kWh/100km",
          })}
          sublabel={
            estimated.has("efficiency_today_kwh_per_100km") ? estimatedNote : "Not vehicle-reported — always calculated."
          }
        />
        <StatCard
          label="Efficiency Since Last Charge"
          value={formatNumber(batteryUsage.efficiency_since_last_charge_kwh_per_100km, {
            decimals: 1,
            unit: " kWh/100km",
          })}
          sublabel={
            estimated.has("efficiency_since_last_charge_kwh_per_100km")
              ? estimatedNote
              : "Not vehicle-reported — always calculated."
          }
        />
      </div>
    </div>
  );
}
