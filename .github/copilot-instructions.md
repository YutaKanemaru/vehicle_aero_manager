# GitHub Copilot Instructions — Vehicle Aero Manager (VAM)

## Project Overview

VAM is a web browser-based application that helps automotive engineers manage vehicle external aerodynamics (Aero) and greenhouse noise (GHN) CFD simulation setup and post-processing for day-to-day vehicle development.

**Core goals**: Consistency · Efficiency · Collaboration (team of 20–30+ engineers)

**Target solver**: Ultrafluid — a commercial LBM CFD solver driven by XML configuration files.

**Development context**: 1-person team, Python-focused, incremental delivery. Do not over-engineer. Prioritize working software over architectural perfection.

---

## Tech Stack

### MVP (Phase 1–2) — Active Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React 19 / TypeScript / Vite 8 | |
| UI Library | Mantine v8 | Use Mantine components exclusively for UI |
| State (server) | TanStack Query v5 | All API calls go through React Query |
| State (client) | Zustand v5 | `src/stores/` only |
| API typing | openapi-typescript v7 | Auto-generated from FastAPI OpenAPI schema |
| Backend | Python 3.12 / FastAPI | |
| Validation | Pydantic v2 | All models use `model_config`, not `class Config` |
| ORM | SQLAlchemy 2.0 (mapped_column style) | |
| DB | SQLite (MVP) → PostgreSQL (scale) | |
| File Storage | Local FS (MVP) → MinIO/S3 (scale) | Use StorageBackend abstraction |
| Auth | JWT (MVP) → Keycloak (scale) | Use AuthBackend abstraction |
| Task Queue | FastAPI BackgroundTasks (MVP) → Celery (scale) | |
| Package manager | uv | Never use pip directly |
| Deploy | Docker Compose | |
| 3D Rendering | `three` + `@react-three/fiber` + `@react-three/drei` | Phase 2A — Template Builder viewer |
| Mesh Decimation | `stl_decimator` (pure Python + NumPy, no extra deps) | `STLReader` (ASCII+Binary auto-detect) + `ProcessPoolExecutor` parallel pure-Python QEM (`QEMDecimator.simplify`) + `GLBExporter` (flat normals, PALETTE colors, stdlib-only GLB writer) |

### Scale-trigger technologies

**DO NOT introduce in Phase 1–2:**
- PostgreSQL, MinIO, Keycloak, Celery, Redis, Kubernetes, Helm

**Introduce when implementation requires it** (no fixed phase restriction):
- ~~Three.js / React Three Fiber~~ — **✅ introduced in Phase 2A**
- VTK / PyVista — for server-side EnSight result processing (Phase 2B)

---

## Current Implementation Status

### Phase 1: MVP Core (Month 1–4)

| Step | Description | Status |
|---|---|---|
| Step 1 (W1-2) | FastAPI + React + Docker Compose + SQLite + JWT auth | ✅ Complete |
| Step 2 (W3-5) | Ultrafluid Pydantic schema — XML ↔ Pydantic round-trip | ✅ Complete |
| Step 3 (W6-8) | Template CRUD with versioning (Aero/GHN) | ✅ Complete |
| Step 4 (W9-12) | Geometry upload + STL analysis + Compute engine + Kinematics | ✅ Complete |
| Step 5 (W13-16) | XML generation + Case/Configuration/Run management + Diff view + Porous coefficients UI | ✅ Complete |

**All Phase 1 steps are complete.**

### Phase 2A: 3D Viewer / Template Builder

| Step | Description | Status |
|---|---|---|
| 2A-1 to 2A-14 | 3D Viewer / Template Builder — GLB pipeline, SceneCanvas, OverlayObjects, PartListPanel, TemplateBuilderPage, ride height transform, backend-driven overlay data | ✅ Complete |
| 2A-15 | 5-Belt STL generation — `belt_service.py`, `belt_stl_path` on Run, `generate-belts` endpoint, yaw rotation, DPI bypass in XML assembly, frontend Generate Belts button | ✅ Complete |
| 2B | Post-processing EnSight viewer (PyVista backend) | 🔲 Planned |

---

## Repository Structure

