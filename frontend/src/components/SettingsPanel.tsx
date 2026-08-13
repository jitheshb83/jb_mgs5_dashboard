import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { Settings } from "../lib/types";

interface SettingsPanelProps {
  settings: Settings;
  isSaving: boolean;
  onSave: (partial: Partial<Settings>) => Promise<Settings>;
}

/**
 * Settings form: schedule toggle + interval, min refresh gap, nameplate kWh.
 * Validates client-side (mirroring api_contract.md's PUT /api/settings 400
 * case — schedule_interval_minutes must be >= min_refresh_gap_minutes)
 * before submitting, and blocks submission with a visible error if invalid.
 */
export function SettingsPanel({ settings, isSaving, onSave }: SettingsPanelProps) {
  const [form, setForm] = useState<Settings>(settings);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // useSettings() seeds `settings` with a fallback and asynchronously replaces
  // it once GET /api/settings resolves (and again after a successful save).
  // useState's initializer only reads `settings` at mount, so without this
  // effect a form opened before that fetch resolves would keep showing/
  // submitting the stale fallback values forever.
  useEffect(() => {
    setForm(settings);
  }, [settings]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);

    if (form.schedule_interval_minutes < form.min_refresh_gap_minutes) {
      setError(
        `Schedule interval (${form.schedule_interval_minutes} min) must be at least the ` +
          `minimum refresh gap (${form.min_refresh_gap_minutes} min).`,
      );
      return;
    }

    setError(null);
    onSave(form)
      .then(() => setSaved(true))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to save settings.");
      });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-900/5"
    >
      <h2 className="text-lg font-semibold text-slate-900">Settings</h2>

      <label className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">Scheduled refresh</span>
        <input
          type="checkbox"
          checked={form.schedule_enabled}
          onChange={(event) => setForm((f) => ({ ...f, schedule_enabled: event.target.checked }))}
          className="h-4 w-4"
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-slate-700">Schedule interval (minutes)</span>
        <input
          type="number"
          value={form.schedule_interval_minutes}
          onChange={(event) =>
            setForm((f) => ({ ...f, schedule_interval_minutes: Number(event.target.value) }))
          }
          className="mt-1 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-slate-700">Minimum refresh gap (minutes)</span>
        <input
          type="number"
          value={form.min_refresh_gap_minutes}
          onChange={(event) =>
            setForm((f) => ({ ...f, min_refresh_gap_minutes: Number(event.target.value) }))
          }
          className="mt-1 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
        />
      </label>

      <label className="block">
        <span className="text-sm font-medium text-slate-700">Battery nameplate capacity (kWh)</span>
        <input
          type="number"
          step="0.1"
          value={form.battery_nameplate_kwh}
          onChange={(event) =>
            setForm((f) => ({ ...f, battery_nameplate_kwh: Number(event.target.value) }))
          }
          className="mt-1 block w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
        />
      </label>

      {error ? (
        <p role="alert" className="text-sm text-red-600">
          {error}
        </p>
      ) : null}
      {saved && !error ? <p className="text-sm text-emerald-600">Settings saved.</p> : null}

      <button
        type="submit"
        disabled={isSaving}
        className="rounded-full bg-slate-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        {isSaving ? "Saving…" : "Save settings"}
      </button>
    </form>
  );
}
