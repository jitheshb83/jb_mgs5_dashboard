import { useState } from "react";
import { useLatestSnapshot } from "./hooks/useLatestSnapshot";
import { useSettings } from "./hooks/useSettings";
import { useScheduledRefresh } from "./hooks/useScheduledRefresh";
import { RefreshButton } from "./components/RefreshButton";
import { Dashboard } from "./components/Dashboard";
import { SettingsPanel } from "./components/SettingsPanel";
import { AdvancedInfoPage } from "./components/AdvancedInfoPage";
import { BatteryUsagePage } from "./components/BatteryUsagePage";

type View = "dashboard" | "settings" | "advanced" | "battery";

const NAV_ITEMS: { view: View; label: string }[] = [
  { view: "dashboard", label: "Dashboard" },
  { view: "advanced", label: "Advanced Info" },
  { view: "battery", label: "Battery Usage" },
  { view: "settings", label: "Settings" },
];

export default function App() {
  const { snapshot, fetchedAt, source, isRefreshing, error, refresh } = useLatestSnapshot();
  const { settings, isSaving, updateSettings } = useSettings();
  const [view, setView] = useState<View>("dashboard");

  useScheduledRefresh(settings.schedule_enabled, settings.schedule_interval_minutes, refresh);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">MGS5 Dashboard</h1>
            <p className="text-sm text-slate-500">MG MGS5 EV — status at a glance</p>
          </div>
          <nav className="flex flex-wrap gap-2">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.view}
                type="button"
                onClick={() => setView(item.view)}
                aria-current={view === item.view ? "page" : undefined}
                className={`rounded-full border px-4 py-2 text-sm font-medium transition ${
                  view === item.view
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-100"
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </header>

        <div className="mb-6">
          <RefreshButton
            onRefresh={refresh}
            isRefreshing={isRefreshing}
            source={source}
            fetchedAt={fetchedAt}
            error={error}
          />
        </div>

        {view === "settings" ? (
          <SettingsPanel settings={settings} isSaving={isSaving} onSave={updateSettings} />
        ) : view === "advanced" ? (
          <AdvancedInfoPage refreshKey={fetchedAt} />
        ) : view === "battery" ? (
          <BatteryUsagePage refreshKey={fetchedAt} />
        ) : (
          <Dashboard snapshot={snapshot} />
        )}
      </div>
    </div>
  );
}
