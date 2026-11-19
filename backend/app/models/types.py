"""Portable column types: work on PostgreSQL (JSONB, optional pgvector) and SQLite (tests)."""
import os
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

JSONType = JSON().with_variant(JSONB(), "postgresql")

EMBEDDING_DIM = 384


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Always timezone-aware UTC (SQLite drops tzinfo)."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value


class EmbeddingType(TypeDecorator):
    """Uses pgvector `vector(N)` when USE_PGVECTOR=1, otherwise JSONB on PostgreSQL and JSON on SQLite."""

    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = EMBEDDING_DIM):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            if os.getenv("USE_PGVECTOR", "").lower() in ("1", "true", "yes"):
                return dialect.type_descriptor(Vector(self.dim))
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
