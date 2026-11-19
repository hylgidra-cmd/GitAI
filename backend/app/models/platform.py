import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.types import EmbeddingType, JSONType, UTCDateTime, utcnow


class Route(Base):
    __tablename__ = "routes"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clusters.id"), index=True)
    slug: Mapped[str] = mapped_column(String(96), unique=True)
    names: Mapped[dict] = mapped_column(JSONType, default=dict)
    length_km: Mapped[float] = mapped_column(Float, default=0)
    duration_min: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class RoutePlace(Base):
    __tablename__ = "route_places"
    __table_args__ = (UniqueConstraint("route_id", "position"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("routes.id"), index=True)
    place_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("places.id"))
    position: Mapped[int] = mapped_column(Integer)


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255), default="")
    year: Mapped[int | None] = mapped_column(Integer)
    license: Mapped[str] = mapped_column(String(128), default="")
    place_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("places.id"), index=True)
    lang: Mapped[str] = mapped_column(String(8))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)  # only verified sources feed AI
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_sources.id"), index=True)
    place_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("places.id"), index=True)
    lang: Mapped[str] = mapped_column(String(8))
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(EmbeddingType())


class AISession(Base):
    __tablename__ = "ai_sessions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    place_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("places.id"))
    lang: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class AIMessage(Base):
    __tablename__ = "ai_messages"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ai_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    text: Mapped[str] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSONType, default=list)
    grounded: Mapped[bool] = mapped_column(Boolean, default=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0)
    feedback: Mapped[str | None] = mapped_column(String(16))  # helpful | not_helpful
    error_report: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class AIUsage(Base):
    """Daily request counter per subject (user:<id> or device:<id>)."""

    __tablename__ = "ai_usage"
    __table_args__ = (UniqueConstraint("subject", "day"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    subject: Mapped[str] = mapped_column(String(80))
    day: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD (UTC)
    count: Mapped[int] = mapped_column(Integer, default=0)


class Event(Base):
    """Anonymous analytics event: no personal data, random device id only."""

    __tablename__ = "events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(48), index=True)
    device_id: Mapped[str] = mapped_column(String(64))
    props: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str] = mapped_column(String(48))
    entity_id: Mapped[str] = mapped_column(String(64))
    data: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONType, default=dict)


class OfflineBundle(Base):
    """Persisted offline bundle manifest per route and language."""

    __tablename__ = "offline_bundles"
    __table_args__ = (UniqueConstraint("route_id", "lang", "version"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    route_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("routes.id"), index=True)
    lang: Mapped[str] = mapped_column(String(8))
    version: Mapped[str] = mapped_column(String(24))
    total_bytes: Mapped[int] = mapped_column(Integer, default=0)
    manifest: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class AIMediaJob(Base):
    """Tourist photo/voice job with mandatory 24-hour expiration (NF-09, AC-11)."""

    __tablename__ = "ai_media_jobs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_sessions.id"), index=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # image | voice | video
    lang: Mapped[str] = mapped_column(String(8))
    storage_key: Mapped[str | None] = mapped_column(String(512))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    exif_stripped: Mapped[bool] = mapped_column(Boolean, default=True)
    ocr_text: Mapped[str] = mapped_column(Text, default="")
    answer_text: Mapped[str] = mapped_column(Text, default="")
    audio_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(24), default="completed")  # pending | completed | purged
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    purged_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

