from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import GuideStatus, RequestStatus, Role
from app.schemas.public import ORM


class OtpRequest(BaseModel):
    email: EmailStr


class OtpVerify(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class UserOut(ORM):
    id: UUID
    email: str
    name: str | None
    role: Role
    preferred_lang: str


class GuideIn(BaseModel):
    display_name: str = Field(min_length=2, max_length=128)
    bio: str = ""
    languages: list[str] = Field(min_length=1)
    specialties: list[str] = []
    has_4x4: bool = False
    price_from_usd: float = Field(ge=0, default=0)
    photo_url: str | None = None


class GuideOut(ORM):
    id: UUID
    display_name: str
    bio: str
    languages: list
    specialties: list
    has_4x4: bool
    price_from_usd: float
    photo_url: str | None
    rating: float
    status: GuideStatus


class DocumentIn(BaseModel):
    kind: str = Field(pattern="^(guide_license|id_card|photo)$")
    storage_key: str


class RequestIn(BaseModel):
    date_from: date
    date_to: date
    group_size: int = Field(ge=1, le=60, default=1)
    route_id: UUID | None = None
    message: str = ""


class RequestOut(ORM):
    id: UUID
    guide_id: UUID
    tourist_id: UUID
    date_from: date
    date_to: date
    group_size: int
    message: str
    status: RequestStatus
    respond_by: datetime


class RequestDecision(BaseModel):
    status: RequestStatus
