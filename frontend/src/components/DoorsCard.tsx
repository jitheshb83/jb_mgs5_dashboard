import type { CSSProperties } from "react";
import { formatBoolean } from "../lib/format";
import type { Doors } from "../lib/types";
import { COLORS } from "../lib/colors";
import { LockIcon, UnlockIcon } from "./icons";

interface DoorsCardProps {
  doors: Doors | null;
}

/** Fill/stroke for one region of the car diagram, per the reserved status-color convention. */
function regionStyle(state: boolean | null): { fill: string; stroke: string; dash?: string } {
  if (state === null) {
    // Unknown must never read as a false "closed" -- a distinct dashed,
    // near-white treatment instead of the solid neutral-gray "closed" fill.
    return { fill: COLORS.surface, stroke: COLORS.inkMuted, dash: "3 3" };
  }
  return state ? { fill: COLORS.warning, stroke: "none" } : { fill: COLORS.neutral, stroke: "none" };
}

interface RegionProps {
  x: number;
  y: number;
  width: number;
  height: number;
  rx?: number;
  state: boolean | null;
  label: string;
}

/** One state-colored rect in the car diagram, with a native hover tooltip via <title>. */
function Region({ x, y, width, height, rx = 8, state, label }: RegionProps) {
  const style = regionStyle(state);
  const stateWord = state === null ? "unknown" : state ? "open" : "closed";
  return (
    <rect
      x={x}
      y={y}
      width={width}
      height={height}
      rx={rx}
      fill={style.fill}
      stroke={style.stroke}
      strokeWidth={style.stroke === "none" ? 0 : 1.5}
      strokeDasharray={style.dash}
    >
      <title>{`${label}: ${stateWord}`}</title>
    </rect>
  );
}

function DoorItem({ label, isOpen }: { label: string; isOpen: boolean | null }) {
  return (
    <div className="rounded-lg bg-slate-50 py-2 text-center">
      <p className="text-sm font-semibold text-slate-800">
        {formatBoolean(isOpen, { yes: "Open", no: "Closed" })}
      </p>
      <p className="text-[11px] uppercase tracking-wide text-slate-400">{label}</p>
    </div>
  );
}

function LegendSwatch({ children, style }: { children: string; style: CSSProperties }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="inline-block h-3 w-3 rounded-sm" style={style} />
      {children}
    </span>
  );
}

/**
 * Doors & Locks card. The primary "image representation" is a top-down
 * schematic car diagram whose regions change fill color by state; a detail
 * caption grid (same field set as before) sits alongside it so the color
 * fill is never the only signal, per the "status color never carries
 * meaning alone" rule.
 *
 * Layout convention: driver = left side of the diagram, passenger = right
 * side. The API contract doesn't say which physical side the car's
 * steering wheel is on (driver_door_open vs. rear_left/rear_right_door_open
 * mix naming conventions), and every region is captioned by name regardless,
 * so this only affects which side of the silhouette lights up, not
 * correctness -- flagged as a judgment call in the implementation report.
 */
export function DoorsCard({ doors }: DoorsCardProps) {
  const locked = doors?.locked ?? null;
  const lockColor = locked === null ? COLORS.neutral : locked ? COLORS.good : COLORS.warning;
  const LockGlyph = locked === false ? UnlockIcon : LockIcon;

  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-900/5 sm:col-span-2 lg:col-span-3">
      <div className="flex items-center gap-2">
        <span style={{ color: lockColor }}>
          <LockGlyph size={22} />
        </span>
        <p className="text-2xl font-semibold text-slate-900">
          {formatBoolean(locked, { yes: "Locked", no: "Unlocked" })}
        </p>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-6 sm:grid-cols-[auto,1fr] sm:items-start">
        <svg
          viewBox="0 0 200 320"
          width={150}
          className="mx-auto flex-shrink-0 sm:mx-0"
          role="img"
          aria-label="Top-down diagram of the car showing door, window, bonnet, boot and sunroof status"
        >
          {/* Body outline (neutral, not state-colored) */}
          <rect x={48} y={8} width={104} height={304} rx={34} fill="#ffffff" stroke={COLORS.axis} strokeWidth={2} />

          <Region x={58} y={14} width={84} height={46} rx={12} state={doors?.bonnet_open ?? null} label="Bonnet" />
          <Region x={58} y={260} width={84} height={46} rx={12} state={doors?.boot_open ?? null} label="Boot" />

          <Region
            x={76}
            y={108}
            width={48}
            height={92}
            rx={14}
            state={doors?.sunroof_open ?? null}
            label="Sunroof"
          />

          <Region
            x={14}
            y={90}
            width={34}
            height={68}
            rx={10}
            state={doors?.driver_door_open ?? null}
            label="Driver door"
          />
          <Region
            x={152}
            y={90}
            width={34}
            height={68}
            rx={10}
            state={doors?.passenger_door_open ?? null}
            label="Passenger door"
          />
          <Region
            x={14}
            y={166}
            width={34}
            height={68}
            rx={10}
            state={doors?.rear_left_door_open ?? null}
            label="Rear left door"
          />
          <Region
            x={152}
            y={166}
            width={34}
            height={68}
            rx={10}
            state={doors?.rear_right_door_open ?? null}
            label="Rear right door"
          />

          <Region
            x={20}
            y={96}
            width={22}
            height={22}
            rx={4}
            state={doors?.driver_window_open ?? null}
            label="Driver window"
          />
          <Region
            x={158}
            y={96}
            width={22}
            height={22}
            rx={4}
            state={doors?.passenger_window_open ?? null}
            label="Passenger window"
          />
          <Region
            x={20}
            y={172}
            width={22}
            height={22}
            rx={4}
            state={doors?.rear_left_window_open ?? null}
            label="Rear left window"
          />
          <Region
            x={158}
            y={172}
            width={22}
            height={22}
            rx={4}
            state={doors?.rear_right_window_open ?? null}
            label="Rear right window"
          />
        </svg>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          <DoorItem label="Driver door" isOpen={doors?.driver_door_open ?? null} />
          <DoorItem label="Passenger door" isOpen={doors?.passenger_door_open ?? null} />
          <DoorItem label="Rear left door" isOpen={doors?.rear_left_door_open ?? null} />
          <DoorItem label="Rear right door" isOpen={doors?.rear_right_door_open ?? null} />
          <DoorItem label="Bonnet" isOpen={doors?.bonnet_open ?? null} />
          <DoorItem label="Boot" isOpen={doors?.boot_open ?? null} />
          <DoorItem label="Driver window" isOpen={doors?.driver_window_open ?? null} />
          <DoorItem label="Passenger window" isOpen={doors?.passenger_window_open ?? null} />
          <DoorItem label="Rear left window" isOpen={doors?.rear_left_window_open ?? null} />
          <DoorItem label="Rear right window" isOpen={doors?.rear_right_window_open ?? null} />
          <DoorItem label="Sunroof" isOpen={doors?.sunroof_open ?? null} />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-4 border-t border-slate-100 pt-3 text-xs text-slate-500">
        <LegendSwatch style={{ background: COLORS.neutral }}>Closed</LegendSwatch>
        <LegendSwatch style={{ background: COLORS.warning }}>Open</LegendSwatch>
        <LegendSwatch style={{ background: COLORS.surface, border: `1px dashed ${COLORS.inkMuted}` }}>
          Unknown
        </LegendSwatch>
      </div>
    </div>
  );
}
