/**
 * Shared visual tokens for charts and status indicators (SOC meter, doors
 * diagram, stat-card icons). Values are fixed by this project's validated
 * dataviz pass -- do not invent new colors or re-derive the palette; extend
 * this file rather than hardcoding hex values elsewhere.
 *
 * Light mode only (this app has no dark mode yet) but kept centralized so
 * adding one later doesn't mean hunting hardcoded hex codes across files.
 */

export const COLORS = {
  // Chart chrome
  surface: "#fcfcfb",
  ink: "#0b0b0b",
  inkSecondary: "#52514e",
  inkMuted: "#898781",
  axis: "#c3c2b7",
  gridline: "#e1e0d9",

  // Categorical (fixed order -- slot 1 before slot 2, never swapped)
  blue: "#2a78d6",
  blueLight: "#cde2fb",
  orange: "#eb6834",

  // Status (reserved -- never repurposed as a categorical/series color)
  good: "#0ca30c",
  warning: "#fab219",
  neutral: "#c3c2b7",
} as const;
