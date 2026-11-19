from fastapi import Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db import get_db
from app.models import Role, User
from app.services.locale_geo import resolve_lang


def get_lang(
    request: Request, lang: str | None = Query(default=None, max_length=8)
) -> str:
    return resolve_lang(lang, request.headers.get("accept-language"))


def _token_from(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:]
    return request.cookies.get("access_token")


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = _token_from(request)
    user_id = decode_token(token, "access") if token else None
    if not user_id:
        return None
    user = db.get(User, user_id)
    return user if user and user.is_active else None


def current_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(401, "not_authenticated")
    return user


def require_roles(*roles: Role):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "forbidden")
        return user

    return dep


def device_id(x_device_id: str | None = Header(default=None, max_length=64)) -> str:
    if not x_device_id:
        raise HTTPException(400, "x_device_id_required")
    return x_device_id
