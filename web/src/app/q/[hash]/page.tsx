"use client";

import React, { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { LANG_LABELS, Lang, UI_TEXT } from "@/i18n/messages";
import { STATIC_PLACES } from "@/lib/api";
import { enqueueAnalyticsEvent } from "@/lib/offline";
import AudioPlayer from "@/components/AudioPlayer";

/**
 * AG-03 & US-01: Instant QR code page (/q/{hash})
 * Opens in 1 tap without app install or registration, auto-detects browser language,
 * allows 1-tap language switching (kaa, uz, ru, en), and immediately plays audio.
 */
export default function QRPlacePage() {
  const params = useParams<{ hash: string }>();
  const searchParams = useSearchParams();
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => {
    const qLang = searchParams.get("lang") as Lang | null;
    if (qLang && ["kaa", "uz", "ru", "en"].includes(qLang)) {
      setLang(qLang);
      return;
    }
    if (typeof navigator !== "undefined") {
      const nav = navigator.language.toLowerCase();
      if (nav.startsWith("uz")) setLang("uz");
      else if (nav.startsWith("ru")) setLang("ru");
      else if (nav.startsWith("kaa") || nav.startsWith("qq")) setLang("kaa");
      else setLang("en");
    }
  }, [searchParams]);

  const place =
    STATIC_PLACES.find((p) => p.qr_hash === params.hash || p.slug === params.hash) ||
    STATIC_PLACES[0];

  useEffect(() => {
    enqueueAnalyticsEvent("qr_scan", { place_id: place.id, qr_hash: params.hash });
  }, [place.id, params.hash]);

  const t = UI_TEXT[lang];

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100">
      <div className="mx-auto max-w-3xl space-y-5">
        {/* Top bar: Back to catalog + 1-tap language switch */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link
            href="/"
            className="rounded-xl border border-slate-800 bg-slate-900 px-3.5 py-2 text-xs font-bold text-teal-300 hover:bg-slate-800"
          >
            ← {t.brand}
          </Link>

          <div className="flex items-center gap-1 rounded-xl border border-slate-800 bg-slate-900 p-1">
            {(["kaa", "uz", "ru", "en"] as Lang[]).map((code) => (
              <button
                key={code}
                type="button"
                onClick={() => setLang(code)}
                className={`rounded-lg px-2.5 py-1 text-xs font-bold transition cursor-pointer ${
                  lang === code
                    ? "bg-teal-500 text-slate-950"
                    : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                {LANG_LABELS[code].short}
              </button>
            ))}
          </div>
        </div>

        {/* Place Header */}
        <div className="rounded-2xl border border-teal-500/30 bg-slate-900/90 p-5">
          <span className="rounded-full bg-teal-500/15 px-3 py-1 text-xs font-bold text-teal-300">
            ⚡ {t.qrInstantBadge} · /q/{place.qr_hash}
          </span>
          <h1 className="mt-3 text-2xl font-black text-white">{place.titles[lang]}</h1>
          <p className="mt-1 text-xs text-slate-400">
            Cluster: {place.cluster_slug.toUpperCase()} · Geofence: {place.geofence_radius_m}m
          </p>
        </div>

        {/* Audio Player with Synchronized Transcript */}
        <AudioPlayer place={place} lang={lang} />
      </div>
    </div>
  );
}