```
vehicle_aero_manager/
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml           # uv-managed dependencies
│   ├── alembic/                 # DB migrations — always use Alembic, never create_all()
│   └── app/
│       ├── main.py              # FastAPI entry point — only app setup, no business logic
│       ├── config.py            # Pydantic Settings — env vars with VAM_ prefix
│       ├── database.py          # SQLAlchemy engine, SessionLocal, Base, get_db
│       ├── auth/                # JWT helpers (jwt.py), FastAPI deps (deps.py)
│       ├── api/v1/              # Route handlers only — no business logic here
│       ├── models/              # SQLAlchemy ORM models only
│       ├── schemas/             # Pydantic request/response schemas only
│       ├── services/            # Business logic — DB operations belong here, not in routers
│       │   ├── viewer_service.py      # GLB generation, decimation, cache management
│       │   ├── stl_decimator.py       # Pure-Python QEM decimation (STLReader + QEMDecimator + GLBExporter)
│       │   ├── ride_height_service.py # Ride height / yaw STL transform + System creation
│       │   ├── preview_service.py     # Overlay data: assemble_ufx_solver_deck() → extract_overlay_data() → OverlayData
│       ├── storage/             # StorageBackend abstraction
│       ├── utils/               # Shared utilities
│       │   └── filename.py      # safe_filename() — strips illegal chars, spaces→underscore, max 200 chars
│       └── ultrafluid/          # XML schema (Pydantic), parser, serializer — isolated module
├── frontend/
│   └── src/
│       ├── api/                 # API client — generated schema.d.ts + templateDefaults.ts + typed wrappers
│       │   ├── systems.ts         # systemsApi + transformApi (Phase 2A-5)
│       │   ├── preview.ts         # previewApi.getOverlayData() + OverlayData types
│       ├── components/          # UI components
│       │   ├── cases/
│       │   │   ├── CaseList.tsx             # table with compare-mode toggle; row click → /cases/:id
│       │   │   ├── CaseDetailPage.tsx       # /cases/:caseId — 2 tabs: Case Info & Compare / Runs & Viewer
│       │   │   ├── CaseCreateModal.tsx      # New Case tab + Copy from Case tab
│       │   │   ├── CaseDuplicateModal.tsx
│       │   │   └── CaseCompareModal.tsx     # 2-column run list comparison
│       │   ├── maps/
│       │   │   ├── MapList.tsx
│       │   │   ├── MapCreateModal.tsx
│       │   │   └── ConditionFormModal.tsx  # create/edit condition with ride height accordion
│       ├── hooks/               # Custom React hooks (useTemplateSettingsForm, useJobsPoller, etc.)
│       ├── scripts/             # Build-time Node.js scripts (extract-defaults.mjs)
│       ├── stores/              # Zustand stores only (auth, jobs, viewerStore)
│       ├── components/viewer/   # 3D viewer components (Phase 2A)
│       └── types/               # Shared TypeScript types
└── tests/
```
---

## Docker & Local Development

### Start the full stack

```bash
docker compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### Backend hot reload

Backend source (`backend/app/`) is volume-mounted into the container — changes apply instantly without rebuild.

### Installing Python packages

```bash
# Always use uv, never pip
uv add <package-name>
```

---

## Prohibited Patterns

1. **Do not introduce scale-trigger backend technologies** (Celery, Redis, PostgreSQL, MinIO, Keycloak) until their scale trigger is reached.
2. **Do not write business logic in API routers** — all logic belongs in `app/services/`.
3. **Do not bypass `schema.d.ts`** — never write manual API type definitions in the frontend.
4. **Do not use `Base.metadata.create_all()`** in application code — use Alembic exclusively.
5. **Do not write SQLite-specific SQL** (beyond the `check_same_thread` config) — keep code portable to PostgreSQL.
6. **Do not use `pip install`** — always use `uv add`.
7. **Do not skip ahead to future steps** — implement features in the order defined in the Implementation Phases.
8. **Do not use `class Config` in Pydantic models** — use `model_config = ConfigDict(...)`.
9. **Do not use Japanese (or any non-English language) in user-facing UI text** — all labels, buttons, messages, and tooltips must be in English.
10. **Do not hardcode numeric defaults in `TemplateSettingsForm.tsx` or other UI components** — all form defaults must originate from `SIM_TYPE_PRESETS` / `_aero_setup()` in `backend/app/schemas/template_settings.py`, propagate through `npm run generate-api` → `templateDefaults.ts`, and be consumed via `FORM_DEFAULTS` in `useTemplateSettingsForm.ts`. To change a default: update the Pydantic model/preset, run `npm run generate-api`.

---

## Instructions

Coding conventions are in `.github/instructions/` and auto-applied by VS Code Copilot:

| File | Applies to |
|---|---|
| [backend.instructions.md](instructions/backend.instructions.md) | `backend/**` — SQLAlchemy, Pydantic, Router/Service rules, Alembic, Auth |
| [frontend.instructions.md](instructions/frontend.instructions.md) | `frontend/src/**` — API client, State, Mantine, component patterns |

---

## Specifications

Detailed feature specs are in `docs/specs/` — reference with `#file` in Copilot Chat when working on specific features:

| Spec | Description |
|---|---|
| [Auth](../docs/specs/auth-spec.md) | JWT, roles, endpoints, deps |
| [Ultrafluid XML](../docs/specs/ultrafluid-xml-schema.md) | XML schema, parser, serializer, aero vs GHN differences |
| [Templates](../docs/specs/template-spec.md) | Template CRUD, versioning, JSON schema, TemplateSettingsForm |
| [Geometry & Assembly](../docs/specs/geometry-spec.md) | Upload, STL analysis, background jobs, compute engine, decimation |
| [Case / Run](../docs/specs/case-run-spec.md) | ConditionMap, Case, Run, XML generation, ride-height transform |
| [3D Viewer](../docs/specs/viewer-3d-spec.md) | GLB pipeline, viewer_service, SceneCanvas, OverlayObjects, Template Builder |
| [Roadmap](../docs/specs/roadmap.md) | Phase 2B post-processing, data management, scheduler integration |
