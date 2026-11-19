import hashlib
import hmac
import secrets
from datetime import timedelta
from uuid import UUID

import jwt

from app.core.config import settings
from app.models.types import utcnow


def create_token(sub: str, kind: str, ttl: timedelta) -> str:
    now = utcnow()
    payload = {"sub": sub, "kind": kind, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_access_token(user_id: str) -> str:
    return create_token(user_id, "access", timedelta(minutes=settings.access_ttl_min))


def create_refresh_token(user_id: str) -> str:
    return create_token(user_id, "refresh", timedelta(days=settings.refresh_ttl_days))


def decode_token(token: str, kind: str) -> UUID | None:
    """Return user id, or None if token is invalid, expired or of the wrong kind."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return UUID(payload["sub"]) if payload.get("kind") == kind else None
    except (jwt.PyJWTError, ValueError, KeyError):
        return None


def hash_code(code: str) -> str:
    return hmac.new(settings.jwt_secret.encode(), code.encode(), hashlib.sha256).hexdigest()


def new_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def new_qr_hash() -> str:
    return secrets.token_urlsafe(6)


def sign_resource(resource_id: str, ttl_seconds: int = 300) -> tuple[int, str]:
    """Return (expires_epoch, hmac_sig) for a private resource such as a guide document."""
    expires = int(utcnow().timestamp()) + ttl_seconds
    msg = f"{resource_id}:{expires}".encode()
    sig = hmac.new(settings.jwt_secret.encode(), msg, hashlib.sha256).hexdigest()
    return expires, sig


def verify_resource_signature(resource_id: str, expires: int, sig: str) -> bool:
    if expires < int(utcnow().timestamp()):
        return False
    msg = f"{resource_id}:{expires}".encode()
    expected = hmac.new(settings.jwt_secret.encode(), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)
