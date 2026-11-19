import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.types import JSONType, UTCDateTime, utcnow


class Role(str, enum.Enum):
    tourist = "tourist"
    guide = "guide"
    content_manager = "content_manager"
    editor = "editor"
    admin = "admin"


class GuideStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str | None] = mapped_column(String(128))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.tourist)
    preferred_lang: Mapped[str] = mapped_column(String(8), default="en")
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class OtpCode(Base):
    __tablename__ = "otp_codes"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), index=True)
    code_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class GuideProfile(Base):
    __tablename__ = "guide_profiles"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    display_name: Mapped[str] = mapped_column(String(128))
    bio: Mapped[str] = mapped_column(Text, default="")
    languages: Mapped[list] = mapped_column(JSONType, default=list)  # ["uz","en"]
    specialties: Mapped[list] = mapped_column(JSONType, default=list)
    has_4x4: Mapped[bool] = mapped_column(Boolean, default=False)
    price_from_usd: Mapped[float] = mapped_column(Float, default=0)
    photo_url: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[GuideStatus] = mapped_column(Enum(GuideStatus), default=GuideStatus.pending)
    rating: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class GuideDocument(Base):
    """Metadata only; the file lives in private storage, served via signed URLs."""

    __tablename__ = "guide_documents"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    guide_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guide_profiles.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # guide_license, id_card, photo
    storage_key: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class BookingRequest(Base):
    __tablename__ = "booking_requests"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    guide_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("guide_profiles.id"), index=True)
    tourist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    route_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("routes.id"))
    date_from: Mapped[date] = mapped_column(Date)
    date_to: Mapped[date] = mapped_column(Date)
    group_size: Mapped[int] = mapped_column(Integer, default=1)
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.pending)
    respond_by: Mapped[datetime] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
