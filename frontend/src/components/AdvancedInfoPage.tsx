import { useAdvancedInfo } from "../hooks/useAdvancedInfo";
import { PLACEHOLDER, formatDateTime } from "../lib/format";
import { labelForRawField } from "../lib/rawFieldLabels";

/** snake_case key -> "Title Case" label, e.g. `remote_climate_state` -> "Remote Climate State". */
function labelify(key: string): string {
  return key
    .split("_")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Generic value formatter for the advanced page's unknown-shaped fields.
 * Booleans/numbers/strings get sensible display forms; nested objects (e.g.
 * `scheduled_charging`, `hv_battery`) render as "Label: value" pairs rather
 * than raw JSON, since several decoded fields are now small structs, not
 * just scalars.
 */
function formatValue(value: unknown): string {
  if (value === null || value === undefined) return PLACEHOLDER;
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : PLACEHOLDER;
  if (typeof value === "string") return value.length === 0 ? PLACEHOLDER : value;
  if (Array.isArray(value)) {
    // e.g. alertDataSum -- a long raw array. Individual entry meanings aren't
    // confirmed, so summarize rather than dumping every value inline (the
    // full array is still available via the title tooltip).
    const nonZero = value.filter((v) => typeof v === "number" && v !== 0).length;
    return nonZero === 0
      ? `${value.length} values, all zero`
      : `${value.length} values, ${nonZero} non-zero`;
  }
  if (typeof value === "object") {
    try {
      return Object.entries(value as Record<string, unknown>)
        .map(([k, v]) => `${labelify(k)}: ${formatValue(v)}`)
        .join(" · ");
    } catch {
      return PLACEHOLDER;
    }
  }
  return String(value);
}

/** Full-fidelity tooltip text for a raw value -- lets an array's exact contents
 * still be inspected even though formatValue() only shows a summary. */
function titleForValue(value: unknown): string | undefined {
  if (Array.isArray(value)) {
    try {
      return JSON.stringify(value);
    } catch {
      return undefined;
    }
  }
  return undefined;
}

/**
 * Renders GET /api/latest/advanced generically: iterates whatever keys are
 * present rather than hardcoding a fixed field list, since the backend's
 * exact field set for this endpoint is still being finalized (see
 * api_contract.md). A nested `raw_undecoded` object, if present, is rendered
 * in a visually distinct section noting those field meanings are unconfirmed.
 */
interface AdvancedInfoPageProps {
  /** The main dashboard's `fetchedAt` -- triggers a refetch when a new snapshot lands. */
  refreshKey?: string | null;
}

export function AdvancedInfoPage({ refreshKey }: AdvancedInfoPageProps) {
  const { advanced, fetchedAt, isLoading, error } = useAdvancedInfo(refreshKey);

  if (isLoading) {
    return <p className="text-sm text-slate-500">Loading advanced info…</p>;
  }
  if (error) {
    return (
      <p role="alert" className="text-sm text-red-600">
        {error}
      </p>
    );
  }
  if (!advanced) {
    return (
      <p className="text-sm text-slate-500">No advanced info available yet — refresh to fetch data.</p>
    );
  }

  const { raw_undecoded, ...decoded } = advanced;
  const decodedEntries = Object.entries(decoded);
  const rawEntries =
    raw_undecoded && typeof raw_undecoded === "object" ? Object.entries(raw_undecoded) : [];

  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-500">As of {formatDateTime(fetchedAt)}</p>

      <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-900/5">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Advanced Info</p>
        {decodedEntries.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">No decoded fields available.</p>
        ) : (
          <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2">
            {decodedEntries.map(([key, value]) => (
              <div key={key} className="border-b border-slate-100 py-1.5 text-sm">
                <dt className="text-slate-500">{labelify(key)}</dt>
                <dd className="mt-0.5 break-words font-medium text-slate-800">
                  {formatValue(value)}
                </dd>
              </div>
            ))}
          </dl>
        )}
      </div>

      {rawEntries.length > 0 ? (
        <div className="rounded-2xl bg-amber-50 p-5 ring-1 ring-amber-200">
          <p className="text-xs font-medium uppercase tracking-wide text-amber-700">
            Raw / undecoded values
          </p>
          <p className="mt-1 text-xs text-amber-700">
            The field names below are translated to plain English where the field's{" "}
            <em>purpose</em> is known from SAIC/EV terminology — but what each <em>value</em>{" "}
            means is not confirmed by any source, so raw numbers are shown as-is, unconverted.
          </p>
          <dl className="mt-3 grid grid-cols-1 gap-x-6 gap-y-1 sm:grid-cols-2">
            {rawEntries.map(([key, value]) => (
              <div
                key={key}
                className="flex items-baseline justify-between gap-4 border-b border-amber-100 py-1.5 text-sm"
              >
                <dt className="text-amber-800">
                  {labelForRawField(key)}
                  <span className="ml-1.5 font-mono text-xs text-amber-600">({key})</span>
                </dt>
                <dd className="whitespace-nowrap font-mono text-amber-900" title={titleForValue(value)}>
                  {formatValue(value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}
    </div>
  );
}
