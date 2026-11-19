import math
import re

from app.core.config import settings


def resolve_lang(query_lang: str | None, accept_language: str | None) -> str:
    """?lang= wins, then Accept-Language (with q-weights), then default."""
    supported = settings.supported_langs
    if query_lang in supported:
        return query_lang
    if accept_language:
        items = []
        for part in accept_language.split(","):
            m = re.match(r"\s*([a-zA-Z-]+)\s*(?:;\s*q=([0-9.]+))?", part)
            if m:
                q = float(m.group(2)) if m.group(2) else 1.0
                items.append((q, m.group(1).lower().split("-")[0]))
        for _, code in sorted(items, key=lambda x: -x[0]):
            if code in supported:
                return code
            if code == "qq":  # ISO 639-1 style code for Karakalpak
                return "kaa"
    return settings.default_lang


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
