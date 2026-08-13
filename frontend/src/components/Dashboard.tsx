import { useMemo } from "react";
import type { Snapshot } from "../lib/types";
import { formatNumber } from "../lib/format";
import { useHistory } from "../hooks/useHistory";
import { SocCard } from "./SocCard";
import { RangeCard } from "./RangeCard";
import { ChargingCard } from "./ChargingCard";
import { TyrePressureCard } from "./TyrePressureCard";
import { StatCard } from "./StatCard";
import { DoorsCard } from "./DoorsCard";
import { Section } from "./Section";
import { BatteryIcon, ThermometerIcon, GaugeIcon } from "./icons";
import { ChartCard } from "../charts/ChartCard";
import { SocTrendChart } from "../charts/SocTrendChart";
import { RangeTrendChart } from "../charts/RangeTrendChart";
import { VoltageTrendChart } from "../charts/VoltageTrendChart";

interface DashboardProps {
  snapshot: Snapshot | null;
}

/**
 * Current-state dashboard grid covering every requirements.md 4.4 field
 * except vehicle location/map (deferred to v2) and SOH (no endpoint yet).
 * `snapshot` itself may be null (e.g. before any refresh has happened) —
 * every field read below falls back to null so cards render placeholders
 * instead of crashing.
 */
export function Dashboard({ snapshot }: DashboardProps) {
  const { snapshots: history, isLoading: historyLoading, error: historyError } = useHistory();

  // GET /api/history returns newest-first (see backend/src/app/db/repository.py's
  // `ORDER BY fetched_at DESC`) -- reverse to chronological (oldest-first) so
  // trend charts read left-to-right as time moving forward.
  const chronological = useMemo(() => [...history].reverse(), [history]);

  return (
    <div className="space-y-10">
      <Section title="At a glance">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <SocCard socPct={snapshot?.soc_pct ?? null} />
          <RangeCard
            rangeBmsKm={snapshot?.range_bms_km ?? null}
            rangeImcuKm={snapshot?.range_imcu_km ?? null}
          />
          <ChargingCard
            isCharging={snapshot?.is_charging ?? null}
            plugStatus={snapshot?.plug_status ?? null}
            chargingCurrent={snapshot?.charging_current ?? null}
          />
          <StatCard
            label="12V Battery"
            icon={<BatteryIcon />}
            value={formatNumber(snapshot?.battery_12v_voltage ?? null, { decimals: 2, unit: " V" })}
          />
          <StatCard
            label="Cabin Temperature"
            icon={<ThermometerIcon />}
            value={formatNumber(snapshot?.cabin_temp_c ?? null, { decimals: 1, unit: "°C" })}
          />
          <StatCard
            label="Odometer"
            icon={<GaugeIcon />}
            value={formatNumber(snapshot?.odometer_km ?? null, { decimals: 1, unit: " km" })}
          />
          <TyrePressureCard
            fl={snapshot?.tyre_pressure_fl ?? null}
            fr={snapshot?.tyre_pressure_fr ?? null}
            rl={snapshot?.tyre_pressure_rl ?? null}
            rr={snapshot?.tyre_pressure_rr ?? null}
          />
        </div>
      </Section>

      <Section title="Trends" description="From your recent refresh history.">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <ChartCard title="State of Charge">
            <SocTrendChart snapshots={chronological} isLoading={historyLoading} />
          </ChartCard>
          <ChartCard title="12V Battery Voltage">
            <VoltageTrendChart snapshots={chronological} isLoading={historyLoading} />
          </ChartCard>
          <ChartCard title="Estimated Range" className="lg:col-span-2">
            <RangeTrendChart snapshots={chronological} isLoading={historyLoading} />
          </ChartCard>
        </div>
        {historyError ? (
          <p role="alert" className="text-sm text-red-600">
            {historyError}
          </p>
        ) : null}
      </Section>

      <Section title="Doors & Locks">
        <DoorsCard doors={snapshot?.doors ?? null} />
      </Section>
    </div>
  );
}
