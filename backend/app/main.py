from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(title="Audio Guide API", version="0.1.0", openapi_url="/api/v1/openapi.json")


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "langs": settings.supported_langs}
