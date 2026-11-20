# Audio Guide — Karakalpakstan & Uzbekistan (GitAI)

[![Backend Tests](https://img.shields.io/badge/pytest-58%20passed-brightgreen)](#)
[![Next.js Build](https://img.shields.io/badge/next.js-15.1.6%20build%20passing-blue)](#)
[![Languages](https://img.shields.io/badge/languages-kaa%20%7C%20uz%20%7C%20ru%20%7C%20en-orange)](#)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fhylgidra-cmd%2FGitAI&root-directory=web)

> 🌐 **Live Production Vercel PWA:** [https://gitai-web-git-main-hylgidra-7217s-projects.vercel.app](https://gitai-web-git-main-hylgidra-7217s-projects.vercel.app)  
> 🎧 **1-Tap QR Playback (Savitsky Museum - Karakalpak):** [https://gitai-web-git-main-hylgidra-7217s-projects.vercel.app/q/savitsky01?lang=kaa](https://gitai-web-git-main-hylgidra-7217s-projects.vercel.app/q/savitsky01?lang=kaa)

A production-grade, multi-tenant Audio Guide and Grounded AI Tourist Companion Progressive Web Application (PWA) built according to **Technical Specification (TZ v2.0)**.

Designed for single-tap physical QR playback at cultural sites, interactive map exploration, offline bundle playback in remote desert zones, grounded AI concierge Q&A with strict anti-hallucination guardrails, and verified local tour guides discovery.

---

## 🏛️ Project Architecture & Scope

- **Multi-Tenant Hierarchy:** `Country` → `Region` → `Cluster` → `Place` → `PlaceContent`
  - Scalable from Karakalpakstan pilot clusters to all of Uzbekistan (Samarkand, Bukhara, Khiva, Tashkent) and international destinations.
- **Pilot Coverage (3 Clusters):**
  1. **Nukus Cluster:** I.V. Savitsky State Museum of Arts, Mizdakhan Necropolis.
  2. **Moynaq / Aral Cluster:** Ship Graveyard, Aral Sea History Museum.
  3. **Ancient Khorezm Fortress Cluster:** Ayaz-kala, Toprak-kala, Chilpyk Tower of Silence.
- **Supported Languages:**
  - `kaa` — Karakalpak (Latin script, human narrator audio only as per R1 restriction)
  - `uz` — Uzbek (Latin script)
  - `ru` — Russian
  - `en` — English

---

## 🚀 Key Modules & Capabilities

### 1. 1-Tap QR & Audio Player (`web/src/components/AudioPlayer.tsx`, `/q/{hash}`)
- Instant web player loading in `< 1.5s` upon QR scan.
- Audio playback with `±15s` skip controls, `0.8x – 2.0x` variable playback speed.
- Paragraph-synchronized transcript highlighting.
- Native mobile lock-screen & background control via Media Session API.

### 2. Offline Mode & PWA Bundles (`web/src/lib/offline.ts`, `backend/app/services/content.py`)
- PWA Service Worker caching app shell and manifest.
- Zip/JSON offline route bundles capped at `≤ 150 MB` (Opus 64 kbps, WebP) for remote desert zones with zero cellular signal (Chilpyk, Toprak-kala, Sudochye).
- Local fallback data storage for offline catalog navigation.

### 3. Grounded RAG AI Guide (`backend/app/services/rag.py`, `backend/app/api/v1/ai.py`)
- Hybrid lexical + vector search over verified cultural knowledge chunks.
- Anti-hallucination guardrail ($\ge 95\%$ groundedness) with post-retrieval numerical fact verification.
- Multilingual honest refusal ("Bilmeymen / Bilmayman / Не знаю / I don't know") when queried out of base.
- Image OCR + Vision with immediate EXIF stripping and automated 24-hour media purge.
- Anonymous (10 req/day) and registered (30 req/day) device budget limits + emergency kill switch.

### 4. Verified Guides Catalog (`backend/app/api/v1/guides.py`)
- Profile filtering by language, cluster, specialization, and car availability.
- Document verification (license badge, HMAC-signed private document URLs).
- Booking inquiry routing with real-time Telegram notification outbox.

### 5. CMS & Two-step Editorial Workflow (`backend/app/services/workflow.py`)
- Strict publication state machine: `draft` → `in_review` → `published`.
- Published contents are immutable; revisions clone into new draft versions.
- Audio loudness normalization enforcement (`-16 LUFS ± 1`).
- Audit logging of all administrative actions.

---

## 📂 Repository Structure

```text
GitAI/
├── backend/
│   ├── alembic/                # Database migrations (initial schema applied)
│   ├── app/
│   │   ├── api/v1/             # FastAPI routers: catalog, auth, guides, ai, events, admin
│   │   ├── core/               # Settings, JWT auth, HMAC URL signatures, security
│   │   ├── models/             # SQLAlchemy ORM models (multi-tenant, content, platform, user)
│   │   ├── schemas/            # Pydantic v2 validation models
│   │   └── services/           # RAG, AI adapters, locale/geo, workflow, offline bundles
│   ├── scripts/                # Database seed script (seed.py: 3 clusters, 7 places, 4 langs)
│   ├── tests/                  # 58 pytest unit & integration tests (100% passing)
│   └── pyproject.toml
├── web/                        # Next.js 15 (App Router) + React 19 + Tailwind CSS v4 PWA
│   ├── public/                 # PWA manifest, service worker (sw.js), icons
│   ├── src/
│   │   ├── app/                # Main PWA page (catalog, map, AI, guides, CMS) & /q/[hash]
│   │   ├── components/         # AudioPlayer, InteractiveMap
│   │   ├── i18n/               # Complete translations dictionary (kaa, uz, ru, en)
│   │   └── lib/                # API client with offline fallback, bundle storage
│   └── package.json
├── infra/
│   ├── docker-compose.yml      # PostgreSQL 16 + PostGIS + pgvector (5433:5432), Redis 7
│   └── init.sql
└── docs/                       # Architecture decisions, data model, TZ v2.0
```

---

## 🛠️ Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+ & npm

---

### Step 1: Start Infrastructure (PostgreSQL + Redis)

```powershell
docker compose -f infra/docker-compose.yml up -d
```
*Note: PostgreSQL is exposed on port `5433` (to avoid conflicts with existing standard PostgreSQL installations).*

---

### Step 2: Backend Setup & Testing

```powershell
cd backend

# Create virtual environment & activate
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Seed initial 4-language Karakalpakstan data
python -m scripts.seed

# Run test suite (58 tests)
pytest

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

### Step 3: Frontend PWA Setup

```powershell
cd web

# Install npm dependencies
npm install

# Run linter & production build
npm run lint
npm run build

# Start development server
npm run dev
```
- Web Application: `http://localhost:3000`
- 1-Tap QR Instant Playback Example: `http://localhost:3000/q/savitsky01?lang=kaa`

---

## 🧪 Verification & Test Results

- **Backend Pytest:** `58 passed in 4.14s`
  - Catalog language negotiation & geo-haversine: `12 tests`
  - OTP authentication & cookies: `6 tests`
  - Verified guides & Telegram notifications: `9 tests`
  - Grounded RAG, AI budget caps, kill switch, image OCR & EXIF purge: `15 tests`
  - CMS two-step editorial workflow, audit logs & LUFS: `10 tests`
  - Privacy-preserving event analytics: `3 tests`
  - Health endpoint: `1 test`
- **Ruff Code Style:** Clean (`All checks passed!`).
- **Frontend Next.js Build:** Production build passed cleanly with static page pre-rendering and dynamic QR route.
- **Frontend ESLint:** Zero warnings or errors.

---

## 📜 License
Proprietary — Developed for Audio Guide Karakalpakstan & Uzbekistan.
