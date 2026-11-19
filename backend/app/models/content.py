"""Core multi-tenant content model: Country -> Region -> Cluster -> Place -> PlaceContent."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.types import JSONType, UTCDateTime, utcnow


class ContentStatus(str, enum.Enum):
    draft = "draft"
    in_review = "in_review"
    published = "published"


class Country(Base):
    __tablename__ = "countries"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(2), unique=True)  # ISO 3166-1 alpha-2
    names: Mapped[dict] = mapped_column(JSONType, default=dict)  # {"uz": "...", "en": "..."}
    regions: Mapped[list["Region"]] = relationship(back_populates="country")


class Region(Base):
    __tablename__ = "regions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    country_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("countries.id"))
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    names: Mapped[dict] = mapped_column(JSONType, default=dict)
    country: Mapped[Country] = relationship(back_populates="regions")
    clusters: Mapped[list["Cluster"]] = relationship(back_populates="region")


class Cluster(Base):
    __tablename__ = "clusters"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regions.id"))
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    names: Mapped[dict] = mapped_column(JSONType, default=dict)
    region: Mapped[Region] = relationship(back_populates="clusters")
    places: Mapped[list["Place"]] = relationship(back_populates="cluster")


class Place(Base):
    __tablename__ = "places"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clusters.id"), index=True)
    slug: Mapped[str] = mapped_column(String(96), unique=True)
    kind: Mapped[str] = mapped_column(String(32))  # museum, fortress, monument, ...
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    geofence_radius_m: Mapped[int] = mapped_column(Integer, default=50)  # 20-100
    cover_image_url: Mapped[str | None] = mapped_column(String(512))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    cluster: Mapped[Cluster] = relationship(back_populates="places")
    contents: Mapped[list["PlaceContent"]] = relationship(back_populates="place")
    qr_codes: Mapped[list["QRCode"]] = relationship(back_populates="place")


class PlaceContent(Base):
    __tablename__ = "place_content"
    __table_args__ = (UniqueConstraint("place_id", "lang", "version"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    place_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("places.id"), index=True)
    lang: Mapped[str] = mapped_column(String(8))  # kaa, uz, ru, en, ...
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    audio_url: Mapped[str | None] = mapped_column(String(512))
    audio_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    audio_duration_s: Mapped[int] = mapped_column(Integer, default=0)
    paragraph_timings: Mapped[list] = mapped_column(JSONType, default=list)  # [{start_s, end_s}]
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.draft)
    version: Mapped[int] = mapped_column(Integer, default=1)
    # [{"title":..., "author":..., "license":...}] - license is mandatory to publish
    source_refs: Mapped[list] = mapped_column(JSONType, default=list)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    place: Mapped[Place] = relationship(back_populates="contents")


class QRCode(Base):
    __tablename__ = "qr_codes"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    place_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("places.id"), index=True)
    hash: Mapped[str] = mapped_column(String(16), unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    place: Mapped[Place] = relationship(back_populates="qr_codes")


class Asset(Base):
    """Media asset (audio track, WebP photo, stand PDF) with mandatory source & license metadata."""

    __tablename__ = "assets"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    place_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("places.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # audio, image, stand_pdf
    lang: Mapped[str | None] = mapped_column(String(8))
    url: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[str] = mapped_column(String(64), default="audio/ogg")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    duration_s: Mapped[int] = mapped_column(Integer, default=0)
    loudness_lufs: Mapped[float] = mapped_column(Float, default=-16.0)
    source: Mapped[str] = mapped_column(String(255), default="")
    license: Mapped[str] = mapped_column(String(128), default="")
    is_tts: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

