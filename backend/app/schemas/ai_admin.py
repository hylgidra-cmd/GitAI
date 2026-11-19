from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import ContentStatus, GuideStatus


class ChatIn(BaseModel):
    question: str = Field(min_length=2, max_length=1000)
    place_id: UUID | None = None
    lang: str | None = None


class CitationOut(BaseModel):
    chunk_id: str
    source_id: str
    source_title: str
    score: float


class ChatOut(BaseModel):
    message_id: UUID
    answer: str
    grounded: bool
    citations: list[CitationOut]
    lang: str
    remaining_today: int | None = None


class VoiceIn(BaseModel):
    audio_base64: str = Field(default="", max_length=2_000_000)
    transcript_hint: str = Field(default="", max_length=1000)
    place_id: UUID | None = None
    lang: str | None = None


class VoiceOut(BaseModel):
    message_id: UUID
    transcript: str
    answer: str
    audio_url: str | None = None
    grounded: bool
    citations: list[CitationOut]
    lang: str
    remaining_today: int | None = None


class ImageIn(BaseModel):
    image_base64: str = Field(default="")
    ocr_hint: str = Field(default="", max_length=1000)
    place_id: UUID | None = None
    lang: str | None = None


class ImageOut(BaseModel):
    job_id: UUID
    message_id: UUID
    ocr_text: str
    answer: str
    audio_url: str | None = None
    grounded: bool
    citations: list[CitationOut]
    exif_stripped: bool
    expires_at: datetime
    lang: str
    remaining_today: int | None = None


class FeedbackIn(BaseModel):
    feedback: str | None = Field(default=None, pattern="^(helpful|not_helpful)$")
    error_report: str | None = Field(default=None, max_length=2000)


class PlaceIn(BaseModel):
    cluster_id: UUID
    slug: str
    kind: str
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    geofence_radius_m: int = Field(ge=20, le=100, default=50)
    cover_image_url: str | None = None


class ContentIn(BaseModel):
    lang: str
    title: str
    body: str
    audio_url: str | None = None
    audio_size_bytes: int = 0
    audio_duration_s: int = 0
    paragraph_timings: list = []
    source_refs: list = []


class AudioUploadIn(BaseModel):
    audio_url: str
    size_bytes: int = Field(ge=0, default=120_000)
    duration_s: int = Field(ge=1, default=150)
    source: str = "Narrator recording"
    license: str = "Work-for-hire"


class TransitionIn(BaseModel):
    target: ContentStatus


class SourceIn(BaseModel):
    title: str
    author: str = ""
    year: int | None = None
    license: str = ""
    place_id: UUID | None = None
    lang: str
    text: str = Field(min_length=10)


class GuideModeration(BaseModel):
    status: GuideStatus


class SettingIn(BaseModel):
    value: bool | int | float | str | list[str]
