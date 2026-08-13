/**
 * Display formatting helpers. Per api_contract.md, the backend does not
 * convert units — the frontend owns display formatting, and any null field
 * must render as a placeholder, never the literal "null"/"undefined".
 */

export const PLACEHOLDER = "—";

/** Formats a nullable number with a fixed decimal count and optional unit suffix. */
export function formatNumber(
  value: number | null | undefined,
  options: { decimals?: number; unit?: string } = {},
): string {
  const { decimals = 1, unit = "" } = options;
  if (value === null || value === undefined || Number.isNaN(value)) {
    return PLACEHOLDER;
  }
  return `${value.toFixed(decimals)}${unit}`;
}

/** Formats a nullable boolean as a human label. */
export function formatBoolean(
  value: boolean | null | undefined,
  labels: { yes: string; no: string } = { yes: "Yes", no: "No" },
): string {
  if (value === null || value === undefined) return PLACEHOLDER;
  return value ? labels.yes : labels.no;
}

/** Formats a nullable string, capitalizing the first letter for display. */
export function formatString(value: string | null | undefined): string {
  if (value === null || value === undefined || value.length === 0) {
    return PLACEHOLDER;
  }
  return value.charAt(0).toUpperCase() + value.slice(1).replace(/_/g, " ");
}

/** Formats an ISO8601 timestamp as a local date/time string, or the placeholder if absent. */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return PLACEHOLDER;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return PLACEHOLDER;
  return date.toLocaleString();
}
