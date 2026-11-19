# Architecture decisions (ADR)

| # | Decision | Status |
|---|---|---|
| 1 | Backend: Python + FastAPI, SQLAlchemy 2, Alembic (TZ v2.0). Python >= 3.11 locally (TZ says 3.12) | Accepted (default) |
| 2 | Karakalpak (`kaa`) alphabet: Latin | Accepted (default), customer to confirm |
| 3 | Multi-tenant hierarchy from day 1: Country → Region → Cluster → Place | Accepted |
| 4 | MVP scope = TZ v2.0 (3 clusters, ~15 places, 4 languages, 12 weeks) | Accepted |
| 5 | Languages: `kaa`, `uz`, `ru`, `en`; new language = data, not code | Accepted |
| 6 | Karakalpak audio = human narrators; TTS only if week-1 spike passes (avg >= 4.0/5) | Accepted |
| 7 | No payments/escrow in MVP; booking requests only | Accepted |
| 8 | Postgres 16 + PostGIS + pgvector as single data store; Redis for queues; S3-compatible storage | Accepted |
| 9 | Personal data of UZ citizens hosted in Uzbekistan (legal confirmation pending) | Open |

## Expansion phases
MVP (Karakalpakstan) → v1.1 (tr/fr, deposit, Pass, B2B) → v1.5 (Samarkand, Bukhara, Khiva, Tashkent) → v2 (escrow, realtime voice) → v3 (other countries, white-label).
