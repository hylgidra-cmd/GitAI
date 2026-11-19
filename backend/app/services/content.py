import hashlib
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import ContentStatus, Place, PlaceContent, Route, RoutePlace


def published_content(db: Session, place_id: UUID, lang: str) -> PlaceContent | None:
    return db.scalar(
        select(PlaceContent)
        .where(
            PlaceContent.place_id == place_id,
            PlaceContent.lang == lang,
            PlaceContent.status == ContentStatus.published,
        )
        .order_by(PlaceContent.version.desc())
    )


def build_bundle(db: Session, route: Route, lang: str) -> dict:
    """Offline manifest for a route in one language. Only published content is included."""
    rows = db.execute(
        select(Place, RoutePlace.position)
        .join(RoutePlace, RoutePlace.place_id == Place.id)
        .where(RoutePlace.route_id == route.id)
        .order_by(RoutePlace.position)
    ).all()
    files, places, versions = [], [], []
    for place, pos in rows:
        c = published_content(db, place.id, lang)
        if c is None:
            continue
        versions.append(f"{place.id}:{c.version}")
        places.append({"place_id": str(place.id), "position": pos, "version": c.version})
        if c.audio_url:
            files.append({"url": c.audio_url, "kind": "audio", "size_bytes": c.audio_size_bytes})
        if place.cover_image_url:
            files.append({"url": place.cover_image_url, "kind": "image", "size_bytes": 0})
    total = sum(f["size_bytes"] for f in files)
    version = hashlib.sha256("|".join(versions).encode()).hexdigest()[:12]
    return {
        "route_id": str(route.id),
        "lang": lang,
        "version": version,
        "places": places,
        "files": files,
        "total_bytes": total,
        "over_limit": total > settings.bundle_max_bytes,
    }
