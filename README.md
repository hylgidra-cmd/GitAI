# Audio Guide (GitAI)

Multi-language PWA audio guide + AI guide for tourism. MVP: Karakalpakstan (3 clusters),
architecture is multi-tenant (Country → Region → Cluster → Place) for expansion to all of
Uzbekistan and beyond. Languages: `kaa` (Latin), `uz`, `ru`, `en`.

## Layout

| Path | Purpose |
|---|---|
| `docs/` | Decisions (ADR), data model, roadmap, TZ |
| `infra/` | Docker Compose (Postgres+PostGIS+pgvector, Redis, MinIO) |
| `backend/` | FastAPI modular monolith |
| `web/` | Next.js PWA (Phase 3) |

## Quick start (backend)

```powershell
docker compose -f infra/docker-compose.yml up -d
cd backend
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
pytest
```
