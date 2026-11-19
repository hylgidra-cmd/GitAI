"use client";

const DEVICE_KEY = "audioguide_device_id";
const FAV_KEY = "audioguide_favorites";
const HIST_KEY = "audioguide_history";
const BUNDLES_KEY = "audioguide_offline_bundles";
const QUEUE_KEY = "audioguide_event_queue";

export function getDeviceId(): string {
  if (typeof window === "undefined") return "ssr-device";
  let id = localStorage.getItem(DEVICE_KEY);
  if (!id) {
    id = "dev-" + Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
    localStorage.setItem(DEVICE_KEY, id);
  }
  return id;
}

export function getFavorites(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(FAV_KEY) || "[]");
  } catch {
    return [];
  }
}

export function toggleFavorite(slug: string): string[] {
  const cur = getFavorites();
  const next = cur.includes(slug) ? cur.filter((s) => s !== slug) : [...cur, slug];
  localStorage.setItem(FAV_KEY, JSON.stringify(next));
  return next;
}

export function getHistory(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(HIST_KEY) || "[]");
  } catch {
    return [];
  }
}

export function recordHistory(slug: string): string[] {
  const cur = getHistory().filter((s) => s !== slug);
  const next = [slug, ...cur].slice(0, 20);
  if (typeof window !== "undefined") {
    localStorage.setItem(HIST_KEY, JSON.stringify(next));
  }
  return next;
}

export interface SavedBundle {
  routeSlug: string;
  lang: string;
  version: string;
  totalBytes: number;
  downloadedAt: string;
}

export function getSavedBundles(): Record<string, SavedBundle> {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(localStorage.getItem(BUNDLES_KEY) || "{}");
  } catch {
    return {};
  }
}

export function saveBundleOffline(bundle: SavedBundle): Record<string, SavedBundle> {
  const all = getSavedBundles();
  all[`${bundle.routeSlug}:${bundle.lang}`] = bundle;
  if (typeof window !== "undefined") {
    localStorage.setItem(BUNDLES_KEY, JSON.stringify(all));
  }
  return all;
}

export interface QueuedEvent {
  name: string;
  props: Record<string, unknown>;
}

export function enqueueAnalyticsEvent(
  name: string,
  props: Record<string, unknown> = {},
  apiBase = "http://localhost:8000/api/v1"
): void {
  if (typeof window === "undefined") return;
  const queue: QueuedEvent[] = JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]");
  queue.push({ name, props });
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue.slice(-90)));
  if (navigator.onLine) {
    void flushAnalyticsQueue(apiBase);
  }
}

export async function flushAnalyticsQueue(
  apiBase = "http://localhost:8000/api/v1"
): Promise<number> {
  if (typeof window === "undefined" || !navigator.onLine) return 0;
  const raw = localStorage.getItem(QUEUE_KEY);
  if (!raw) return 0;
  const events: QueuedEvent[] = JSON.parse(raw);
  if (!events.length) return 0;
  try {
    const res = await fetch(`${apiBase}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: getDeviceId(), events }),
    });
    if (res.ok) {
      localStorage.removeItem(QUEUE_KEY);
      return events.length;
    }
  } catch {
    // stay queued until network returns (OF-05)
  }
  return 0;
}
