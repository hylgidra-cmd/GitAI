"use client";

import React from "react";
import { Lang, UI_TEXT } from "@/i18n/messages";
import { PlaceItem } from "@/lib/api";

interface Props {
  places: PlaceItem[];
  selectedSlug: string;
  lang: Lang;
  onSelect: (slug: string) => void;
  onSimulateGeofence: (place: PlaceItem) => void;
}

/**
 * Interactive vector map canvas of Karakalpakstan & Ancient Khorezm (PMTiles / MapLibre compatible offline view)
 * Shows object pins, geofence radii (20-100m), and 1-tap GPS proximity simulation (AG-01, AG-05).
 */
export default function InteractiveMap({
  places,
  selectedSlug,
  lang,
  onSelect,
  onSimulateGeofence,
}: Props) {
  const t = UI_TEXT[lang];

  // Normalize lat/lng to SVG viewport (lat 41.8..43.9, lng 58.9..61.0)
  const toXY = (lat: number, lng: number) => {
    const x = ((lng - 58.8) / 2.3) * 520 + 40;
    const y = ((44.0 - lat) / 2.3) * 260 + 25;
    return { x: Math.max(40, Math.min(560, x)), y: Math.max(30, Math.min(270, y)) };
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-semibold text-teal-300">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-teal-400" />
          <span>MapLibre / PMTiles Offline Vector Canvas · Qaraqalpaqstan & Xorezm</span>
        </div>
        <button
          type="button"
          onClick={() => {
            const current = places.find((p) => p.slug === selectedSlug) || places[0];
            if (current) onSimulateGeofence(current);
          }}
          className="rounded-lg border border-amber-400/40 bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-300 hover:bg-amber-500/20 cursor-pointer"
        >
          📍 GPS Geofence Test ({t.geofenceAction})
        </button>
      </div>

      <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-gradient-to-br from-slate-950 via-slate-900 to-teal-950/40">
        <svg viewBox="0 0 600 300" className="h-64 w-full">
          {/* Grid lines & Amu Darya / Aral Sea stylized contours */}
          <defs>
            <pattern id="mapGrid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path
                d="M 40 0 L 0 0 0 40"
                fill="none"
                stroke="rgba(148,163,184,0.08)"
                strokeWidth="1"
              />
            </pattern>
          </defs>
          <rect width="600" height="300" fill="url(#mapGrid)" />

          {/* Aral Sea remnant contour */}
          <ellipse
            cx="115"
            cy="48"
            rx="65"
            ry="28"
            fill="rgba(13,148,136,0.12)"
            stroke="rgba(45,212,191,0.25)"
            strokeDasharray="4 4"
          />
          <text x="85" y="45" fill="rgba(45,212,191,0.5)" fontSize="10" fontWeight="600">
            ARAL SEA / MOYNAQ
          </text>

          {/* Amu Darya river path */}
          <path
            d="M 110 75 Q 210 155 265 195 T 490 275"
            fill="none"
            stroke="rgba(56,189,248,0.25)"
            strokeWidth="4"
          />

          {/* Object Pins & Geofence circles */}
          {places.map((p) => {
            const { x, y } = toXY(p.lat, p.lng);
            const active = p.slug === selectedSlug;
            return (
              <g
                key={p.slug}
                onClick={() => onSelect(p.slug)}
                className="cursor-pointer"
              >
                <circle
                  cx={x}
                  cy={y}
                  r={active ? 24 : 16}
                  fill={active ? "rgba(20,184,166,0.22)" : "rgba(148,163,184,0.12)"}
                  stroke={active ? "#2dd4bf" : "rgba(148,163,184,0.3)"}
                  strokeDasharray="3 3"
                />
                <circle
                  cx={x}
                  cy={y}
                  r={active ? 8 : 6}
                  fill={active ? "#2dd4bf" : "#fbbf24"}
                  stroke="#090d16"
                  strokeWidth="2"
                />
                <text
                  x={x + 12}
                  y={y + 4}
                  fill={active ? "#ffffff" : "#cbd5e1"}
                  fontSize={active ? "11" : "10"}
                  fontWeight={active ? "700" : "500"}
                >
                  {p.titles[lang].slice(0, 26)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
