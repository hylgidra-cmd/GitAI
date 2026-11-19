"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { LANG_LABELS, Lang, UI_TEXT } from "@/i18n/messages";
import {
  AIResponse,
  GuideItem,
  PlaceItem,
  STATIC_GUIDES,
  STATIC_PLACES,
  STATIC_ROUTES,
  askAIGuide,
} from "@/lib/api";
import {
  SavedBundle,
  enqueueAnalyticsEvent,
  flushAnalyticsQueue,
  getFavorites,
  getHistory,
  getSavedBundles,
  saveBundleOffline,
  toggleFavorite,
} from "@/lib/offline";
import AudioPlayer from "@/components/AudioPlayer";
import InteractiveMap from "@/components/InteractiveMap";

type Tab = "explore" | "routes" | "ai" | "guides" | "admin";

export default function HomePage() {
  const [lang, setLang] = useState<Lang>("uz");
  const [tab, setTab] = useState<Tab>("explore");
  const [isOnline, setIsOnline] = useState(true);

  // Catalog state
  const [places, setPlaces] = useState<PlaceItem[]>(STATIC_PLACES);
  const [clusterFilter, setClusterFilter] = useState<string>("all");
  const [kindFilter, setKindFilter] = useState<string>("all");
  const [selectedSlug, setSelectedSlug] = useState<string>(STATIC_PLACES[0].slug);
  const [geofenceAlert, setGeofenceAlert] = useState<PlaceItem | null>(null);
  const [autoPlayTrigger, setAutoPlayTrigger] = useState(false);

  // Local favorites & history (AG-07)
  const [favorites, setFavorites] = useState<string[]>([]);
  const [history, setHistory] = useState<string[]>([]);

  // Offline bundles (OF-01..04)
  const [savedBundles, setSavedBundles] = useState<Record<string, SavedBundle>>({});
  const [downloadingRoute, setDownloadingRoute] = useState<string | null>(null);

  // AI state (AI-01..08)
  const [question, setQuestion] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiHistory, setAiHistory] = useState<
    Array<{ q: string; res: AIResponse; mode: "text" | "voice" | "photo"; feedback?: string }>
  >([]);
  const [aiEnabled, setAiEnabled] = useState(true);
  const [aiCostToday, setAiCostToday] = useState(0.18);

  // Guides state (GD-01..04)
  const [guides, setGuides] = useState<GuideItem[]>(STATIC_GUIDES);
  const [guideLangFilter, setGuideLangFilter] = useState<string>("all");
  const [only4x4, setOnly4x4] = useState(false);
  const [bookingGuide, setBookingGuide] = useState<GuideItem | null>(null);
  const [bookingSuccess, setBookingSuccess] = useState<string | null>(null);
  const [bookingDates, setBookingDates] = useState({
    from: "2026-11-25",
    to: "2026-11-27",
    group: 3,
    notes: "Moynaq & Ustyurt expedition",
  });

  // CMS state (CM-01..06, AD-01..04)
  const [cmsRole, setCmsRole] = useState<"content_manager" | "editor" | "admin">("editor");
  const [cmsMessage, setCmsMessage] = useState<string | null>(null);

  const t = UI_TEXT[lang];

  useEffect(() => {
    setFavorites(getFavorites());
    setHistory(getHistory());
    setSavedBundles(getSavedBundles());
    setIsOnline(typeof navigator !== "undefined" ? navigator.onLine : true);

    const onOnline = () => {
      setIsOnline(true);
      void flushAnalyticsQueue();
    };
    const onOffline = () => setIsOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  const filteredPlaces = places.filter((p) => {
    if (clusterFilter !== "all" && p.cluster_slug !== clusterFilter) return false;
    if (kindFilter !== "all" && p.kind !== kindFilter) return false;
    return true;
  });

  const selectedPlace =
    places.find((p) => p.slug === selectedSlug) || filteredPlaces[0] || places[0];

  async function handleAskAI(mode: "text" | "voice" | "photo", overrideQ?: string) {
    if (!aiEnabled) return;
    const qText = (overrideQ ?? question).trim();
    if (!qText) return;
    setAiLoading(true);
    enqueueAnalyticsEvent("ai_query", { mode, lang, place_id: selectedPlace.id });
    const res = await askAIGuide(qText, lang, selectedPlace.id);
    if (mode === "photo") {
      res.exif_stripped = true;
      res.ocr_text = qText;
      res.expires_at = new Date(Date.now() + 24 * 3600 * 1000).toISOString();
    }
    if (mode === "voice" && lang !== "kaa") {
      res.audio_url = `https://cdn.audioguide.uz/tts/${lang}/answer.opus`;
    }
    setAiHistory((prev) => [{ q: qText, res, mode }, ...prev]);
    setAiCostToday((c) => Number((c + 0.006).toFixed(3)));
    setQuestion("");
    setAiLoading(false);
  }

  function handleDownloadBundle(routeSlug: string, mb: number) {
    setDownloadingRoute(routeSlug);
    enqueueAnalyticsEvent("offline_download_start", { route: routeSlug, lang });
    setTimeout(() => {
      const updated = saveBundleOffline({
        routeSlug,
        lang,
        version: "v1-" + lang,
        totalBytes: Math.round(mb * 1024 * 1024),
        downloadedAt: new Date().toISOString(),
      });
      setSavedBundles({ ...updated });
      setDownloadingRoute(null);
      enqueueAnalyticsEvent("offline_download_finish", { route: routeSlug, lang });
    }, 650);
  }

  function handleTransitionContent(placeSlug: string, nextStatus: "draft" | "in_review" | "published") {
    if (nextStatus === "published" && cmsRole === "content_manager") {
      setCmsMessage("❌ CM-04: Content Manager cannot publish directly. Native Speaker Editor or Admin required.");
      return;
    }
    setPlaces((prev) =>
      prev.map((p) =>
        p.slug === placeSlug ? { ...p, status: nextStatus, version: p.version + 1 } : p
      )
    );
    setCmsMessage(`✅ ${placeSlug} → ${nextStatus.toUpperCase()} (role: ${cmsRole})`);
  }

  function handleGenerateTTSDraft(placeSlug: string) {
    if (lang === "kaa") {
      setCmsMessage(
        "⚠️ CM-03 / R1: Karakalpak (kaa) TTS draft is blocked by policy. Only verified human narrator recording (-16 LUFS) is allowed."
      );
      return;
    }
    setCmsMessage(
      `🎙 CM-03: TTS draft generated for ${placeSlug} [${lang.toUpperCase()}] and normalized to -16 LUFS (Opus 64 kbps).`
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top Header with 1-Tap 4-Language Switcher (AG-03, NF-10) */}
      <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500 text-slate-950 font-black text-lg shadow">
              AG
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-white sm:text-lg">{t.brand}</h1>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                    isOnline
                      ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                      : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
                  }`}
                >
                  {isOnline ? `● ${t.online}` : `⚡ ${t.offlineMode}`}
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">{t.subtitle}</p>
            </div>
          </div>

          {/* 1-Tap Language Switcher: kaa, uz, ru, en */}
          <div className="flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-900 p-1">
            {(["kaa", "uz", "ru", "en"] as Lang[]).map((code) => (
              <button
                key={code}
                type="button"
                onClick={() => setLang(code)}
                className={`rounded-lg px-2.5 py-1.5 text-xs font-bold transition cursor-pointer ${
                  lang === code
                    ? "bg-teal-500 text-slate-950 shadow"
                    : "text-slate-300 hover:bg-slate-800"
                }`}
              >
                {LANG_LABELS[code].short} ·{" "}
                <span className="font-normal">{LANG_LABELS[code].native}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="mx-auto flex max-w-7xl gap-2 overflow-x-auto px-4 pb-2.5">
          {(
            [
              ["explore", `🎧 ${t.tabExplore}`],
              ["routes", `📦 ${t.tabRoutes}`],
              ["ai", `🤖 ${t.tabAI}`],
              ["guides", `🧭 ${t.tabGuides}`],
              ["admin", `🛠 ${t.tabAdmin}`],
            ] as Array<[Tab, string]>
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={`whitespace-nowrap rounded-xl px-4 py-2 text-xs font-bold transition cursor-pointer ${
                tab === key
                  ? "bg-teal-500/20 text-teal-300 border border-teal-400/40"
                  : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      {/* GPS Geofence Prompt Banner (AG-05: prompt without autoplay) */}
      {geofenceAlert && (
        <div className="bg-amber-500/15 border-b border-amber-400/40 px-4 py-2.5">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 text-xs">
            <span className="font-medium text-amber-200">
              📍 <strong>{geofenceAlert.titles[lang]}</strong> — {t.geofenceHint}
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setSelectedSlug(geofenceAlert.slug);
                  setAutoPlayTrigger(true);
                  setGeofenceAlert(null);
                }}
                className="rounded-lg bg-amber-400 px-3 py-1 font-bold text-slate-950 hover:bg-amber-300 cursor-pointer"
              >
                ▶ {t.geofenceAction}
              </button>
              <button
                type="button"
                onClick={() => setGeofenceAlert(null)}
                className="rounded-lg border border-amber-400/30 px-2 py-1 text-amber-200 cursor-pointer"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        {/* TAB 1: PLACES, MAP & AUDIO GUIDE (AG-01..07) */}
        {tab === "explore" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            {/* Left column: Filters, Map, Object Cards */}
            <div className="space-y-5 lg:col-span-5">
              {/* Cluster & Type Filters (AG-01) */}
              <div className="flex flex-wrap gap-2">
                <select
                  value={clusterFilter}
                  onChange={(e) => setClusterFilter(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs font-semibold text-slate-200"
                >
                  <option value="all">{t.allClusters} (Nukus · Moynaq · Xorezm)</option>
                  <option value="nukus">Nukus & Mizdakhan</option>
                  <option value="aral">Moynaq & Aral Sea</option>
                  <option value="khorezm-fortresses">Ancient Khorezm Fortresses</option>
                </select>

                <select
                  value={kindFilter}
                  onChange={(e) => setKindFilter(e.target.value)}
                  className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-2 text-xs font-semibold text-slate-200"
                >
                  <option value="all">{t.allKinds}</option>
                  <option value="museum">{t.kindMuseum}</option>
                  <option value="fortress">{t.kindFortress}</option>
                  <option value="monument">{t.kindMonument}</option>
                </select>
              </div>

              {/* Interactive Map (MapLibre / PMTiles Offline Canvas) */}
              <InteractiveMap
                places={filteredPlaces}
                selectedSlug={selectedPlace.slug}
                lang={lang}
                onSelect={(slug) => {
                  setSelectedSlug(slug);
                  setAutoPlayTrigger(false);
                }}
                onSimulateGeofence={(place) => setGeofenceAlert(place)}
              />

              {/* Object Catalog List */}
              <div className="space-y-2.5">
                {filteredPlaces.map((p) => {
                  const isSel = p.slug === selectedPlace.slug;
                  const isFav = favorites.includes(p.slug);
                  return (
                    <div
                      key={p.slug}
                      onClick={() => {
                        setSelectedSlug(p.slug);
                        setAutoPlayTrigger(false);
                      }}
                      className={`cursor-pointer rounded-2xl border p-4 transition ${
                        isSel
                          ? "border-teal-400 bg-teal-500/10 shadow-lg"
                          : "border-slate-800 bg-slate-900/70 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-bold uppercase text-teal-300">
                              {p.cluster_slug}
                            </span>
                            <span className="text-[11px] text-slate-400">
                              Geofence: {p.geofence_radius_m}m
                            </span>
                          </div>
                          <h3 className="mt-1 text-sm font-bold text-white">
                            {p.titles[lang]}
                          </h3>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setFavorites(toggleFavorite(p.slug));
                            }}
                            className="rounded-lg border border-slate-700 px-2 py-1 text-xs hover:border-amber-400 cursor-pointer"
                            title={t.favorite}
                          >
                            {isFav ? "★" : "☆"}
                          </button>
                          <Link
                            href={`/q/${p.qr_hash}?lang=${lang}`}
                            onClick={(e) => e.stopPropagation()}
                            className="rounded-lg border border-teal-500/40 bg-teal-500/10 px-2.5 py-1 text-[11px] font-bold text-teal-300 hover:bg-teal-500/20"
                          >
                            QR /q/{p.qr_hash}
                          </Link>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right column: Selected Object Audio Guide, Synchronized Transcript & Quick AI */}
            <div className="space-y-5 lg:col-span-7">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="rounded-full bg-teal-500/15 px-3 py-1 text-xs font-bold text-teal-300 border border-teal-500/30">
                      {t.qrInstantBadge} · /q/{selectedPlace.qr_hash}
                    </span>
                    <h2 className="mt-2 text-xl font-extrabold text-white sm:text-2xl">
                      {selectedPlace.titles[lang]}
                    </h2>
                  </div>
                  <Link
                    href={`/q/${selectedPlace.qr_hash}?lang=${lang}`}
                    className="rounded-xl bg-slate-800 px-3 py-2 text-xs font-semibold text-teal-300 hover:bg-slate-700"
                  >
                    🔗 QR Standalone View →
                  </Link>
                </div>

                {/* Audio Player with Synchronized Paragraph Highlighting */}
                <div className="mt-5">
                  <AudioPlayer
                    place={selectedPlace}
                    lang={lang}
                    autoStart={autoPlayTrigger}
                  />
                </div>

                {/* Local Favorites & History Bar (AG-07) */}
                <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
                  <div>
                    ★ {t.favorite}:{" "}
                    {favorites.length ? favorites.join(", ") : "—"}
                  </div>
                  <div>
                    🕒 {t.history}:{" "}
                    {history.length ? history.slice(0, 3).join(", ") : "—"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: ROUTES & OFFLINE BUNDLES (AG-06, OF-01..05) */}
        {tab === "routes" && (
          <div className="space-y-6">
            <div className="rounded-2xl border border-teal-500/30 bg-slate-900/80 p-5">
              <h2 className="text-lg font-bold text-white">{t.tabRoutes}</h2>
              <p className="mt-1 text-xs text-slate-300">{t.bundleSizeLimit}</p>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
              {STATIC_ROUTES.map((r) => {
                const key = `${r.slug}:${lang}`;
                const saved = savedBundles[key];
                const isDownloading = downloadingRoute === r.slug;
                return (
                  <div
                    key={r.slug}
                    className="flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/80 p-5"
                  >
                    <div>
                      <span className="rounded bg-teal-500/15 px-2.5 py-1 text-xs font-bold text-teal-300">
                        {r.cluster_slug.toUpperCase()}
                      </span>
                      <h3 className="mt-3 text-base font-bold text-white">
                        {r.names[lang]}
                      </h3>
                      <div className="mt-2 flex gap-4 text-xs text-slate-400">
                        <span>📏 {r.length_km} km</span>
                        <span>⏱ {Math.round(r.duration_min / 60)} h</span>
                        <span>📦 {r.bundle_mb} MB (≤150 MB)</span>
                      </div>

                      <div className="mt-4 space-y-1.5">
                        {r.place_slugs.map((slug, idx) => {
                          const pl = places.find((p) => p.slug === slug);
                          return (
                            <div
                              key={slug}
                              onClick={() => {
                                setSelectedSlug(slug);
                                setTab("explore");
                              }}
                              className="cursor-pointer rounded-lg bg-slate-800/70 px-3 py-2 text-xs text-slate-200 hover:bg-slate-800"
                            >
                              {idx + 1}. {pl ? pl.titles[lang] : slug}
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="mt-5 pt-4 border-t border-slate-800">
                      {saved ? (
                        <div className="rounded-xl bg-emerald-500/15 border border-emerald-500/30 p-3 text-xs font-semibold text-emerald-300">
                          ✓ {t.bundleDownloaded} ({r.bundle_mb} MB · {saved.version})
                        </div>
                      ) : (
                        <button
                          type="button"
                          disabled={isDownloading}
                          onClick={() => handleDownloadBundle(r.slug, r.bundle_mb)}
                          className="w-full rounded-xl bg-teal-500 px-4 py-2.5 text-xs font-bold text-slate-950 hover:bg-teal-400 disabled:opacity-50 cursor-pointer"
                        >
                          {isDownloading
                            ? "⏳ Downloading Opus + WebP + PMTiles..."
                            : `⬇ ${t.downloadBundle} (${r.bundle_mb} MB)`}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 3: GROUNDED AI GUIDE (AI-01..08) */}
        {tab === "ai" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <div className="space-y-4 lg:col-span-5">
              <div className="rounded-2xl border border-teal-500/30 bg-slate-900/90 p-5">
                <h2 className="text-lg font-bold text-white">{t.aiTitle}</h2>
                <p className="mt-1 text-xs text-slate-300">{t.aiSub}</p>

                {!isOnline && (
                  <div className="mt-3 rounded-xl border border-amber-400/40 bg-amber-500/10 p-3 text-xs text-amber-200">
                    ⚡ {t.aiOfflineNotice}
                  </div>
                )}

                {!aiEnabled && (
                  <div className="mt-3 rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-xs text-rose-200">
                    🛑 AI Kill Switch is active (AD-04). Audio Guide & Guides catalog continue to operate normally (NF-07).
                  </div>
                )}

                <div className="mt-4 space-y-3">
                  <textarea
                    rows={3}
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder={t.aiPlaceholder}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-sm text-white placeholder-slate-500 focus:border-teal-400 focus:outline-none"
                  />

                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={aiLoading || !aiEnabled}
                      onClick={() => handleAskAI("text")}
                      className="rounded-xl bg-teal-500 px-4 py-2.5 text-xs font-bold text-slate-950 hover:bg-teal-400 disabled:opacity-50 cursor-pointer"
                    >
                      💬 {t.aiAsk}
                    </button>

                    <button
                      type="button"
                      disabled={aiLoading || !aiEnabled || lang === "kaa"}
                      onClick={() =>
                        handleAskAI(
                          "voice",
                          question || "Savitsky Museum founded 1966 avant-garde collection"
                        )
                      }
                      title={
                        lang === "kaa"
                          ? "Voice STT/TTS disabled for kaa until week-1 spike >= 4.0 (R1, AC-06)"
                          : "Push-to-talk Voice STT -> RAG -> Audio"
                      }
                      className="rounded-xl border border-teal-400/40 bg-teal-500/10 px-3.5 py-2.5 text-xs font-bold text-teal-300 hover:bg-teal-500/20 disabled:opacity-40 cursor-pointer"
                    >
                      🎙 {t.aiVoiceBtn} {lang === "kaa" ? "(Text only for KAA)" : ""}
                    </button>

                    <button
                      type="button"
                      disabled={aiLoading || !aiEnabled}
                      onClick={() =>
                        handleAskAI(
                          "photo",
                          question || "Mizdakhan Mazlumkhan Sulu underground mausoleum inscription"
                        )
                      }
                      className="rounded-xl border border-amber-400/40 bg-amber-500/10 px-3.5 py-2.5 text-xs font-bold text-amber-300 hover:bg-amber-500/20 disabled:opacity-40 cursor-pointer"
                    >
                      📷 {t.aiPhotoBtn}
                    </button>
                  </div>
                </div>

                {/* Preset Grounded vs Out-of-base test questions */}
                <div className="mt-5 border-t border-slate-800 pt-4">
                  <div className="text-[11px] font-semibold uppercase text-slate-400">
                    Test Prompts (Grounded RAG vs Honest Refusal AI-06):
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() =>
                        handleAskAI("text", "Savitsky Museum 1966 Igor Savitsky Nukus")
                      }
                      className="rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs text-teal-300 hover:bg-slate-700 cursor-pointer"
                    >
                      ✓ Savitsky Museum (1966)
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        handleAskAI("text", "Moynaq Aral Sea Amu Darya 1960 ship graveyard")
                      }
                      className="rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs text-teal-300 hover:bg-slate-700 cursor-pointer"
                    >
                      ✓ Why did the Aral Sea shrink?
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        handleAskAI("text", "What is the capital of Australia?")
                      }
                      className="rounded-lg bg-slate-800 px-2.5 py-1.5 text-xs text-amber-300 hover:bg-slate-700 cursor-pointer"
                    >
                      ✗ Out-of-base question (Must refuse)
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Responses with Citations, EXIF/24h TTL notice, and Feedback (AI-01, AI-06, AI-08) */}
            <div className="space-y-4 lg:col-span-7">
              {aiHistory.length === 0 ? (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8 text-center text-sm text-slate-400">
                  {t.aiSub}
                </div>
              ) : (
                aiHistory.map((item, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <span className="font-bold text-teal-300">
                        [{item.mode.toUpperCase()}] Q: {item.q}
                      </span>
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] text-slate-300">
                        🏷 {t.aiBadge}
                      </span>
                    </div>

                    <p className="text-sm leading-relaxed text-slate-100">
                      {item.res.answer}
                    </p>

                    {item.res.exif_stripped && (
                      <div className="rounded-lg bg-amber-500/10 border border-amber-500/30 px-3 py-1.5 text-[11px] text-amber-200">
                        🔒 NF-09 / AC-11: EXIF & GPS stripped · Auto-deletes in 24h (
                        {item.res.expires_at})
                      </div>
                    )}

                    {/* Citations */}
                    {item.res.citations.length > 0 ? (
                      <div className="rounded-xl bg-slate-950/80 p-3 text-xs text-slate-300">
                        <div className="font-bold text-emerald-300">
                          ✓ Grounded Citation (Groundedness ≥ 95%):
                        </div>
                        {item.res.citations.map((c, i) => (
                          <div key={i} className="mt-1 text-slate-400">
                            • {c.source_title} (chunk: {c.chunk_id.slice(0, 8)}, score: {c.score})
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="rounded-xl bg-amber-500/10 border border-amber-400/30 p-3 text-xs text-amber-200">
                        ⚠ AI-06 Safe Refusal: No verified fragment found in knowledge base.
                      </div>
                    )}

                    {/* Feedback Buttons (AI-08) */}
                    <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            const copy = [...aiHistory];
                            copy[idx].feedback = "helpful";
                            setAiHistory(copy);
                          }}
                          className={`rounded-lg px-2.5 py-1 border cursor-pointer ${
                            item.feedback === "helpful"
                              ? "border-emerald-400 bg-emerald-500/20 text-emerald-200"
                              : "border-slate-700 text-slate-300"
                          }`}
                        >
                          👍 {t.aiHelpful}
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            const copy = [...aiHistory];
                            copy[idx].feedback = "not_helpful";
                            setAiHistory(copy);
                          }}
                          className={`rounded-lg px-2.5 py-1 border cursor-pointer ${
                            item.feedback === "not_helpful"
                              ? "border-rose-400 bg-rose-500/20 text-rose-200"
                              : "border-slate-700 text-slate-300"
                          }`}
                        >
                          👎 {t.aiNotHelpful}
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            const copy = [...aiHistory];
                            copy[idx].feedback = "reported";
                            setAiHistory(copy);
                          }}
                          className="rounded-lg border border-slate-700 px-2.5 py-1 text-slate-400 hover:text-amber-300 cursor-pointer"
                        >
                          ⚑ {t.aiReportError}
                        </button>
                      </div>
                      <span className="text-slate-500">
                        Limit left today: {item.res.remaining_today}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 4: VERIFIED LOCAL GUIDES & REQUESTS (GD-01..04) */}
        {tab === "guides" && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
              <div>
                <h2 className="text-lg font-bold text-white">{t.guidesTitle}</h2>
                <p className="mt-1 text-xs text-slate-300">{t.guidesSub}</p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <select
                  value={guideLangFilter}
                  onChange={(e) => setGuideLangFilter(e.target.value)}
                  className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs font-semibold text-slate-200"
                >
                  <option value="all">All Languages (kaa / uz / ru / en)</option>
                  <option value="kaa">Qaraqalpaqsha (kaa)</option>
                  <option value="uz">O‘zbekcha (uz)</option>
                  <option value="ru">Русский (ru)</option>
                  <option value="en">English (en)</option>
                </select>
                <label className="flex items-center gap-2 text-xs font-semibold text-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={only4x4}
                    onChange={(e) => setOnly4x4(e.target.checked)}
                    className="accent-teal-400"
                  />
                  🚙 {t.filter4x4}
                </label>
              </div>
            </div>

            {bookingSuccess && (
              <div className="rounded-2xl border border-emerald-500/40 bg-emerald-500/15 p-4 text-sm font-semibold text-emerald-200">
                ✅ {bookingSuccess} · {t.timer24h}
              </div>
            )}

            <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
              {guides
                .filter((g) => g.status === "approved")
                .filter((g) =>
                  guideLangFilter === "all"
                    ? true
                    : g.languages.includes(guideLangFilter as Lang)
                )
                .filter((g) => (only4x4 ? g.has_4x4 : true))
                .map((g) => (
                  <div
                    key={g.id}
                    className="flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-900/90 p-5"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-bold text-emerald-300">
                          ✓ Verified Guide · ★ {g.rating}
                        </span>
                        {g.has_4x4 && (
                          <span className="rounded bg-amber-500/15 px-2 py-0.5 text-[11px] font-bold text-amber-300">
                            🚙 4×4 Off-Road
                          </span>
                        )}
                      </div>
                      <h3 className="mt-3 text-base font-bold text-white">
                        {g.display_name}
                      </h3>
                      <p className="mt-1 text-xs text-slate-300">{g.bio}</p>

                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {g.languages.map((l) => (
                          <span
                            key={l}
                            className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-semibold uppercase text-teal-300"
                          >
                            {l}
                          </span>
                        ))}
                        {g.specialties.map((s) => (
                          <span
                            key={s}
                            className="rounded bg-slate-800/60 px-2 py-0.5 text-[11px] text-slate-400"
                          >
                            #{s}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="mt-5 flex items-center justify-between border-t border-slate-800 pt-4">
                      <div className="text-sm font-bold text-white">
                        from ${g.price_from_usd}{" "}
                        <span className="text-xs font-normal text-slate-400">/ day</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setBookingGuide(g)}
                        className="rounded-xl bg-teal-500 px-4 py-2 text-xs font-bold text-slate-950 hover:bg-teal-400 cursor-pointer"
                      >
                        {t.bookGuide}
                      </button>
                    </div>
                  </div>
                ))}
            </div>

            {/* Booking Request Modal (GD-04) */}
            {bookingGuide && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
                <div className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-white">
                      {t.bookGuide}: {bookingGuide.display_name}
                    </h3>
                    <button
                      type="button"
                      onClick={() => setBookingGuide(null)}
                      className="text-slate-400 hover:text-white cursor-pointer"
                    >
                      ✕
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <label className="text-slate-400">Date from</label>
                      <input
                        type="date"
                        value={bookingDates.from}
                        onChange={(e) =>
                          setBookingDates({ ...bookingDates, from: e.target.value })
                        }
                        className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white"
                      />
                    </div>
                    <div>
                      <label className="text-slate-400">Date to</label>
                      <input
                        type="date"
                        value={bookingDates.to}
                        onChange={(e) =>
                          setBookingDates({ ...bookingDates, to: e.target.value })
                        }
                        className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white"
                      />
                    </div>
                  </div>
                  <div className="text-xs">
                    <label className="text-slate-400">Group size</label>
                    <input
                      type="number"
                      min={1}
                      max={40}
                      value={bookingDates.group}
                      onChange={(e) =>
                        setBookingDates({ ...bookingDates, group: Number(e.target.value) })
                      }
                      className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white"
                    />
                  </div>
                  <div className="text-xs">
                    <label className="text-slate-400">Route & Wishes</label>
                    <textarea
                      rows={2}
                      value={bookingDates.notes}
                      onChange={(e) =>
                        setBookingDates({ ...bookingDates, notes: e.target.value })
                      }
                      className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-white"
                    />
                  </div>
                  <p className="text-[11px] text-amber-300">{t.timer24h}</p>
                  <button
                    type="button"
                    onClick={() => {
                      enqueueAnalyticsEvent("request_sent", { guide_id: bookingGuide.id });
                      setBookingSuccess(
                        `${t.requestSent} (${bookingGuide.display_name}, ${bookingDates.from} → ${bookingDates.to})`
                      );
                      setBookingGuide(null);
                    }}
                    className="w-full rounded-xl bg-teal-500 py-2.5 text-xs font-bold text-slate-950 hover:bg-teal-400 cursor-pointer"
                  >
                    📨 Confirm & Notify Guide (Telegram + Email)
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: CMS & ADMIN DASHBOARD (CM-01..06, AD-01..04) */}
        {tab === "admin" && (
          <div className="space-y-6">
            {/* Admin Metrics & Emergency AI Kill Switch (AD-03, AD-04, AC-12) */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                <div className="text-xs text-slate-400">Published Audio Tracks (AC-02)</div>
                <div className="mt-1 text-2xl font-black text-teal-400">
                  {places.length * 4} / {places.length * 4}
                </div>
                <div className="text-[11px] text-slate-500">kaa · uz · ru · en</div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                <div className="text-xs text-slate-400">AI Groundedness (AC-04)</div>
                <div className="mt-1 text-2xl font-black text-emerald-400">97.4%</div>
                <div className="text-[11px] text-slate-500">Target ≥ 95% · Hallucinations ≤ 2%</div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
                <div className="text-xs text-slate-400">AI Cost Today (AD-03)</div>
                <div className="mt-1 text-2xl font-black text-amber-300">${aiCostToday}</div>
                <div className="text-[11px] text-slate-500">Daily budget cap: $10.00</div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4 flex flex-col justify-between">
                <div className="text-xs text-slate-400">AI Emergency Kill Switch (AD-04)</div>
                <button
                  type="button"
                  onClick={() => setAiEnabled((v) => !v)}
                  className={`mt-2 rounded-xl px-3 py-2 text-xs font-bold cursor-pointer ${
                    aiEnabled
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                      : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                  }`}
                >
                  {aiEnabled ? "🛑 Disable AI Subsystem" : "▶ Re-enable AI Subsystem"}
                </button>
              </div>
            </div>

            {/* CMS Role Simulator & Dual-Verification Workflow (CM-01..05, AD-01) */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-base font-bold text-white">{t.cmsTitle}</h2>
                  <p className="text-xs text-slate-400">
                    CM-04 Two-step review: Author (draft → in_review) → Native Speaker Editor (in_review → published)
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400">Active RBAC Role (AD-01):</span>
                  {(["content_manager", "editor", "admin"] as const).map((r) => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setCmsRole(r)}
                      className={`rounded-lg px-2.5 py-1 font-bold cursor-pointer ${
                        cmsRole === r
                          ? "bg-teal-500 text-slate-950"
                          : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>

              {cmsMessage && (
                <div className="rounded-xl border border-teal-500/40 bg-teal-500/10 p-3 text-xs font-semibold text-teal-200">
                  {cmsMessage}
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-800 text-slate-400">
                    <tr>
                      <th className="py-2 pr-3">Place</th>
                      <th className="py-2 pr-3">Lang ({lang.toUpperCase()}) Title</th>
                      <th className="py-2 pr-3">Status & Ver</th>
                      <th className="py-2 pr-3">Audio Pipeline (CM-02 / CM-03)</th>
                      <th className="py-2">Workflow Actions (CM-04 / CM-05)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/70">
                    {places.map((p) => (
                      <tr key={p.slug}>
                        <td className="py-3 pr-3 font-mono text-teal-300">{p.slug}</td>
                        <td className="py-3 pr-3 font-semibold text-white">
                          {p.titles[lang]}
                        </td>
                        <td className="py-3 pr-3">
                          <span className="rounded bg-slate-800 px-2 py-0.5 font-bold uppercase text-emerald-300">
                            {p.status} · v{p.version}
                          </span>
                        </td>
                        <td className="py-3 pr-3 space-x-1.5">
                          <button
                            type="button"
                            onClick={() =>
                              setCmsMessage(
                                `🎙 CM-02: Narrator audio attached for ${p.slug} (${lang.toUpperCase()}), loudness normalized to -16.0 LUFS, encoded to Opus.`
                              )
                            }
                            className="rounded bg-slate-800 px-2 py-1 text-slate-200 hover:bg-slate-700 cursor-pointer"
                          >
                            Upload Narrator (-16 LUFS)
                          </button>
                          <button
                            type="button"
                            onClick={() => handleGenerateTTSDraft(p.slug)}
                            className="rounded bg-slate-800 px-2 py-1 text-teal-300 hover:bg-slate-700 cursor-pointer"
                          >
                            TTS Draft
                          </button>
                        </td>
                        <td className="py-3 space-x-1.5">
                          <button
                            type="button"
                            onClick={() => handleTransitionContent(p.slug, "in_review")}
                            className="rounded bg-amber-500/20 px-2 py-1 text-amber-300 cursor-pointer"
                          >
                            → In Review
                          </button>
                          <button
                            type="button"
                            onClick={() => handleTransitionContent(p.slug, "published")}
                            className="rounded bg-emerald-500/20 px-2 py-1 text-emerald-300 cursor-pointer"
                          >
                            → Publish
                          </button>
                          <button
                            type="button"
                            onClick={() =>
                              setCmsMessage(
                                `🖨 CM-05: A4 QR Stand layout generated for ${p.slug} (/q/${p.qr_hash}) with 4-language headlines.`
                              )
                            }
                            className="rounded bg-slate-800 px-2 py-1 text-slate-300 cursor-pointer"
                          >
                            QR Stand A4
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
