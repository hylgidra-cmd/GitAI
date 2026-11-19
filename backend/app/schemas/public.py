from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ContentOut(ORM):
    lang: str
    title: str
    body: str
    audio_url: str | None
    audio_duration_s: int
    paragraph_timings: list
    version: int
    source_refs: list


class PlaceOut(ORM):
    id: UUID
    slug: str
    kind: str
    lat: float
    lng: float
    geofence_radius_m: int
    cover_image_url: str | None
    cluster_id: UUID
    lang: str | None = None
    title: str | None = None
    distance_m: float | None = None


class PlaceDetail(PlaceOut):
    content: ContentOut | None = None
    available_langs: list[str] = []


class ClusterOut(ORM):
    id: UUID
    slug: str
    names: dict
    region_id: UUID


class RouteOut(ORM):
    id: UUID
    slug: str
    names: dict
    length_km: float
    duration_min: int
    cluster_id: UUID


class RouteDetail(RouteOut):
    place_ids: list[UUID]


class EventIn(BaseModel):
    name: str
    props: dict = {}


class EventBatch(BaseModel):
    device_id: str
    events: list[EventIn]
