from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_lang
from app.core.config import settings
from app.db import get_db
from app.models import (
    Cluster,
    ContentStatus,
    Event,
    Place,
    PlaceContent,
    QRCode,
    Route,
    RoutePlace,
)
from app.schemas.public import (
    ClusterOut,
    ContentOut,
    PlaceDetail,
    PlaceOut,
    RouteDetail,
    RouteOut,
)
from app.services.content import build_bundle, published_content
from app.services.locale_geo import haversine_m

router = APIRouter(tags=["catalog"])


def _content_fallback(db: Session, place_id: UUID, lang: str) -> PlaceContent | None:
    """Requested language first, then en, ru, uz."""
    for code in dict.fromkeys([lang, "en", "ru", "uz"]):
        c = published_content(db, place_id, code)
        if c is not None:
            return c
    return None


def _place_out(db: Session, p: Place, lang: str, lat=None, lng=None) -> PlaceOut:
    c = _content_fallback(db, p.id, lang)
    out = PlaceOut.model_validate(p)
    out.lang = c.lang if c else None
    out.title = c.title if c else None
    if lat is not None and lng is not None:
        out.distance_m = round(haversine_m(lat, lng, p.lat, p.lng), 1)
    return out


def _place_detail(db: Session, p: Place, lang: str) -> PlaceDetail:
    c = _content_fallback(db, p.id, lang)
    langs = db.scalars(
        select(PlaceContent.lang)
        .where(PlaceContent.place_id == p.id, PlaceContent.status == ContentStatus.published)
        .distinct()
    ).all()
    base = _place_out(db, p, lang)
    return PlaceDetail(
        **base.model_dump(),
        content=ContentOut.model_validate(c) if c else None,
        available_langs=sorted(langs),
    )


@router.get("/languages")
def languages() -> dict:
    return {"supported": settings.supported_langs, "default": settings.default_lang}


@router.get("/clusters", response_model=list[ClusterOut])
def clusters(db: Session = Depends(get_db)):
    return db.scalars(select(Cluster)).all()


@router.get("/places", response_model=list[PlaceOut])
def list_places(
    cluster: str | None = None,
    kind: str | None = None,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    radius_km: float | None = Query(default=None, gt=0, le=500),
    lang: str = Depends(get_lang),
    db: Session = Depends(get_db),
):
    stmt = select(Place).where(Place.is_active.is_(True))
    if cluster:
        stmt = stmt.join(Cluster, Cluster.id == Place.cluster_id).where(Cluster.slug == cluster)
    if kind:
        stmt = stmt.where(Place.kind == kind)
    out = [_place_out(db, p, lang, lat, lng) for p in db.scalars(stmt).all()]
    if lat is not None and lng is not None:
        if radius_km:
            out = [o for o in out if o.distance_m is not None and o.distance_m <= radius_km * 1000]
        out.sort(key=lambda o: o.distance_m or 0)
    return out


@router.get("/places/{place_id}", response_model=PlaceDetail)
def place_detail(place_id: UUID, lang: str = Depends(get_lang), db: Session = Depends(get_db)):
    p = db.get(Place, place_id)
    if p is None or not p.is_active:
        raise HTTPException(404, "place_not_found")
    return _place_detail(db, p, lang)


@router.get("/q/{code}", response_model=PlaceDetail)
def qr_open(
    code: str,
    device: str | None = Query(default=None, max_length=64),
    lang: str = Depends(get_lang),
    db: Session = Depends(get_db),
):
    qr = db.scalar(select(QRCode).where(QRCode.hash == code))
    if qr is None:
        raise HTTPException(404, "qr_not_found")
    p = db.get(Place, qr.place_id)
    if p is None or not p.is_active:
        raise HTTPException(404, "place_not_found")
    db.add(Event(name="qr_scan", device_id=device or "anon", props={"place_id": str(p.id)}))
    db.commit()
    return _place_detail(db, p, lang)


@router.get("/routes", response_model=list[RouteOut])
def list_routes(cluster: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Route).where(Route.is_active.is_(True))
    if cluster:
        stmt = stmt.join(Cluster, Cluster.id == Route.cluster_id).where(Cluster.slug == cluster)
    return db.scalars(stmt).all()


@router.get("/routes/{route_id}", response_model=RouteDetail)
def route_detail(route_id: UUID, db: Session = Depends(get_db)):
    r = db.get(Route, route_id)
    if r is None or not r.is_active:
        raise HTTPException(404, "route_not_found")
    ids = db.scalars(
        select(RoutePlace.place_id)
        .where(RoutePlace.route_id == r.id)
        .order_by(RoutePlace.position)
    ).all()
    return RouteDetail(**RouteOut.model_validate(r).model_dump(), place_ids=list(ids))


@router.get("/routes/{route_id}/bundle")
def route_bundle(route_id: UUID, lang: str = Depends(get_lang), db: Session = Depends(get_db)):
    r = db.get(Route, route_id)
    if r is None or not r.is_active:
        raise HTTPException(404, "route_not_found")
    return build_bundle(db, r, lang)
