from fastapi import APIRouter

from app.api.v1 import admin, ai, auth, catalog, events, guides
from app.core.config import settings

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "langs": settings.supported_langs}


for r in (catalog.router, auth.router, guides.router, ai.router, events.router, admin.router):
    api_router.include_router(r)
