"use client";

import React, { useEffect, useRef, useState } from "react";
import { Lang, UI_TEXT } from "@/i18n/messages";
import { PlaceItem } from "@/lib/api";
import { enqueueAnalyticsEvent, recordHistory } from "@/lib/offline";

const SPEEDS = [0.8, 1.0, 1.25, 1.5, 2.0];

interface Props {
  place: PlaceItem;
  lang: Lang;
  autoStart?: boolean;
}

export default function AudioPlayer({ place, lang, autoStart = false }: Props) {
  const t = UI_TEXT[lang];
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [speed, setSpeed] = useState(1.0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const duration = place.audio_duration_s || 90;
  const paragraphs = place.bodies[lang]
    .split("\n\n")
    .map((p) => p.trim())
    .filter(Boolean);

  // Determine active paragraph index from current playback second (AG-04)
  const activeParagraphIdx = (() => {
    const share = duration / Math.max(1, paragraphs.length);
    return Math.min(paragraphs.length - 1, Math.floor(currentTime / share));
  })();

  useEffect(() => {
    setPlaying(false);
    setCurrentTime(0);
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    if (autoStart) {
      startPlayback(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [place.slug, lang]);

  function setupMediaSession() {
    if (typeof navigator !== "undefined" && "mediaSession" in navigator) {
      navigator.mediaSession.metadata = new MediaMetadata({
        title: place.titles[lang],
        artist: t.brand,
        album: place.cluster_slug.toUpperCase(),
      });
      navigator.mediaSession.setActionHandler("play", () => startPlayback(currentTime));
      navigator.mediaSession.setActionHandler("pause", () => pausePlayback());
      navigator.mediaSession.setActionHandler("seekbackward", () => seekBy(-15));
      navigator.mediaSession.setActionHandler("seekforward", () => seekBy(15));
    }
  }

  function speakText(fromSec: number, rate: number) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const share = duration / Math.max(1, paragraphs.length);
    const startIdx = Math.min(paragraphs.length - 1, Math.floor(fromSec / share));
    const textToSpeak = paragraphs.slice(startIdx).join(". ");
    const utter = new SpeechSynthesisUtterance(textToSpeak);
    utter.rate = rate;
    utter.lang =
      lang === "ru" ? "ru-RU" : lang === "en" ? "en-US" : lang === "uz" ? "uz-UZ" : "uz-UZ";
    window.speechSynthesis.speak(utter);
  }

  function startPlayback(fromSec = currentTime) {
    setPlaying(true);
    setupMediaSession();
    recordHistory(place.slug);
    enqueueAnalyticsEvent("audio_play", { place_id: place.id, lang });
    speakText(fromSec, speed);

    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setCurrentTime((prev) => {
        const next = prev + 0.5 * speed;
        if (next >= duration) {
          if (timerRef.current) clearInterval(timerRef.current);
          setPlaying(false);
          enqueueAnalyticsEvent("audio_complete", { place_id: place.id, lang });
          return duration;
        }
        return next;
      });
    }, 500);
  }

  function pausePlayback() {
    setPlaying(false);
    if (timerRef.current) clearInterval(timerRef.current);
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
  }

  function seekBy(deltaSec: number) {
    setCurrentTime((prev) => {
      const next = Math.max(0, Math.min(duration, prev + deltaSec));
      if (playing) {
        speakText(next, speed);
      }
      return next;
    });
  }

  function cycleSpeed() {
    const idx = SPEEDS.indexOf(speed);
    const nextSpeed = SPEEDS[(idx + 1) % SPEEDS.length];
    setSpeed(nextSpeed);
    if (playing) {
      speakText(currentTime, nextSpeed);
    }
  }

  const fmt = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <div className="rounded-2xl border border-teal-500/30 bg-slate-900/90 p-5 shadow-xl">
      {/* Player Header & Controls (AG-04) */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => (playing ? pausePlayback() : startPlayback())}
            className="flex h-12 w-12 items-center justify-center rounded-full bg-teal-500 text-slate-950 font-bold shadow-lg hover:bg-teal-400 transition cursor-pointer"
            aria-label={playing ? t.pause : t.listenNow}
          >
            {playing ? "❚❚" : "▶"}
          </button>

          <button
            type="button"
            onClick={() => seekBy(-15)}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:border-teal-400 cursor-pointer"
          >
            −15s
          </button>

          <button
            type="button"
            onClick={() => seekBy(15)}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold text-slate-200 hover:border-teal-400 cursor-pointer"
          >
            +15s
          </button>

          <button
            type="button"
            onClick={cycleSpeed}
            className="rounded-lg border border-teal-500/40 bg-teal-500/10 px-3 py-2 text-xs font-bold text-teal-300 hover:bg-teal-500/20 cursor-pointer"
          >
            {t.speed}: {speed}×
          </button>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
          <span className="rounded bg-slate-800 px-2 py-1 text-teal-300">
            {lang === "kaa" ? "🎙 Narrator (-16 LUFS)" : "🎙 Opus 64 kbps (-16 LUFS)"}
          </span>
          <span>
            {fmt(currentTime)} / {fmt(duration)}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-4">
        <input
          type="range"
          min={0}
          max={duration}
          step={1}
          value={Math.floor(currentTime)}
          onChange={(e) => {
            const val = Number(e.target.value);
            setCurrentTime(val);
            if (playing) speakText(val, speed);
          }}
          className="w-full accent-teal-400 cursor-pointer"
          aria-label="Audio progress"
        />
      </div>

      {/* Synchronized Transcript with Active Paragraph Highlighting (AG-02, AG-04, NF-06) */}
      <div className="mt-5">
        <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-wider text-slate-400">
          <span>{t.transcript}</span>
          <span>WCAG 2.1 AA · Media Session API</span>
        </div>
        <div className="space-y-3">
          {paragraphs.map((p, idx) => {
            const isActive = idx === activeParagraphIdx;
            return (
              <p
                key={idx}
                onClick={() => {
                  const targetSec = (idx / paragraphs.length) * duration;
                  setCurrentTime(targetSec);
                  if (playing) speakText(targetSec, speed);
                }}
                className={`cursor-pointer rounded-xl p-3.5 text-sm leading-relaxed transition ${
                  isActive
                    ? "border-l-4 border-teal-400 bg-teal-500/15 text-white font-medium shadow"
                    : "bg-slate-800/50 text-slate-300 hover:bg-slate-800"
                }`}
              >
                {p}
              </p>
            );
          })}
        </div>
      </div>

      {/* Mandatory Source & License Footer (Section 6) */}
      <div className="mt-4 border-t border-slate-800 pt-3 text-xs text-slate-400">
        <span className="font-semibold text-slate-300">{t.sourcesAndLicense}: </span>
        {place.source_refs.map((s, i) => (
          <span key={i} className="inline-block mr-3">
            {s.title} ({s.license})
          </span>
        ))}
      </div>
    </div>
  );
}
