from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router

app = FastAPI(
    title="Audio Guide API",
    version="0.3.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
)


@app.get("/health", tags=["system"])
def root_health() -> dict:
    return {"status": "ok", "service": "Audio Guide API"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def problem_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """RFC 9457 problem+json response preserving `detail` for clients and tests."""
    try:
        title = HTTPStatus(exc.status_code).phrase
    except ValueError:
        title = "Error"
    return JSONResponse(
        status_code=exc.status_code,
        media_type="application/problem+json",
        content={
            "type": f"https://audioguide.uz/problems/{exc.status_code}",
            "title": title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url.path),
        },
    )


app.include_router(api_router)
