/**
 * Hand-authored inline SVG line icons for stat-card headers and the doors
 * diagram. Deliberately not an icon library dependency -- see CLAUDE.md's
 * "no new deps without flagging why" rule; these are simple enough to author
 * directly and keep the bundle dependency-free.
 *
 * All icons share a common shape: 24x24 viewBox, stroke-only, currentColor
 * so callers control color via className/style, sized via the `size` prop.
 */

interface IconProps {
  className?: string;
  size?: number;
}

const commonProps = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function BatteryIcon({ className, size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} className={className} aria-hidden="true" {...commonProps}>
      <rect x="2" y="7" width="17" height="10" rx="2" />
      <path d="M21 10.5v3" />
      <path d="M6 10.5v3M9.5 10.5v3M13 10.5v3" />
    </svg>
  );
}

export function ThermometerIcon({ className, size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} className={className} aria-hidden="true" {...commonProps}>
      <path d="M12 14.5V4a2 2 0 1 0-4 0v10.5a4 4 0 1 0 4 0Z" />
      <path d="M12 9h-2" />
    </svg>
  );
}

export function TyreIcon({ className, size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} className={className} aria-hidden="true" {...commonProps}>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="3" />
      <path d="M12 4v3M12 17v3M4 12h3M17 12h3M6.3 6.3l2.1 2.1M15.6 15.6l2.1 2.1M17.7 6.3l-2.1 2.1M8.4 15.6l-2.1 2.1" />
    </svg>
  );
}

export function PlugIcon({ className, size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} className={className} aria-hidden="true" {...commonProps}>
      <path d="M9 3v4M15 3v4" />
      <path d="M7 7h10v4a5 5 0 0 1-10 0V7Z" />
      <path d="M12 16v5" />
    </svg>
  );
}

export function GaugeIcon({ className, size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} className={className} aria-hidden="true" {...commonProps}>
      <path d="M4 15a8 8 0 1 1 16 0" />
      <path d="M12 15l4-5" />
      <path d="M12 15h.01" />
    </svg>
  );
}

export function LockIcon({ className, size = 18 }: IconProps) {
  return (
    <svg width={size} height={size} className={className} aria-hidden="true" {...commonProps}>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

export function UnlockIcon({ className, size = 18 }: IconProps) {
  return (
    <svg width={size} height={size} className={className} aria-hidden="true" {...commonProps}>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 7.5-1.9" />
    </svg>
  );
}
