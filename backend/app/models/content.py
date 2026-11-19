"""Core multi-tenant content model: Country -> Region -> Cluster -> Place -> PlaceContent."""
import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ContentStatus(str, enum.Enum):
    draft = "draft"
    in_review = "in_review"
    published = "published"


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Country(Base):
    __tablename__ = "countries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(2), unique=True)  # ISO 3166-1 alpha-2
    names: Mapped[dict] = mapped_column(JSONB, default=dict)  # {"uz": "...", "en": "..."}
    regions: Mapped[list["Region"]] = relationship(back_populates="country")


class Region(Base):
    __tablename__ = "regions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    country_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("countries.id"))
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    names: Mapped[dict] = mapped_column(JSONB, default=dict)
    country: Mapped[Country] = relationship(back_populates="regions")
    clusters: Mapped[list["Cluster"]] = relationship(back_populates="region")


class Cluster(Base):
    __tablename__ = "clusters"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regions.id"))
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    names: Mapped[dict] = mapped_column(JSONB, default=dict)
    region: Mapped[Region] = relationship(back_populates="clusters")
    places: Mapped[list["Place"]] = relationship(back_populates="cluster")


class Place(Base):
    __tablename__ = "places"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    cluster_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clusters.id"))
    slug: Mapped[str] = mapped_column(String(96), unique=True)
    kind: Mapped[str] = mapped_column(String(32))  # museum, fortress, monument, ...
    location = mapped_column(Geography("POINT", srid=4326))
    geofence_radius_m: Mapped[int] = mapped_column(Integer, default=50)  # 20-100
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cluster: Mapped[Cluster] = relationship(back_populates="places")
    contents: Mapped[list["PlaceContent"]] = relationship(back_populates="place")


class PlaceContent(Base):
    __tablename__ = "place_content"
    __table_args__ = (UniqueConstraint("place_id", "lang", "version"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    place_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("places.id"))
    lang: Mapped[str] = mapped_column(String(8))  # kaa, uz, ru, en, ...
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.draft)
    version: Mapped[int] = mapped_column(Integer, default=1)
    source_refs: Mapped[list] = mapped_column(JSONB, default=list)  # source + license (required)
    place: Mapped[Place] = relationship(back_populates="contents")
