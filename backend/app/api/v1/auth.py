from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_code,
    new_otp,
)
from app.db import get_db
from app.models import OtpCode, User
from app.models.types import utcnow
from app.schemas.people import OtpRequest, OtpVerify, UserOut
from app.services.notify import notifier

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookies(resp: Response, user_id: str) -> None:
    common = {"httponly": True, "samesite": "lax", "secure": settings.cookie_secure}
    resp.set_cookie("access_token", create_access_token(user_id),
                    max_age=settings.access_ttl_min * 60, **common)
    resp.set_cookie("refresh_token", create_refresh_token(user_id),
                    max_age=settings.refresh_ttl_days * 86400, path="/api/v1/auth", **common)


@router.post("/otp/request", status_code=202)
def otp_request(body: OtpRequest, db: Session = Depends(get_db)):
    email = body.email.lower()
    recent = db.scalar(
        select(OtpCode)
        .where(OtpCode.email == email, OtpCode.created_at > utcnow() - timedelta(seconds=30))
    )
    if recent is not None:
        raise HTTPException(429, "otp_too_frequent")
    code = new_otp()
    db.add(OtpCode(email=email, code_hash=hash_code(code),
                   expires_at=utcnow() + timedelta(minutes=settings.otp_ttl_min)))
    db.commit()
    notifier.send_email(email, "Your login code", f"Code: {code}")
    return {"status": "sent"}


@router.post("/otp/verify")
def otp_verify(body: OtpVerify, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower()
    otp = db.scalar(
        select(OtpCode)
        .where(OtpCode.email == email, OtpCode.used.is_(False))
        .order_by(OtpCode.created_at.desc())
    )
    if otp is None or otp.expires_at < utcnow() or otp.attempts >= settings.otp_max_attempts:
        raise HTTPException(400, "otp_invalid")
    if otp.code_hash != hash_code(body.code):
        otp.attempts += 1
        db.commit()
        raise HTTPException(400, "otp_invalid")
    otp.used = True
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email)
        db.add(user)
    db.commit()
    _set_cookies(response, str(user.id))
    return {"user": UserOut.model_validate(user)}


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    user_id = decode_token(token, "refresh") if token else None
    user = db.get(User, user_id) if user_id else None
    if user is None or not user.is_active:
        raise HTTPException(401, "invalid_refresh")
    _set_cookies(response, str(user.id))
    return {"status": "ok"}


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/api/v1/auth")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
