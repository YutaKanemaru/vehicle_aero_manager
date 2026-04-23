# GitHub Copilot Instructions — Vehicle Aero Manager (VAM)

## Project Overview

VAM is a web browser-based application that helps automotive engineers manage vehicle external aerodynamics (Aero) and greenhouse noise (GHN) CFD simulation setup and post-processing for day-to-day vehicle development.

**Core goals:**
- **Consistency**: Standardize simulation settings across a team of 20–30+ engineers
- **Efficiency**: Streamline the CFD workflow from setup to post-processing
- **Collaboration**: Enable asynchronous cross-domain teamwork (CAE, design, management)

**Key features:**
- **Template setup**: Apply Ultrafluid settings via templates; swap geometry while keeping the same naming convention
- **Check setup**: Verify Ultrafluid settings with 3D visualization; diff settings between base and new
- **Case management**: Manage all simulation-related data (input STL, setup, results, post-processed data) in one place
- **Automation**: Once a template is configured, setup through post-processing is automated — adapts to geometry changes (vehicle size, wheel axis, porous media direction, etc.)
- **Post-processing**: GUI session for detailed analysis + lightweight viewer for automated image/movie generation and comparison
- **Data management**: Cross-domain data lifecycle from Pre (CAD/scan) → Solve (XML/results) → Post (tables/images/reports/GSP)

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
| 2A-1 | Backend GLB generation + cache (`viewer_service.py`) + `/glb` endpoint | ✅ Complete |
| 2A-2 | Frontend Three.js setup + `viewerStore` + GLB fetch helper | ✅ Complete |
| 2A-3 | `SceneCanvas`, `OverlayObjects`, `PartListPanel` components | ✅ Complete |
| 2A-4 | `TemplateBuilderPage` (`/template-builder`) + AppShell nav | ✅ Complete |
| 2A-5 | Ride Height / Yaw Transform — `System` model + `ride_height_service.py` + Template Builder UI | ✅ Complete |
| 2A-6 | 3D viewer enhancements: 3-panel layout, Ortho/Persp, FlatShading, Edges, ContextMenu, Probe/PV/SC overlays | ✅ Complete |
| 2A-7 | Case/Run UX: `case_number`/`run_number`, Duplicate, `CaseCreateModal` Copy tab, `CaseCompareModal`, `Run.stl_path` | ✅ Complete |
| 2A-8 | Launch Assembly Builder button in TemplateBuilderPage — `IconPackage` ActionIcon beside Assembly Select opens `AssemblyGeometriesDrawer`; `handleBuilderClose` double-invalidates queries for live 3D refresh | ✅ Complete |
| 2A-9 | Folder structure + sort for all 5 list views — `TemplateFolder`, `ConditionMapFolder`, `CaseFolder` DB tables + migration; folder CRUD endpoints (`/folders/` routes before `/{id}`); `useSortedItems` hook (name/created_at, asc/desc); `FolderSection` (Paper+Collapse) + `SortTh` headers in TemplateList, MapList, CaseList (new folders) + sort-only in existing GeometryList and AssemblyList | ✅ Complete |
| 2A-10 | `AssemblyGeometriesDrawer` redesign — `SegmentedControl` tab switching (Current / Add geometries); Add panel shows folder-grouped collapsible `FolderBlock` sections (Paper + Collapse) with per-folder select-all checkbox; flat fallback when no folders exist; fetches `foldersApi.list()` + `geometriesApi.list()` on open | ✅ Complete |
| 2A-11 | Template Builder redesign — `RideHeightTemplateConfig` in Template schema; `Run.geometry_override_id`; remove Axis Visualisation + Ride Height Transform sections from Template Builder; add `CreateCaseFromBuilderModal`; Ride Height tab in `TemplateSettingsForm` | ✅ Complete |
| 2A-12 | Edit Template button in Template Builder — `IconPencil` ActionIcon beside Template Select opens `TemplateVersionEditModal` for active version; query key unified to `["templates", id, "versions"]` so edits auto-refresh 3D overlays | ✅ Complete |
| 2A-13 | Tabbed Overlay Panel — `OverlayPanel.tsx` replaces flat Switch list; 4 tabs (Parts / Box / Plane / Probe); `overlayVisibility: Record<string, boolean>` in `viewerStore`; per-item visibility keys; Parts tab badges click-to-filter `PartListPanel` | ✅ Complete |
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
│       │   ├── ride_height_service.py # Ride height / yaw STL transform + System creation
│       ├── storage/             # StorageBackend abstraction
│       └── ultrafluid/          # XML schema (Pydantic), parser, serializer — isolated module
├── frontend/
│   └── src/
│       ├── api/                 # API client — generated schema.d.ts + templateDefaults.ts + typed wrappers
│       │   ├── systems.ts         # systemsApi + transformApi (Phase 2A-5)
│       ├── components/          # UI components
│       │   ├── cases/
│       │   │   ├── CaseList.tsx             # table with compare-mode toggle; row click → /cases/:id
│       │   │   ├── CaseDetailPage.tsx       # /cases/:caseId — 4 tabs: Info / Runs / Compare / Viewer
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

## Backend Coding Conventions

### SQLAlchemy Models (`app/models/`)

Use SQLAlchemy 2.0 mapped style consistently:

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SomeModel(Base):
    __tablename__ = "some_table"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow)
```

Rules:
- UUID primary keys as `str(36)` — do not use integer PKs
- Always use `Mapped[T]` + `mapped_column()` — never use `Column()` directly
- Do not put business logic in models
- **CRITICAL**: Always add **both** `default=datetime.utcnow` (Python-side) **and** `server_default=func.now()` (DB-side) to datetime columns. `server_default` only takes effect when Alembic generates the DDL — tables created via raw SQL or `stamp` will have `NULL` datetime values without the Python-side `default`, causing `ResponseValidationError` at runtime.

### Pydantic Schemas (`app/schemas/`)

```python
from pydantic import BaseModel, ConfigDict

class SomeRequest(BaseModel):
    name: str

class SomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
```

- Use `ConfigDict(from_attributes=True)` on all response schemas that read from ORM objects
- Use `model_config = ConfigDict(...)` — never use `class Config`

### API Routers (`app/api/v1/`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.deps import get_current_user

router = APIRouter()

@router.get("/{id}", response_model=SomeResponse)
def get_something(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = some_service.get(db, id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result
```

Rules:
- Routers call services — never write DB queries directly in routers
- Use `HTTPException` for all error responses
- Always declare `response_model`

### Services (`app/services/`)

- One file per domain (e.g., `project_service.py`, `template_service.py`)
- Functions take `db: Session` as first argument
- Return ORM model instances or raise `HTTPException`

### Environment & Configuration

- All settings use `VAM_` prefix in env vars (defined in `app/config.py` via `pydantic-settings`)
- SQLite DB path: always use an **absolute path** derived from `__file__` to avoid working-directory issues:
  ```python
  # app/config.py
  _BACKEND_DIR = Path(__file__).parent.parent
  database_url: str = f"sqlite:///{_BACKEND_DIR / 'data' / 'vam.db'}"
  ```
- `app/database.py` auto-creates the `data/` directory on startup (do not rely on Docker volumes for this)
- Upload directory: `/app/data/uploads`
- Results directory: `/app/data/results`
- Add new settings to `app/config.py` `Settings` class, never hardcode values

### Database Migrations

- **Always use Alembic** for schema changes
- Never call `Base.metadata.create_all()` in application code (only allowed in test setup)
- Generate migrations: `uv run alembic revision --autogenerate -m "description"`
- Apply migrations: `uv run alembic upgrade head`

---

## Auth & User Management

### Role Hierarchy

| Role | Level | Capabilities |
|---|---|---|
| `superadmin` | Highest | All actions + role assignment; created via `create_superadmin.py` |
| `admin` | Elevated | View user list, delete non-superadmin users |
| `engineer` | Default | Normal app access, self-delete only |
| `viewer` | Lowest | Read-only access |

- `is_admin` property returns `True` for both `admin` and `superadmin`
- `is_superadmin` property returns `True` only for `superadmin`

### Auth Endpoints (`app/api/v1/auth.py`)

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | None | User registration |
| `POST` | `/api/v1/auth/login` | None | Login → returns JWT |
| `GET` | `/api/v1/auth/me` | Login | Get own profile |
| `DELETE` | `/api/v1/auth/me` | Login | Delete own account |
| `GET` | `/api/v1/auth/users` | `admin+` | List all users |
| `DELETE` | `/api/v1/auth/users/{id}` | `admin+` | Delete user (cannot delete superadmin) |
| `PATCH` | `/api/v1/auth/users/{id}/role` | `superadmin` | Change user role |

### Auth Dependencies (`app/auth/deps.py`)

```python
get_current_user    # any authenticated user
get_admin_user      # admin or superadmin only (403 otherwise)
get_superadmin_user # superadmin only (403 otherwise)
```

### Schemas (`app/schemas/auth.py`)

```python
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    is_admin: bool
    is_superadmin: bool

class UpdateRoleRequest(BaseModel):
    role: Literal["superadmin", "admin", "engineer", "viewer"]
```

### Creating the First Superadmin

```bash
# Run from the backend/ directory
uv run python create_superadmin.py

# Override defaults via env vars
VAM_SUPERADMIN_EMAIL=my@email.com VAM_SUPERADMIN_PASSWORD=secret uv run python create_superadmin.py
```

Default credentials: `superadmin` / `changeme123`. The script is idempotent — skips if superadmin already exists.

---

## Frontend Coding Conventions

### API Client (`src/api/`)

The TypeScript API schema and form defaults are auto-generated from the FastAPI backend:

```bash
npm run generate-api
```

This runs **3 steps in sequence**:

1. FastAPI → `backend/openapi.json` (OpenAPI spec dump)
2. `openapi-typescript openapi.json` → `src/api/schema.d.ts` (TypeScript types)
3. `backend/dump_template_defaults.py` → `backend/template_defaults.json` → `scripts/extract-defaults.mjs` → `src/api/templateDefaults.ts` (Pydantic runtime defaults)

Write typed wrappers in `src/api/`:

```typescript
// src/api/auth.ts
import { client } from "./client";
import type { paths } from "./schema.d.ts";

type MeResponse = paths["/api/v1/auth/me"]["get"]["responses"]["200"]["content"]["application/json"];

export const authApi = {
  me: (): Promise<MeResponse> => client.get("/api/v1/auth/me").then(r => r.data),
};
```

Rules:
- **Always use `schema.d.ts` types** — never write manual API types
- Run `npm run generate-api` after every backend schema change (models, defaults, or new endpoints)
- Never call `fetch()` or `axios` directly in components — use `src/api/` wrappers
- `templateDefaults.ts` and `schema.d.ts` are **auto-generated** — never edit manually

### Template Form Defaults (`src/api/templateDefaults.ts`)

`templateDefaults.ts` is auto-generated by `npm run generate-api`. It contains `TemplateSettings().model_dump()` output as a TypeScript `as const` object, ensuring the frontend always uses the same default values as the backend Pydantic models.

```typescript
// Auto-generated — do not edit manually
export const templateDefaults = {
  simulation_parameter: { inflow_velocity: 38.88, density: 1.2041, ... },
  setup_option: { meshing: { coarsest_voxel_size: 0.192, ... }, ... },
  setup: {
    domain_bounding_box: [-5, 10, -12, 12, 0, 20],
    meshing: {
      box_refinement: { Box_RL1: { level: 1, box: [-1, 3, -1, 1, -0.2, 1.5] }, ... },
      offset_refinement: { Body_Offset_ALL_RL7: { level: 7, normal_distance: 0.012, parts: [] }, ... },
      ...
    },
  },
  ...
} as const;
```

**`src/hooks/useTemplateSettingsForm.ts`** consumes this in two places:
- `FORM_DEFAULTS` — form initial values reference `templateDefaults.*` directly (e.g. `D.simulation_parameter.inflow_velocity`)
- `valuesFromSettings(settings)` — all `?? fallback` literals replaced with `?? FORM_DEFAULTS.fieldName`

This means there is now a **single source of truth** for all default values: the Pydantic schema. No manual synchronization required.

**When a Pydantic default changes:** run `npm run generate-api` → `templateDefaults.ts` regenerates → `FORM_DEFAULTS` and `valuesFromSettings()` both update automatically.

**`FORM_DEFAULTS` meshing list fields** (built at import time from `D.setup.meshing.*`):
- `box_refinements` — built via `Object.entries(D.setup.meshing.box_refinement)` → populated from `_aero_setup()` in `template_settings.py`
- `offset_refinements` — built via `Object.entries(D.setup.meshing.offset_refinement)` → populated from `_aero_setup()`
- These are no longer hardcoded in `TemplateSettingsForm.tsx` — to change defaults, update `_aero_setup()` and re-run `npm run generate-api`

**Fields that remain hardcoded in `FORM_DEFAULTS`** (no Pydantic equivalent):
- `fd_bbox_xmin/xmax/ymin/ymax/zmin/zmax` — form-specific UI bbox when `full_data.bbox` is null
- `ac_ref_area` (2.4 m²) / `ac_ref_length` (2.7 m) — manual fallback when `reference_area_auto=false`

**Generation pipeline files:**

| File | Role |
|---|---|
| `backend/dump_template_defaults.py` | `TemplateSettings().model_dump()` → `backend/template_defaults.json` |
| `frontend/scripts/extract-defaults.mjs` | `template_defaults.json` → `src/api/templateDefaults.ts` |
| `backend/template_defaults.json` | Intermediate JSON snapshot (committed) |
| `frontend/src/api/templateDefaults.ts` | Final TS `as const` object (committed, auto-generated) |

### State Management

- **Server state**: TanStack Query (`useQuery`, `useMutation`) — for all data from the API
- **Client/UI state**: Zustand stores in `src/stores/` — for auth, UI preferences, etc.
- Do not use `useState` for data that comes from the API

### UI Components

- Use Mantine v8 components for all UI elements (forms, tables, modals, notifications)
- Use `@tabler/icons-react` for icons
- Minimize custom CSS — prefer Mantine's style props and `sx`/`style` API
- Forms: use `@mantine/form`'s `useForm` hook
- **Mantine v8 gotchas**: `Modal.NativeScrollArea` does not exist — omit `scrollAreaComponent` prop entirely. Use `ScrollArea` component directly inside modal content if needed.

### UI Language

- **All user-facing text in the application must be in English** — labels, placeholders, button text, error messages, tooltips, notifications, and modal titles.
- Code comments, commit messages, and internal documentation may be written in either English or Japanese.
- This rule applies to all components under `src/components/` and any string literals rendered to the user.

### Component Structure

```
src/components/
  auth/        # Login, registration pages
  layout/      # AppShell, navigation
  projects/    # Project-level components (Step 3+)
  templates/   # Template CRUD components (Step 3+)
  configurations/  # Configuration management (Step 5+)
```

---

## Ultrafluid XML Schema (Step 2 — Complete)

### Root Pydantic Model

```python
# app/ultrafluid/schema.py
class UfxSolverDeck(BaseModel):
    version: Version
    simulation: Simulation          # general, material, wall_modeling
    geometry: Geometry              # source_file, baffle, domain_bbox, domain_parts
    meshing: Meshing                # general, refinement (box/offset/custom), overset (rotating)
    boundary_conditions: BoundaryConditions  # inlet, outlet, static, wall
    sources: Sources                # porous, mrf, turbulence
    output: Output                  # general, moment_reference_system, aero_coefficients,
                                    # section_cut, probe_file, partial_surface, partial_volume,
                                    # monitoring_surface
```

### Known XML Structure (derived from sample files)

The root element is `<uFX_solver_deck>`. Key sub-structures:

```
<uFX_solver_deck>
  <version>
    <gui_version>          # str e.g. "2024"
    <solver_version>       # str e.g. "2024"
  <simulation>
    <general>
      <num_coarsest_iterations>   # int
      <mach_factor>               # float, default 1.0
      <num_ramp_up_iterations>    # int, default 200
      <parameter_preset>          # "default" | "fan_noise"
    <material>
      <name>                      # str e.g. "Air"
      <density>                   # float [kg/m³]
      <dynamic_viscosity>         # float [kg/(s·m)]
      <temperature>               # float [K]
      <specific_gas_constant>     # float [J/(kg·K)]
    <wall_modeling>
      <wall_model>                # "GLW" | "GWF" | "WangMoin" | "off", default "GLW"
      <coupling>                  # "adaptive_two-way" | "two-way" | "one-way" | "off"
      <transitional_bl_detection> # bool (GHN only)
  <geometry>
    <source_file>                 # str — STL/ZIP filename
    <baffle_parts>                # list of <name>
    <domain_bounding_box>         # x_min/x_max/y_min/y_max/z_min/z_max (Computed)
    <triangle_plinth>             # bool
    <surface_mesh_optimization>
      <triangle_splitting>
        <active>                  # bool — global ON/OFF
        <max_absolute_edge_length>  # float — global limit (0 = disabled)
        <max_relative_edge_length>  # float — global limit
        <triangle_splitting_instance>[]  # optional per-part overrides
          <name>, <active>, <max_absolute_edge_length>, <max_relative_edge_length>
          <parts><name>[]
    <domain_part>
      <export_mesh>               # bool
      <domain_part_instance>[]    # name, location ("z_min" etc.), bounding_range
  <meshing>
    <general>
      <coarsest_mesh_size>        # float (Computed from finest_resolution × 2^n_levels)
      <mesh_preview>              # bool
      <mesh_export>               # bool
      <refinement_level_transition_layers> # int default 8
    <refinement>
      <box><box_instance>[]       # name, refinement_level, bounding_box
      <offset><offset_instance>[] # name, normal_distance, refinement_level, [parts]
      <custom><custom_instance>[] # name, refinement_level, parts (GHN only)
    <overset>
      <rotating><rotating_instance>[]  # name, rpm, center(x/y/z), axis(x/y/z), parts
                                        # Aero: 4 wheels (VREV_*). GHN: empty <overset/>
  <boundary_conditions>
    <inlet><inlet_instance>[]     # name, parts, fluid_bc_settings (type: velocity)
    <outlet><outlet_instance>[]   # name, parts, fluid_bc_settings (type: non_reflective_pressure)
    <static/>                     # typically empty
    <wall><wall_instance>[]       # name, parts, [roughness], fluid_bc_settings
                                  # fluid_bc_settings type: static|slip|moving|rotating
  <sources>
    <porous><porous_instance>[]   # name, inertial_resistance, viscous_resistance,
                                  # porous_axis (x/y/z dir), parts
    <mrf/>                        # typically empty
    <turbulence><turbulence_instance>[]  # name, num_eddies, length_scale,
                                          # turbulence_intensity, point, bounding_box
                                          # Aero only; GHN has no <turbulence>
  <output>
    <general>                     # file_format, output_coarsening, output_variables_full/surface,
                                  # avg_start/window_size/frequency, bounding_box
    <moment_reference_system>     # origin, roll/pitch/yaw axis (no Type field — not in official docs)
    <aero_coefficients>           # reference_area/length, coefficients_along_axis, passive_parts
    <section_cut><section_cut_instance>[]  # GHN specific — high-frequency transient output
    <probe_file><probe_file_instance>[]    # optional — probe locations loaded from CSV
    <partial_surface><partial_surface_instance>[]
    <partial_volume><partial_volume_instance>[]
    <monitoring_surface/>
```

### Aero vs GHN Differences

| Element | Aero | GHN |
|---|---|---|
| `meshing.refinement.custom` | absent | present (VREF_RL7 etc.) |
| `meshing.overset.rotating` | 4 wheels (VREV_*) | empty `<overset/>` |
| `boundary_conditions.wall` | Belt (moving) + wheel (rotating) | static/slip only |
| `sources.turbulence` | present (tg_ground, tg_body) | absent |
| `output.section_cut` | absent | present (high-freq transient) |
| `simulation.wall_modeling.transitional_bl_detection` | absent | present |

### Known Enum Values (from official docs & sample files)

| Field | Valid Values | Default |
|---|---|---|
| `parameter_preset` | `"default"`, `"fan_noise"` | `"default"` |
| `wall_model` | `"GLW"`, `"GWF"`, `"WangMoin"`, `"off"` | `"GLW"` |
| `coupling` | `"adaptive_two-way"`, `"two-way"`, `"one-way"`, `"off"` | `"adaptive_two-way"` |
| `pressure_gradient` | `"favorable"`, `"adverse"`, `"full"`, `"off"` | `"adverse"` |
| `domain_part_instance.location` | `"z_min"`, `"x_min"`, `"x_max"`, `"y_min"`, `"y_max"`, `"z_max"` | — |
| `fluid_bc_settings.type` | `"velocity"`, `"non_reflective_pressure"`, `"static"`, `"slip"`, `"moving"`, `"rotating"` | — |

### Field Classification

| Classification | Description | Example |
|---|---|---|
| `Fixed` | Value defined in a Template, does not change per geometry | `simulation.general.*`, `boundary_conditions.inlet.velocity` |
| `Computed` | Derived from STL geometry analysis (streaming ASCII parser + NumPy) | `geometry.domain_bounding_box`, `meshing.overset.rotating` |
| `UserInput` | Set explicitly by the engineer via UI | `sources.porous.resistance` |

### XML Generation Pipeline

```
Template (JSON/Fixed) + GeometrySet (STL/Computed) + UserInput
    ↓
Compute Engine (trimesh + NumPy)
    ↓
Pydantic model assembly + validation (UfxSolverDeck)
    ↓
lxml.etree serialization
    ↓
Ultrafluid XML file
```

### XML Serialization Rules

> **Reference**: All XML structure, tag naming, field semantics, and parameter values must conform to the official **[Altair ultraFluidX User Guide](https://help.altair.com/hwcfdsolvers/ufx/index.htm)**. When in doubt about an XML element's name, structure, or valid values, consult the user guide first before referring to sample files.

- Use `lxml.etree` for all XML generation — never use `xml.etree.ElementTree`
- Implement a `to_xml()` method or standalone serializer in `app/ultrafluid/serializer.py`
- Implement a `from_xml()` parser in `app/ultrafluid/parser.py`
- Round-trip test required: `parse(serialize(model)) == model`
- XML tag names are snake_case (e.g. `<domain_bounding_box>`, `<num_coarsest_iterations>`)
- Lists of instances use a repeated child pattern: `<box><box_instance>...</box_instance><box_instance>...</box_instance></box>`
- Boolean values are serialized as lowercase strings: `"true"` / `"false"`
- Float values may use scientific notation: e.g. `1.8194e-05`
- Empty optional sections must be serialized as self-closing tags: `<mrf/>`, `<static/>`
- Sample files reference: `docs/samples/aero/AUR_v1.2_EXT_1.99_corrected.xml` (Aero), `docs/samples/GHN/CX1_v1.2_GHN_cut_plane_volume_corrected.xml` (GHN)

---

## Step 3: Template CRUD — Implementation Details (Complete)

### Backend

**Models** (`app/models/template.py`)
- `Template`: `id`, `name`, `description`, `sim_type` (`"aero"`/`"ghn"`), `created_by`, `created_at`, `updated_at`
- `TemplateVersion`: `id`, `template_id`, `version_number`, `settings` (JSON string), `is_active`, `comment`, `created_by`, `created_at`
- `Template.versions` → `cascade="all, delete-orphan"`

**Schemas** (`app/schemas/template.py`, `app/schemas/template_settings.py`)
- `TemplateSettings`: 6-section Pydantic model (`setup_option`, `simulation_parameter`, `setup`, `output`, `target_names`, `porous_coefficients`)
- `TemplateCreate`, `TemplateUpdate`, `TemplateVersionCreate`, `TemplateVersionUpdate`, `TemplateForkRequest` (requests)
- `SettingsValidationError`, `SettingsValidateRequest`, `SettingsValidateResponse` — for JSON import validation
- `TemplateResponse`, `TemplateVersionResponse` (responses — include `active_version`, `version_count`)
- `@field_validator("settings", mode="before")` parses JSON string from DB automatically

**Service** (`app/services/template_service.py`)
- `list_templates`, `get_template`, `create_template`, `update_template`, `delete_template`
- `delete_template()`: raises HTTP 400 if any `Case.template_id` references this template — delete those cases first
- `list_versions`, `create_version`, `activate_version`
- `update_version_settings(db, template_id, version_id, data: TemplateVersionUpdate, current_user)` — overwrites `settings` (and optionally `comment`) of an existing version **in-place**; no new version row created
- `validate_settings(data: dict) -> SettingsValidateResponse` — validates raw dict via `TemplateSettings.model_validate()`; returns normalized settings on success
- `fork_template` — copies active version settings to a new template
- Permission check: `template.created_by == current_user.id OR current_user.is_admin`
- `create_version` / `activate_version`: deactivates all existing versions before setting new active

**API Endpoints** (`app/api/v1/templates.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/templates/` | List all templates |
| `POST` | `/api/v1/templates/` | Create template (creates v1 simultaneously) |
| `POST` | `/api/v1/templates/validate-settings` | Validate raw settings dict; returns normalized or errors |
| `GET` | `/api/v1/templates/presets/{sim_type}` | Return default `TemplateSettings` for a sim_type |
| `GET` | `/api/v1/templates/{id}` | Get template with active version |
| `PATCH` | `/api/v1/templates/{id}` | Update name/description |
| `DELETE` | `/api/v1/templates/{id}` | Delete template + cascade versions |
| `GET` | `/api/v1/templates/{id}/versions` | List all versions |
| `POST` | `/api/v1/templates/{id}/versions` | Create new version (becomes active) |
| `PATCH` | `/api/v1/templates/{id}/versions/{vid}` | **Edit version in-place** — overwrite settings without creating a new version |
| `PATCH` | `/api/v1/templates/{id}/versions/{vid}/activate` | Activate specific version |
| `POST` | `/api/v1/templates/{id}/fork` | Fork: copy active version to new template |

**Route ordering rule**: `/validate-settings` and `/presets/{sim_type}` MUST be declared before `/{template_id}` to avoid routing conflicts.

**Migration**: `alembic/versions/40849f49edd9_add_templates_and_template_versions.py`

### Frontend

**API layer** (`src/api/`)
- `client.ts`: `get`, `post`, `put`, `patch`, `delete` wrappers; handles 204 No Content; exports `client` (primary) and `api` (backward-compat alias)
- `templates.ts`: All endpoints wrapped; all types from `schema.d.ts` (never manual); exports `TemplateVersionUpdate`, `SettingsValidateResponse`
- `auth.ts` `UserResponse` + `stores/auth.ts` `User`: both include `is_admin: boolean` and `is_superadmin: boolean`

**Components** (`src/components/templates/`)

| File | Description |
|---|---|
| `TemplateList.tsx` | Table view with Versions / Edit (active version shortcut) / Fork / Export JSON / Delete action icons per row |
| `TemplateCreateModal.tsx` | Full settings form for creating a new template — `size="90%"`, wraps `TemplateSettingsForm` with `generalContent` (Name / Description / Application / Version comment in the General tab) |
| `TemplateVersionsDrawer.tsx` | Right-side drawer showing version history; New Version button (owner/admin only); per-version 👁 / `</>` / ✏️ (edit, owner/admin) / ✓ (activate, owner/admin) icons |
| `TemplateVersionCreateModal.tsx` | Settings form pre-filled from active version; creates a new version — `size="90%"`, wraps `TemplateSettingsForm`; includes "Load from JSON" file button |
| `TemplateVersionEditModal.tsx` | Settings form pre-filled from the **specific version's** settings; submits `PATCH` to overwrite in-place — `size="90%"`, same structure as CreateModal but title shows "Edit Version vN"; includes "Load from JSON" file button |
| `TemplateSettingsViewModal.tsx` | Read-only view of all settings — `size="90%"`, reuses `TemplateSettingsForm` with `readOnly` prop; `<fieldset disabled>` applied per-panel so tab navigation remains functional |
| `TemplateForkModal.tsx` | Form to fork a template: enter new name, description, comment; copies active version settings |
| `TemplateImportModal.tsx` | File drop → JSON.parse → `POST /validate-settings` → error table or create form (name, description, sim_type, comment) → `templatesApi.create()`; ValidationState: `idle \| loading \| syntax_error \| valid \| invalid` |

**Permission model (frontend)**
- Fork button: visible to all authenticated users
- Export JSON button: visible to all authenticated users (when active_version exists)
- Edit active version shortcut (TemplateList) / Edit button (TemplateVersionsDrawer): visible only when `user.id === template.created_by || user.is_admin`
- Delete button: visible only when `user.id === template.created_by || user.is_admin`
- New Version / Activate buttons: visible only when `user.id === template.created_by || user.is_admin`

**JSON Export / Import**
- Export: downloads active version settings as `{name}_v{N}_settings.json` (JSON stringify of `active_version.settings`)
- Import: `TemplateImportModal` — validates via `POST /validate-settings` before allowing template creation; errors shown in a table
- "Load from JSON" button in `TemplateVersionCreateModal` and `TemplateVersionEditModal` — populates the form with validated+normalized settings without creating anything yet

**In-place edit vs New Version**
- **Edit (in-place)**: `PATCH /versions/{vid}` — overwrites `settings` and optionally `comment` of an existing version row; version_number does NOT change; use when fixing a mistake
- **New Version**: `POST /versions` — always creates a new row with next `version_number`, deactivates all others, becomes the active version; use when you want history

---

## Template JSON Schema (Step 3 Reference)

A Template's `settings` JSON field follows a **5-section + 1 top-level** structure (see `app/schemas/template_settings.py`):

```json
{
  "setup_option": {
    "simulation": {
      "temperature_degree": true,
      "simulation_time_with_FP": false
    },
    "meshing": {
      "triangle_splitting": true,
      "max_absolute_edge_length": 0.0,
      "max_relative_edge_length": 9.0,
      "refinement_level_transition_layers": 8,
      "domain_bounding_box_relative": true,  // always true — UI switch removed, hardcoded in buildSettings()
      "box_offset_relative": true,            // always true — UI switch removed, hardcoded in buildSettings()
      "box_refinement_porous": true,
      "box_refinement_porous_per_coefficient": false,  // true = one BoxInstance per porous_coefficient entry (union of matched parts); UI label: "Box per porous media"
      "triangle_splitting_instances": [       // optional per-part overrides
        { "name": "TS_Body", "active": true, "max_absolute_edge_length": 0.0, "max_relative_edge_length": 5.0, "parts": ["Body_"] }
      ]
    },
    "boundary_condition": {
      "ground": {
        "ground_height_mode": "from_geometry",
        "ground_mode": "rotating_belt_5",
        "overset_wheels": true,
        "ground_patch_active": true,
        // no_slip_xmin_pos: required when apply=true AND (ground_mode != rotating_belt_5 OR no_slip_xmin_from_belt_xmin=false)
        // GroundConfig.model_validator enforces this — ValidationError if missing
        "bl_suction": { "apply": true, "no_slip_xmin_from_belt_xmin": true, "bl_xmin_offset": 0.0 },
        "belt5": { "wheel_belt_location_auto": true, "belt_size_wheel": {"x": 0.4, "y": 0.3}, ... }
      },
      "turbulence_generator": {
        "enable_ground_tg": true, "enable_body_tg": true,
        "ground_tg_intensity": 0.05, "body_tg_intensity": 0.01,
        // num_eddies is hardcoded to 800 in Compute Engine — not stored in settings
        // length_scale: null = auto (4 × coarsest × 0.5^6 = 0.012 when coarsest=0.192)
        "ground_tg_length_scale": null, "body_tg_length_scale": null
      }
    },
    "compute": {
      "adjust_ride_height": false
    }
  },
  "simulation_parameter": {
    "inflow_velocity": 38.88,
    "density": 1.2041,
    "dynamic_viscosity": 1.8194e-5,
    "temperature": 20.0,
    "specific_gas_constant": 287.05,
    "mach_factor": 2.0,
    "num_ramp_up_iter": 200,
    "coarsest_voxel_size": 0.192,
    "number_of_resolution": 7,
    "simulation_time": 2.0,
    "simulation_time_FP": 30.0,
    "start_averaging_time": 1.5,
    "avg_window_size": 0.3,
    "yaw_angle": 0.0
  },
  "setup": {
    "domain_bounding_box": [-5, 10, -12, 12, 0, 20],  // vehicle-relative multipliers
    "meshing": {
      // Keyed dicts — name is the key, value holds level + geometry
      "box_refinement": {
        "Box_RL1": {"level": 1, "box": [-1, 3, -1, 1, -0.2, 1.5]},
        "Box_RL2": {"level": 2, "box": [-0.5, 1.5, -0.75, 0.75, -0.2, 1.0]},
        // ... Box_RL3 / RL4 / RL5 (defaults defined in _aero_setup())
      },
      "part_box_refinement": {},     // legacy (unused in current presets)
      "part_based_box_refinement": { // box defined by parts + per-axis offset factors
        "Box_Porous_RL7": {"level": 7, "parts": ["Porous_"], "offset_xmin": 0.0, "offset_xmax": 0.0, ...}
        // per-coefficient behaviour controlled globally by setup_option.meshing.box_refinement_porous_per_coefficient
        // (False = union bbox of all matched parts → 1 BoxInstance; True = one BoxInstance per porous_coefficients entry, name: {entry_name}_{coeff.part_name})
      },
      "offset_refinement": {
        "Body_Offset_ALL_RL7": {"level": 7, "normal_distance": 0.012, "parts": []},
        "Body_Offset_ALL_RL6": {"level": 6, "normal_distance": 0.036, "parts": []}
      },
      "custom_refinement": {}        // GHN only
    }
  },
  "output": {
    "full_data": {
      "output_start_time": 1.5, "output_interval": 0.3,
      "file_format": "h3d",
      "output_coarsening_active": false,
      "bbox_mode": "from_meshing_box",
      "output_variables_full": { "pressure": false, ... },
      "output_variables_surface": { "pressure": false, ... }
    },
    "partial_surfaces": [
      { "name": "PS_Body", "output_start_time": 1.5, "output_interval": 0.3, "file_format": "h3d",
        "include_parts": ["Body_"], "exclude_parts": [],
        "baffle_export_option": null, "output_variables": {...} }
    ],
    "partial_volumes": [
      { "name": "PV_Wake", "output_start_time": 1.5, "output_interval": 0.3, "file_format": "h3d",
        "bbox_mode": "user_defined",
        "bbox": [-1, 5, -1.5, 1.5, 0, 1.5], "output_variables": {...} },
      { "name": "PV_RL5", "output_start_time": 1.5, "output_interval": 0.3, "file_format": "h3d",
        "bbox_mode": "from_meshing_box",
        "bbox_source_box_name": "Box_RL5", "output_variables": {...} }
    ],
    "section_cuts": [
      { "name": "SC_Center", "output_start_time": 1.5, "output_interval": 0.3, "file_format": "h3d",
        "axis_x": 0, "axis_y": 1, "axis_z": 0,
        "point_x": 0, "point_y": 0, "point_z": 0.5, "bbox": [], "output_variables": {...} }
    ],
    "probe_files": [
      { "name": "front_probes", "probe_type": "volume", "radius": 0.05,
        "output_frequency": 1.0, "output_start_iteration": 0,
        "scientific_notation": true, "output_precision": 7,
        "output_variables": { "cp": true, "time_avg_pressure": true },
        "points": [ {"x_pos": 0.5, "y_pos": 0.0, "z_pos": 0.3, "description": "nose"} ]
      }
    ],
    "aero_coefficients": {
      "reference_area_auto": true, "reference_length_auto": true,
      "coefficients_along_axis_active": false
    }
  },
  "target_names": {
    "wheel": ["Wheel_"], "rim": ["_Spokes_"],
    "baffle": ["_Baffle_"],
    "windtunnel": [], "wheel_tire_fr_lh": "", "wheel_tire_fr_rh": "",
    "wheel_tire_rr_lh": "", "wheel_tire_rr_rh": "",
    "overset_fr_lh": "", "overset_fr_rh": "", "overset_rr_lh": "", "overset_rr_rh": "",
    "tire_roughness": 0.0
  },
  "porous_coefficients": [
    { "part_name": "Porous_Media_Radiator", "inertial_resistance": 50.0, "viscous_resistance": 10.0 }
  ]
}
```

**Key principles:**
- `setup_option` (flags) + `simulation_parameter` (physical values) + `setup` (geometry-relative rules) are **Fixed** in Template.
- `output` fully defines all output instances (full data, partial surface/volume, section cuts, probe files).
- `target_names` maps solver concepts to part-naming patterns.
- `porous_coefficients` provides default porous resistance values (can be overridden per Configuration).

---

## Step 4: Geometry Upload + STL Analysis + Assembly — Implementation Details (Complete)

### Data Model (5-layer hierarchy)

| Model | Purpose |
|---|---|
| `GeometryFolder` | Optional organisational folder for grouping Geometries (e.g. by vehicle type) |
| `Geometry` | Single STL file entity — stores file path, status, and analysis results |
| `AssemblyFolder` | Optional organisational folder for grouping Assemblies |
| `GeometryAssembly` | Named collection of Geometries — optionally linked to an AssemblyFolder |
| `assembly_geometry_link` | Many-to-many association table |

**Part swap workflow**: change which `Geometry` objects are members of a `GeometryAssembly`.
**Folder workflow**: purely organisational — both Geometry and Assembly hierarchies use the same folder pattern.

### Backend

**Models** (`app/models/geometry.py`)
- `GeometryFolder`: `id`, `name`, `description`, `created_by`, `created_at`, `updated_at`; `geometries` one-to-many relationship
- `Geometry`: `id`, `name`, `description`, `folder_id` (nullable FK→geometry_folders), `file_path` (upload時: `upload_dir` 相対パス / link時: 絶対パス), `original_filename`, `file_size`, `is_linked: bool` (default `False` — `True` の場合消死時にファイルを肝ない), `status` (`pending`/`analyzing`/`ready`/`error`), `analysis_result` (JSON string), `error_message`, `uploaded_by` (FK→users), `created_at`, `updated_at`
- `AssemblyFolder`: `id`, `name`, `description`, `created_by`, `created_at`, `updated_at`; `assemblies` one-to-many relationship
- `GeometryAssembly`: `id`, `name`, `description`, `folder_id` (nullable FK→assembly_folders), `created_by`, `created_at`, `updated_at`; `geometries` many-to-many relationship; `folder` many-to-one relationship
- `assembly_geometry_link`: association table (`assembly_id`, `geometry_id`)
- Class ordering in file: `assembly_geometry_link` → `GeometryFolder` → `Geometry` → `AssemblyFolder` → `GeometryAssembly`

**Schemas** (`app/schemas/geometry.py`)
- `PartInfo`: `centroid [x,y,z]`, `bbox dict`, `vertex_count`, `face_count`
- `AnalysisResult`: `parts`, `vehicle_bbox`, `vehicle_dimensions`, `part_info dict`
- `GeometryResponse`: full response including parsed `analysis_result`, `folder_id: str | None`, `is_linked: bool`
- `GeometryUpdate`: `name`, `description`, `folder_id` — uses `model_fields_set` to distinguish explicit null (remove from folder) from field not sent
- `GeometryLinkRequest`: `name`, `description`, `file_path` (server absolute path), `folder_id` — for Link only mode
- `GeometryFolderCreate`, `GeometryFolderUpdate`, `GeometryFolderResponse`
- `AssemblyFolderCreate`, `AssemblyFolderUpdate`, `AssemblyFolderResponse`
- `AssemblyCreate`, `AssemblyUpdate` — both include `folder_id: str | None = None`
- `AssemblyResponse` — includes `geometries: list[GeometryResponse]` and `folder_id: str | None`
- `@field_validator("analysis_result", mode="before")` parses JSON string from DB automatically

**Compute Engine** (`app/services/compute_engine.py`)
- `_detect_stl_format(file_path) -> "ascii" | "binary"`: reads 84 bytes only — detects binary by magic bytes OR by `80 + 4 + n*50 == file_size` check to handle binaries whose header starts with `solid`
- `_parse_stl_ascii_streaming(file_path, verbose) -> dict`: line-by-line streaming parser — **never allocates vertex arrays**; maintains running `x_min/max, y_min/max, z_min/max, vertex_count, face_count` per solid; centroid = bbox center `(min+max)/2` on `endsolid`
- `analyze_stl(file_path: Path) -> dict`: calls `_detect_stl_format` → raises `ValueError` if binary; calls streaming parser; computes vehicle bbox by union of per-part bboxes (no `np.concatenate`)
- **Binary STL is not supported** — `ValueError("Binary STL format is not supported. Please convert to ASCII STL before uploading.")` is raised immediately
- Extracts per-part: centroid (bbox center), bbox (x/y/z min/max), vertex_count, face_count
- Computes vehicle bbox (union of all parts) and dimensions (length, width, height)
- Returns JSON-serializable dict matching `AnalysisResult` schema
- Multi-solid ASCII STL fully supported

**Service** (`app/services/geometry_service.py`)
- `upload_geometry(db, name, description, file, current_user, folder_id=None)`: saves file to `upload_dir/geometries/{id}/{filename}` using `shutil.copyfileobj(..., length=8MB)` (chunked — avoids holding full file in memory), stores relative path, triggers `BackgroundTasks`
- `link_geometry(db, data: GeometryLinkRequest, current_user)`: validates path exists on server, creates `Geometry` row with `is_linked=True` and absolute `file_path`, triggers `BackgroundTasks`
- `run_analysis()`: background task — `pending` → `analyzing` → `ready`/`error`; `is_linked=True` 時は `file_path` を絶対パスとしてそのまま使用、`is_linked=False` 時は `settings.upload_dir / file_path`
- `update_geometry()`: uses `model_fields_set` — only updates `folder_id` when field is explicitly in request body
- `delete_geometry()`: `is_linked=False` の時のみファイル削除。`file_path` が相対パスなら `upload_dir` から解決、絶対パスならそのまま使用。`upload_dir` そのものを削除しない安全ガードあり。ファイル削除は `_rmtree_force(path)` ヘルパー（Windows read-only 属性対策: `onerror` で `os.chmod(S_IWRITE)` してリトライ）で実行。削除失敗時は `logger.warning` で報告（サイレントにスキップしない）。`is_linked=True` の場合は DB 行のみ削除し元ファイルはそのまま
- `list_folders`, `create_folder`, `update_folder`, `delete_folder` — folder delete sets `geometry.folder_id = None` for all children
- `_folder_or_404(db, folder_id)` helper validates folder existence
- All CRUD for both `Geometry` and `GeometryAssembly`
- Assembly folder CRUD: `list_assembly_folders`, `create_assembly_folder`, `update_assembly_folder`, `delete_assembly_folder` — delete sets `assembly.folder_id = None` for all children
- `_assembly_folder_or_404(db, folder_id)` helper validates assembly folder existence
- `create_assembly()` accepts `folder_id`; `update_assembly()` handles `folder_id` via `model_fields_set`
- `delete_assembly()`: raises HTTP 400 if any `Case.assembly_id` references this assembly — delete or reassign those cases first
- `add_geometry_to_assembly`, `remove_geometry_from_assembly`
- Permission check: `resource.created_by == current_user.id OR current_user.is_admin`

**API Endpoints**

`app/api/v1/geometries.py` (`/api/v1/geometries/`):
| Method | Path | Description |
|---|---|---|
| `GET` | `/geometries/folders/` | List all folders |
| `POST` | `/geometries/folders/` | Create folder |
| `PATCH` | `/geometries/folders/{folder_id}` | Update folder |
| `DELETE` | `/geometries/folders/{folder_id}` | Delete folder (children become uncategorized) |
| `GET` | `/geometries/` | List all geometries |
| `POST` | `/geometries/` | Upload STL (multipart/form-data: `name`, `description`, `folder_id`, `file`) — triggers background analysis |
| `POST` | `/geometries/link` | Link only (JSON body: `GeometryLinkRequest`) — ファイルコピーなしでサーバーパスのみ登録、即解析 |
| `GET` | `/geometries/{id}` | Get geometry with analysis result |
| `PATCH` | `/geometries/{id}` | Update name/description/folder_id |
| `DELETE` | `/geometries/{id}` | Delete + file cleanup (linked files are not deleted) |

**Route order matters**: folder endpoints MUST be declared before `/{geometry_id}` in the router file to avoid FastAPI routing ambiguity.

`app/api/v1/assemblies.py` (`/api/v1/assemblies/`):
| Method | Path | Description |
|---|---|---|
| `GET` | `/assemblies/folders/` | List all assembly folders |
| `POST` | `/assemblies/folders/` | Create assembly folder |
| `PATCH` | `/assemblies/folders/{folder_id}` | Update assembly folder |
| `DELETE` | `/assemblies/folders/{folder_id}` | Delete assembly folder (children become uncategorized) |
| `GET` | `/assemblies/` | List all assemblies |
| `POST` | `/assemblies/` | Create assembly |
| `GET` | `/assemblies/{id}` | Get assembly with geometries (selectinload) |
| `PATCH` | `/assemblies/{id}` | Update name/description/template_id/folder_id |
| `DELETE` | `/assemblies/{id}` | Delete assembly |
| `POST` | `/assemblies/{id}/geometries/{gid}` | Add geometry to assembly |
| `DELETE` | `/assemblies/{id}/geometries/{gid}` | Remove geometry from assembly |

**Route order matters**: folder endpoints MUST be declared before `/{assembly_id}` in assemblies.py to avoid FastAPI routing ambiguity.

**Migrations**:
- `alembic/versions/f46197300d43_add_geometry_and_assembly_tables.py`
- `alembic/versions/d4be3f102eac_add_geometry_folders_and_folder_id_to_.py` — uses `batch_alter_table` for `folder_id` FK (SQLite cannot `ALTER TABLE` to add FK constraints directly)
- `alembic/versions/bd293b1f57fc_add_assembly_folders.py` — creates `assembly_folders` table; adds `folder_id` FK to `geometry_assemblies` via `batch_alter_table`
- `alembic/versions/b6662ad9ba21_add_is_linked_to_geometries.py` — adds `is_linked` boolean column to `geometries` (server_default `0`)

### Frontend

**API layer** (`src/api/geometries.ts`)
- `foldersApi.list()`, `.create(data)`, `.update(id, data)`, `.delete(id)` — geometry folders
- `geometriesApi.list()`, `.get(id)`, `.upload(name, description, folderId, file, onProgress?)` — uses `XMLHttpRequest` (not `fetch`) to support `upload.onprogress` callbacks; `onProgress(pct: number)` fires with 0–100 values
- `geometriesApi.link(data: GeometryLinkRequest)` — Link only登録（JSON POST to `/geometries/link`）
- `geometriesApi.updateFolder(id, folderId)` — convenience wrapper for PATCH with `{ folder_id }`
- `geometriesApi.delete(id)`
- `assemblyFoldersApi.list()`, `.create(data)`, `.update(id, data)`, `.delete(id)` — assembly folders
- `assembliesApi.list()`, `.get(id)`, `.create(data)`, `.update(id, data)`, `.delete(id)`, `.addGeometry(assemblyId, geometryId)`, `.removeGeometry(assemblyId, geometryId)`
- Exported types: `AssemblyFolderResponse`, `AssemblyFolderCreate`, `AssemblyFolderUpdate`

**Components** (`src/components/geometries/`, `src/components/assemblies/`)

| File | Description |
|---|---|
| `GeometryList.tsx` | Folder-hierarchy view: geometries grouped into collapsible `FolderSection` panels (Paper + Collapse). Uncategorized geometries shown last. Each geometry row has expand-for-analysis-details + move-to-folder Popover (Select dropdown). Header has "New Folder" + "Upload STL" buttons. Auto-refreshes every 3s when any item is `pending`/`analyzing`. On delete: calls `removeJob(geometry.id)` immediately so the job disappears from the drawer even if geometry is still in `pending`/`analyzing` state. |
| `GeometryUploadModal.tsx` | Upload form: name, description, folder select (from `foldersApi.list()`), STL file input. **Modal closes immediately** after registering jobs in the drawer — XHR transfers continue in background (fire-and-forget). No `uploading` blocking state on the modal. Progress tracked exclusively in Jobs Drawer via `updateUploadProgress`. |
| `GeometryLinkModal.tsx` | Link only登録フォーム: name, description, file_path (server absolute path), folder select. JSON POST を使用（XHR不要）。成功後は uploadと同様に job トラッカーに登録。 |
| `AssemblyList.tsx` | Folder-hierarchy view: assemblies grouped into collapsible `FolderSection` panels (Paper + Collapse). Uncategorized assemblies shown last. Each assembly row has manage-geometries action + move-to-folder Popover. Header has "New Folder" (IconFolderPlus) + "New Assembly" buttons. Folder delete: `delete_assembly_folder` sets all children to uncategorized. |
| `AssemblyCreateModal.tsx` | Create assembly with optional folder select (`assemblyFoldersApi.list()`) — **no template link** (removed) |
| `AssemblyGeometriesDrawer.tsx` | Right-side drawer; accepts `assemblyId: string | null` and fetches assembly data via `useQuery(["assembly", assemblyId])` internally (always fresh). `SegmentedControl` tab switching: **Current** tab — geometry rows with status badge + Remove button; **Add geometries** tab — geometries grouped into collapsible `FolderBlock` sections (Paper + Collapse, open by default), each folder header has select-all checkbox (with indeterminate state) + count badge + chevron toggle; uncategorized geometries shown as an "Uncategorized" folder when other folders exist, or as a plain flat list when no folders are defined; footer sticky "Add selected (N)" button; fetches `foldersApi.list()` + `geometriesApi.list()` (enabled only when `opened`); mutation `onSuccess` invalidates `["assembly", assemblyId]` + `["assemblies"]` for instant UI refresh |

**Navigation**: `AppShell.tsx` nav includes `Geometries` (IconBox) and `Assemblies` (IconStack2).

### Implementation Notes
- Upload endpoint uses `Form()` + `File()` FastAPI dependencies — NOT JSON body
- Link endpoint uses JSON body (`GeometryLinkRequest`) — `file_path` must be accessible from the backend container; in Docker, the directory must be volume-mounted
- Frontend upload uses `XMLHttpRequest` (not `fetch`) for `upload.onprogress` support; the JSON `client` wrapper cannot handle multipart
- `is_linked=True` geometries show a cyan "Linked" badge in `GeometryList.tsx`; delete only removes the DB row, not the original file
- Status polling: `refetchInterval` returns `3000` when any geometry is `pending`/`analyzing`, `false` otherwise
- SQLite FK workaround: use `op.batch_alter_table()` in Alembic whenever adding FK constraints to existing tables
- Kinematics (ride height adjustment) deferred — correct-posture STL is assumed for now

---

## Background Jobs System (Step 4 Addition)

A lightweight client-side job tracker for long-running background tasks (STL analysis, file upload).

### Zustand Store (`src/stores/jobs.ts`)

```typescript
export type JobType = "stl_analysis";
export type JobStatus = "uploading" | "pending" | "analyzing" | "ready-decimating" | "ready" | "error";

export interface Job {
  id: string;
  name: string;
  type: JobType;
  status: JobStatus;
  uploadProgress?: number; // 0-100, only set when status === "uploading"
  error_message?: string | null;
  addedAt: number;
}
```

**Actions**: `addJob(id, name, type)` — starts as `uploading` · `updateJob(id, status, error_message?)` · `updateUploadProgress(id, progress)` · `removeJob(id)` · `clearCompleted()` (removes `ready` + `error` only; use per-job X button for other statuses)

**Selectors**: `selectActiveJobs(s)` · `selectActiveCount(s)` — both include `uploading` + `pending` + `analyzing` + `ready-decimating`

**Persistence**: `zustand/middleware persist` with `partialize` — stores only jobs younger than 24 hours

### Upload Flow
1. `addJob(tempId, name, "stl_analysis")` — job immediately appears as "Uploading…" in drawer
2. **Modal closes immediately** — user can continue using the app
3. XHR `upload.onprogress` → `updateUploadProgress(tempId, pct)` — progress bar updates in real time
4. On XHR success → `removeJob(tempId)` + `addJob(realId, name, ...)` + `updateJob(realId, "pending")`
5. `useJobsPoller` picks up the real ID and polls until `ready`/`error`

### Poller Hook (`src/hooks/useJobsPoller.ts`)
- Mounted in `AppShell` — runs for the lifetime of the app
- Polls `GET /geometries/` every 3 s when any job is `pending`, `analyzing`, or `ready-decimating`
- **Does NOT poll** `uploading` jobs — those are tracked entirely via XHR callbacks
- Uses `useInterval` from `@mantine/hooks`
- **Deleted geometry cleanup (during polling)**: if a `pending`/`analyzing`/`ready-decimating` job ID is not found in the API response, `removeJob()` is called immediately. `ready`/`error` stale jobs are also cleaned on the same cycle.
- **Deleted geometry cleanup (after polling stops)**: when `hasActive` transitions `true→false`, runs one final `geometriesApi.list()` to remove any `ready`/`error` jobs whose geometry was deleted while no polling was active.

### Jobs Drawer (`src/components/layout/JobsDrawer.tsx`)
- Triggered from AppShell header button with active-count `Indicator` badge
- **In Progress** section: `uploading`, `pending`, `analyzing`, `ready-decimating` jobs
- **Completed** section: `ready`, `error` jobs + "Clear" button removes them all
- Status configs: `uploading` (cyan, real progress %) · `pending` (yellow, 15% animated) · `analyzing` (blue, 60% striped) · `ready-decimating` (violet, 85% striped) · `ready` (green, 100%) · `error` (red, 100%)
- Badge for `uploading` status shows live `XX%` instead of label text
- **Per-job ✕ button**: every job row has an `ActionIcon` dismiss button — calls `removeJob(id)`. Allows manual removal of any job regardless of status (e.g. stuck `uploading 100%`).

---

## Compute Engine Notes (Step 4 Reference)

The Compute Engine derives `Computed` fields from STL geometry. Key calculations:

| Output | Method | Library |
|---|---|---|
| `domain_bounding_box` | Vehicle bbox × relative multipliers from template | `trimesh` or `numpy` |
| `meshing.overset.rotating` (wheel center/axis) | PCA on rim vertices via `extract_pca_axes()` → axis = `vt[2]` (min variance = rotation axis) | `numpy` |
| `sources.porous.porous_axis` | PCA on porous vertices via `extract_pca_axes()` → `vt[2]` (min variance = face normal = flow direction) | `numpy` |
| `boundary_conditions.wall` (rotating) | Linked to wheel center/axis/rpm | derived from above |

**Additional Compute Engine calculations (Step 4):**

| Output | Method |
|---|---|
| Kinematics (ride height) | Apply user-specified ride height adjustment to geometry |
| Coordinate system conversion | Adjust post-processing settings to new coordinate system after kinematics adjustment |
| Porous media coefficients | Apply user-input resistance values to matched porous parts |

**Implementation rules for Compute Engine:**
- Use `numpy` for XML assembly math — `trimesh` import remains but is NOT used in `analyze_stl`
- Do NOT use `numpy-stl`, `scikit-learn`, or `trimesh.load()` in `analyze_stl` — use the internal streaming parser
- **ASCII STL only**: binary STL raises `ValueError` immediately — users must convert to ASCII before uploading
- STL files may be multi-solid ASCII format — streaming parser handles `solid`/`endsolid` blocks sequentially
- `analyze_stl` never allocates vertex arrays — peak memory during analysis is O(number of parts), not O(file size)
- Centroid = bounding box center `(min+max)/2` per axis — NOT vertex average
- **Part name normalization**: `_normalize_stl_part_name(name)` strips `COMMENT: ...` suffixes injected by CAD exporters (e.g. Altair Inspire). Applied in `_parse_stl_ascii_streaming` (analysis) and `STLReader._read_ascii` (decimator/GLB). Both sites must stay in sync so `analysis_result.parts` keys match GLB node names for Three.js part-state lookup.
- Wheel grouping: classify FR-LH / FR-RH / RR-LH / RR-RH by comparing part centroid to vehicle COG (x, y)
- RPM calculation: `rpm = (inflow_velocity / wheel_circumference) × 60` — needs wheel radius from bbox
- `analyze_stl(file_path, verbose=False)` — pass `verbose=True` to print step-by-step progress logs (used by `backend/scripts/test_compute_engine.py`)
- **`extract_pca_axes()` is a separate STL re-scan** — `analyze_stl` intentionally discards vertices for memory efficiency; `extract_pca_axes` streams the STL a second time collecting only the vertices of matched parts
- **Porous axis PCA**: uses `vt[2]` (min variance direction = face normal = flow direction through the flat porous surface). `vt[0]` was wrong and has been corrected.
- **Rim axis PCA**: uses `vt[2]` (min variance = rotation axis of the flat rim disk); if `y < 0`, flip sign.
- **Porous matching**: `porous_coefficients[].part_name` is a glob pattern — `_matches_any` is used so `HX_Rad_*` can match multiple parts (e.g. inlet + outlet). All matched parts are grouped into a single `PorousInstance` with their combined vertices used for PCA.

**Test script**: `backend/scripts/test_compute_engine.py` — runs `analyze_stl()` standalone and prints vehicle bbox, dimensions, and per-part summary. Run with `uv run python scripts/test_compute_engine.py [<stl_path>]`. Auto-detects first STL in `data/uploads/geometries/` if no argument given. Saves full result to `test_compute_engine_result.json`.

---

## Step 5: Case / Configuration / Run — Implementation Details (Complete)

> **Note**: The original `Configuration` model has been refactored into `ConditionMap` + `Condition`. The term "Configuration" no longer exists in the codebase.

### Data Model (4-layer hierarchy)

| Model | File | Purpose |
|---|---|---|
| `ConditionMap` | `app/models/configuration.py` | Named collection of run conditions (e.g. "40m/s sweep") |
| `Condition` | `app/models/configuration.py` | Single run condition: velocity + yaw + ride_height_json + yaw_config_json |
| `Case` | `app/models/configuration.py` | Bundles Template × Assembly; optionally linked to a ConditionMap |
| `Run` | `app/models/configuration.py` | Execution unit: links Case + Condition → generates XML |
| `System` | `app/models/system.py` | STL transform record: source_geometry → result_geometry + transform_snapshot |

**Design decision**: ConditionMaps are independent of Cases — they can be reused across multiple Cases. A Run picks one Condition from any map.

### Backend

**Models** (`app/models/configuration.py`)
- `ConditionMap`: `id`, `name`, `description`, `created_by`, `created_at`, `updated_at`; `conditions` one-to-many (cascade delete)
- `Condition`: `id`, `map_id` (FK→condition_maps, index), `name`, `inflow_velocity`, `yaw_angle`, `ride_height_json` (Text, nullable), `yaw_config_json` (Text, nullable), `created_by`, `created_at`, `updated_at`
  - `@property ride_height` → parses `ride_height_json` or returns `{}`
  - `@property yaw_config` → parses `yaw_config_json` or returns `{}`
- `Case`: `id`, `case_number`, `name`, `description`, `template_id` (FK→templates), `assembly_id` (FK→geometry_assemblies), `map_id` (FK→condition_maps, nullable), `folder_id` (nullable FK→case_folders), `parent_case_id` (nullable self-FK → cases, ondelete SET NULL), `created_by`, `created_at`, `updated_at`; `runs` relationship
- `Run`: `id`, `run_number`, `name`, `case_id` (FK→cases, CASCADE, index), `condition_id` (FK→conditions), `xml_path` (nullable), `stl_path` (nullable), `geometry_override_id` (nullable FK→geometries, ondelete SET NULL — overrides assembly geometry for XML generation), `status` (`pending`/`generating`/`ready`/`error`), `error_message` (nullable), `scheduler_job_id` (nullable), `created_by`, `created_at`, `updated_at`

**Models** (`app/models/system.py`)
- `System`: `id`, `name`, `source_geometry_id` (FK→geometries), `result_geometry_id` (FK→geometries, nullable), `condition_id` (FK→conditions, nullable), `transform_snapshot` (Text/JSON), `created_by`, `created_at`

**Schemas** (`app/schemas/configuration.py`)

```python
class RideHeightConditionConfig(BaseModel):
    enabled: bool = False
    target_front_wheel_axis_rh: float | None = None  # m from ground
    target_rear_wheel_axis_rh: float | None = None
    # used when template.ride_height.adjust_body_wheel_separately=True and use_original_wheel_position=False
    target_front_wheel_rh: float | None = None
    target_rear_wheel_rh: float | None = None

# NOTE: adjust_body_wheel_separately / use_original_wheel_position moved to RideHeightTemplateConfig (template_settings.py)

class YawConditionConfig(BaseModel):
    center_mode: Literal["wheel_center", "user_input"] = "wheel_center"
    center_x: float = 0.0
    center_y: float = 0.0

class ConditionCreate(BaseModel):
    name: str
    inflow_velocity: float
    yaw_angle: float = 0.0
    ride_height: RideHeightConditionConfig = Field(default_factory=RideHeightConditionConfig)
    yaw_config: YawConditionConfig = Field(default_factory=YawConditionConfig)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Strip whitespace; reject empty string."""
        if not v.strip():
            raise ValueError("Condition name must not be empty")
        return v.strip()

class ConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; map_id: str; name: str; inflow_velocity: float; yaw_angle: float
    ride_height: RideHeightConditionConfig
    yaw_config: YawConditionConfig
    created_by: str; created_at: datetime; updated_at: datetime
    # @model_validator(mode="before") parses ride_height_json / yaw_config_json from ORM

class ConditionMapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; name: str; description: str | None
    created_by: str; created_at: datetime; updated_at: datetime
    condition_count: int = 0  # populated in router

class TransformRequest(BaseModel):
    """POST /geometries/{id}/transform"""
    name: str  # name for the resulting Geometry
    condition_id: str | None = None
    ride_height: RideHeightConditionConfig = Field(default_factory=RideHeightConditionConfig)
    rh_template: RideHeightTemplateConfig = Field(default_factory=RideHeightTemplateConfig)  # "how" config (separate/original-pos)
    yaw_angle_deg: float = 0.0
    yaw_config: YawConditionConfig = Field(default_factory=YawConditionConfig)

class SystemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; name: str; source_geometry_id: str; result_geometry_id: str | None
    condition_id: str | None; transform_snapshot: dict | None
    created_by: str; created_at: datetime
```

- `CaseCreate`, `CaseUpdate` (`name`, `description`, `template_id`, `assembly_id`, `map_id`, `folder_id`), `CaseResponse` (includes `run_count`, `case_number`, `template_name`, `assembly_name`, `map_name`, `parent_case_id`, `parent_case_number`, `parent_case_name`)
- `CaseDuplicateRequest`: `{ name, description }` — copies active template/assembly/map from source case; auto-sets `parent_case_id`
- `RunCreate`: `{ name: str = "", condition_id, comment: str = "" }` — if `name` is empty, auto-formats as `{case_number}_{run_number}_{condition_name}[_{comment}]`
- `RunResponse` (includes `xml_path`, `stl_path`, `status`, `run_number`, `condition_name`, `condition_velocity`, `condition_yaw`, `geometry_override_id`)
- `RunUpdate`: `{ geometry_override_id: str | None }` — used to set geometry override after ride-height transform
- `DiffResult`: list of changed fields between two Runs
- `PartsDiffResult`: `{ added: list[str], removed: list[str], common: list[str] }` — assembly parts comparison
- `CaseCompareResult`: `{ base_case_id, compare_case_id, base_case_number, compare_case_number, template_settings_diff: list[DiffField], map_diff: list[DiffField], parts_diff: PartsDiffResult }`

**Service** (`app/services/configuration_service.py`)
- `list_maps`, `get_map`, `create_map`, `update_map`, `delete_map`
- `delete_map()`: raises HTTP 400 if any `Case.map_id` references this map — unlink or delete those cases first
- `list_conditions(map_id)`, `get_condition`, `create_condition`, `update_condition`, `delete_condition` — JSON fields serialized via `json.dumps(data.ride_height.model_dump())`
- `delete_condition()`: raises HTTP 400 if any `Run.condition_id` references this condition — delete those runs first
- `list_cases`, `get_case`, `create_case`, `update_case`, `delete_case`
- `update_case()`: accepts `template_id` and `assembly_id` updates (validates existence)
- `delete_case()`: cascades DB delete to Runs; also deletes `data/runs/{run_id}/` output directories
- `create_run(case_id, data: RunCreate, current_user)`: auto-name = `{case_number}_R{n:02d}_{condition_name}[_{comment}]` when `data.name` is empty; `data.comment` appended as suffix
- `list_runs(case_id)`
- `delete_run(db, case_id, run_id, current_user)` — deletes Run row + `data/runs/{run_id}/` directory
- `reset_run(db, case_id, run_id, current_user)` — clears `xml_path`, `stl_path`, `error_message`, sets `status="pending"`, deletes output dir
- `update_run(db, case_id, run_id, data: RunUpdate, current_user)` — updates `geometry_override_id` on a Run (PATCH)
- `trigger_xml_generation(db, case_id, run_id, current_user, background_tasks, geometry_only=False)` — triggers `_generate_xml_task(run_id, geometry_only)`
- `_generate_xml_task(run_id, geometry_only=False)` — background task. When `geometry_only=True` and `case.parent_case_id` is set: finds parent's ready Run (same condition preferred), parses its XML via `parse_ufx()`, swaps `geometry.source_file` for the new assembly STL, serializes and saves — skips full re-assembly. Falls back to full generation if no parent ready run found.
- `duplicate_case(db, source_case_id, data: CaseDuplicateRequest, current_user)` — copies Case row (same template/assembly/map); sets `parent_case_id = source_case_id`; does NOT copy Runs
- `create_case_with_runs(db, case_data, current_user)` — creates Case + one Run per Condition; run names auto-formatted as `{case_number}_R{n:02d}_{condition_name}`
- `compare_cases(db, base_case_id, compare_case_id) -> CaseCompareResult`: deep-diffs active template settings JSON, flat map condition values, and assembly `analysis_result.parts` sets
- `get_axes_glb(db, case_id, run_id) -> bytes`: resolves Run → Condition → Assembly → `viewer_service.build_axes_glb()`; raises 400 on ValueError
- `get_diff(run_id_a, run_id_b, db)` → `DiffResult`
- `enrich_case_response(db, case)` — populates `parent_case_number` + `parent_case_name` when `parent_case_id` is set
- Permission check: `resource.created_by == current_user.id OR current_user.is_admin`

**API Endpoints** (`app/api/v1/configurations.py`):

| Method | Path | Description |
|---|---|---|
| `GET` | `/maps/` | List all condition maps |
| `POST` | `/maps/` | Create condition map |
| `GET` | `/maps/{map_id}` | Get map (includes condition_count) |
| `PATCH` | `/maps/{map_id}` | Update map name/description |
| `DELETE` | `/maps/{map_id}` | Delete map + cascade conditions |
| `GET` | `/maps/{map_id}/conditions/` | List conditions in map |
| `POST` | `/maps/{map_id}/conditions/` | Create condition (includes ride_height, yaw_config) |
| `GET` | `/maps/{map_id}/conditions/{cid}` | Get condition |
| `PATCH` | `/maps/{map_id}/conditions/{cid}` | Update condition |
| `DELETE` | `/maps/{map_id}/conditions/{cid}` | Delete condition |
| `GET` | `/cases/` | List all cases |
| `POST` | `/cases/` | Create case (template_id + assembly_id required) |
| `GET` | `/cases/{id}` | Get case with run_count, parent_case_number/name |
| `PATCH` | `/cases/{id}` | Update name/description/template_id/assembly_id/map_id |
| `DELETE` | `/cases/{id}` | Delete case + cascade |
| `GET` | `/cases/{id}/compare?with={id2}` | Compare two cases: template settings diff, map conditions diff, assembly parts diff |
| `GET` | `/cases/{id}/runs/` | List runs |
| `POST` | `/cases/{id}/runs/` | Create run (condition_id + optional comment; auto-formats name) |
| `POST` | `/cases/{id}/runs/{rid}/generate?geometry_only=false` | Trigger XML generation; `geometry_only=true` reuses parent Run's XML and swaps STL only |
| `PATCH` | `/cases/{id}/runs/{rid}` | Update run (set `geometry_override_id`) |
| `DELETE` | `/cases/{id}/runs/{rid}` | Delete a single Run + output directory |
| `POST` | `/cases/{id}/runs/{rid}/reset` | Reset Run to pending (clears xml/stl/error, deletes output dir) |
| `GET` | `/cases/{id}/runs/{rid}/download` | Download generated XML |
| `GET` | `/cases/{id}/runs/{rid}/download-stl` | Download input STL used for XML generation |
| `GET` | `/cases/{id}/runs/{rid}/axes-glb` | On-demand axis-visualisation GLB |
| `POST` | `/cases/{id}/duplicate` | Duplicate a Case; sets `parent_case_id = source_case_id` |
| `GET` | `/runs/diff?a={rid}&b={rid}` | Diff two runs' settings |

**API Endpoints** (`app/api/v1/systems.py`):

| Method | Path | Description |
|---|---|---|
| `GET` | `/systems/` | List all systems |
| `GET` | `/systems/{id}` | Get system (transform_snapshot parsed from JSON) |
| `DELETE` | `/systems/{id}` | Delete system (result geometry DB row removed; file kept) |
| `GET` | `/systems/{id}/landmarks-glb` | GLB with before/after landmark spheres |

**`POST /geometries/{id}/transform`** (in `app/api/v1/geometries.py`):
- Body: `TransformRequest` — name, condition_id?, ride_height, rh_template, yaw_angle_deg, yaw_config
- Validates geometry `status == "ready"` and `analysis_result` exists
- Calls `ride_height_service.compute_transform()` → snapshot dict
- Calls `ride_height_service.create_system_and_geometry()` → `(System, Geometry)` in background
- Returns `{system_id, geometry_id, geometry_name, geometry_status, transform_snapshot}`

**Migrations**:
- `4a08074381f4_add_condition_maps_conditions_refactor_` — ConditionMap + Condition tables; Run.condition_id replaces configuration_id
- `8949ff1689b0_add_ride_height_yaw_to_conditions_and_` — systems table; `ride_height_json` + `yaw_config_json` on conditions
- `ff0265eeeb01_add_stl_path_to_runs` — adds nullable `stl_path` Text column to `runs`
- `0601bb149381_add_geometry_override_id_to_runs` — adds nullable `geometry_override_id` FK column to `runs` (ondelete SET NULL); uses `batch_alter_table` for SQLite
- `100503ac21a7_add_parent_case_id_to_cases` — adds nullable `parent_case_id` self-FK to `cases` (ondelete SET NULL); uses `batch_alter_table` for SQLite

### Template Settings Extensions (`app/schemas/template_settings.py`)

`TemplateSettings` has **6 top-level fields** (5 sections + `porous_coefficients`):

```python
class TemplateSettings(BaseModel):
    setup_option:          SetupOption
    simulation_parameter:  SimulationParameter
    setup:                 Setup = Field(default_factory=_aero_setup)  # NOT Setup()
    output:                OutputSettings
    target_names:          TargetNames
    porous_coefficients:   list[PorousMedia] = []
```

**`_aero_setup()` — aero default meshing setup** (defined before `TemplateSettings`):
```python
def _aero_setup() -> Setup:
    """Default meshing setup for aero/fan_noise: 5 box zones + 2 offset layers.
    Used as default_factory for TemplateSettings.setup.
    To change defaults: update this function and run npm run generate-api."""
    _coarse = 0.192  # default coarsest_voxel_size
    return Setup(meshing=MeshingSetup(
        box_refinement={
            "Box_RL1": BoxRefinement(level=1, box=[-1.0, 3.0, -1.0, 1.0, -0.2, 1.5]),
            "Box_RL2": BoxRefinement(level=2, box=[-0.5, 1.5, -0.75, 0.75, -0.2, 1.0]),
            "Box_RL3": BoxRefinement(level=3, box=[-0.3, 1.0, -0.5, 0.5, -0.2, 0.75]),
            "Box_RL4": BoxRefinement(level=4, box=[-0.2, 0.6, -0.3, 0.3, -0.2, 0.5]),
            "Box_RL5": BoxRefinement(level=5, box=[-0.1, 0.3, -0.15, 0.15, -0.2, 0.25]),
        },
        offset_refinement={
            "Body_Offset_ALL_RL7": OffsetRefinement(level=7, normal_distance=0.012, parts=[]),
            "Body_Offset_ALL_RL6": OffsetRefinement(level=6, normal_distance=0.036, parts=[]),
        },
    ))
```

**`MeshingSetup`** key fields:
```python
class MeshingSetup(BaseModel):
    box_refinement: dict[str, BoxRefinement]                   # BoxRefinement.mode: "vehicle_bbox_factors" (×dims) | "user_defined" (abs m)
    part_box_refinement: dict[str, BoxRefinement]              # legacy (unused in current presets)
    part_based_box_refinement: dict[str, BoxRefinementAroundParts]  # bbox derived from part extents
    offset_refinement: dict[str, OffsetRefinement]
    custom_refinement: dict[str, CustomRefinement]             # GHN only
```

**`BoxRefinementAroundParts`** — box defined by part extents + per-axis offsets:
```python
class BoxRefinementAroundParts(BaseModel):
    level: int
    parts: list[str]
    # per-coefficient behaviour is controlled globally via MeshingOption.box_refinement_porous_per_coefficient
    # (False = union bbox of all matched parts → 1 BoxInstance per entry;
    #  True  = one BoxInstance per porous_coefficients entry, name suffix: {entry_name}_{coeff.part_name})
    offset_xmin: float = 0.0   # m — absolute distance beyond matched parts bbox in -X (0 = tight fit, matches old setup script)
    offset_xmax: float = 0.0   # m — absolute distance beyond matched parts bbox in +X
    offset_ymin: float = 0.0   # m — absolute distance beyond matched parts bbox in -Y
    offset_ymax: float = 0.0   # m — absolute distance beyond matched parts bbox in +Y
    offset_zmin: float = 0.0   # m — absolute distance beyond matched parts bbox in -Z
    offset_zmax: float = 0.0   # m — absolute distance beyond matched parts bbox in +Z
```


**`RideHeightTemplateConfig`** (new — template-level "how" config for ride height transforms):
```python
class RideHeightTemplateConfig(BaseModel):
    reference_parts: list[str] = []         # part-name patterns used to derive wheel positions for transform
    adjust_body_wheel_separately: bool = False  # True = body and wheels transformed independently
    use_original_wheel_position: bool = False   # True = restore wheels to original Z when separately=True
```

**`SetupOption`** now includes `ride_height: RideHeightTemplateConfig = Field(default_factory=RideHeightTemplateConfig)`.

**`SetupOption.compute`** (ComputeOption):
```python
class ComputeOption(BaseModel):
    pass  # All flags auto-derived in compute_engine:
          #   rotate_wheels / moving_ground → from ground_mode
          #   porous_media → from bool(template_settings.porous_coefficients)
          #   turbulence_generator → from tg_cfg.enable_ground_tg | enable_body_tg
          # adjust_ride_height removed — ride height is triggered per-condition in CreateCaseFromBuilderModal
```

**`SimulationParameter`** key fields:
```python
coarsest_voxel_size: float = 0.192  # m (ext aero); Compute Engine uses this directly
number_of_resolution: int = 7
start_averaging_time: float = 1.5   # seconds
avg_window_size: float = 0.3        # seconds
yaw_angle: float = 0.0              # Template default (Config can override)
```

**`OutputSettings`** (full structure in `app/schemas/template_settings.py`):
```python
class OutputSettings(BaseModel):
    full_data:          FullDataOutputConfig
    partial_surfaces:   list[PartialSurfaceOutputConfig]
    partial_volumes:    list[PartialVolumeOutputConfig]
    aero_coefficients:  AeroCoefficientsConfig
    section_cuts:       list[SectionCutConfig]    # GHN primarily
    probe_files:        list[ProbeFileConfig]     # optional for any sim type
```

**`ProbeFileConfig`**:
```python
class ProbePointConfig(BaseModel):
    x_pos: float; y_pos: float; z_pos: float; description: str = ""

class ProbeFileOutputVariables(BaseModel):
    # All Optional[bool] — None = use solver default
    pressure: bool | None = None
    cp: bool | None = None
    velocity: bool | None = None
    time_avg_pressure: bool | None = None
    wall_shear_stress: bool | None = None  # surface probes only
    # ... 18 fields total

class ProbeFileConfig(BaseModel):
    name: str = "probe"              # also used as CSV filename
    probe_type: str = "volume"       # "volume" | "surface"
    radius: float = 0.0              # fictitious sphere radius for averaging
    output_frequency: float = 1.0   # coarsest iterations between outputs
    output_start_iteration: int = 0
    scientific_notation: bool = True
    output_precision: int = 7
    output_variables: ProbeFileOutputVariables
    points: list[ProbePointConfig]   # probe locations; generates CSV at XML build time
```

**`TargetNames`** key fields:
```python
wheel: list[str] = []      # part-name patterns for wheel classification
rim: list[str] = []        # part-name patterns for rim (PCA axis) detection
baffle: list[str] = []     # part-name patterns for baffle parts
wheel_tire_fr_lh: str = ""  # individual tyre PID — belt auto-position & roughness
wheel_tire_fr_rh: str = ""
wheel_tire_rr_lh: str = ""
wheel_tire_rr_rh: str = ""
overset_fr_lh: str = ""     # OSM region PID
overset_fr_rh: str = ""
overset_rr_lh: str = ""
overset_rr_rh: str = ""
windtunnel: list[str] = []  # passive parts — excluded from force calc + offset refinement
tire_roughness: float = 0.0
```

**Note**: `porous` and `car_bounding_box` fields have been removed from `TargetNames`.
- Porous part matching now uses `porous_coefficients[].part_name` (exact match) directly — no pattern filter needed.
- `car_bounding_box` was unused and has been deleted.

### Compute Engine Extensions (`app/services/compute_engine.py`)

Key functions for XML assembly:

```python
def assemble_ufx_solver_deck(
    template_settings: TemplateSettings,
    analysis_result: dict,
    sim_type: str,
    inflow_velocity: float,
    yaw_angle: float,
    source_file: str | None = None,
    source_files: list[str] | None = None,
    pca_axes: dict | None = None,   # from extract_pca_axes()
) -> UfxSolverDeck:
    """Top-level orchestrator — assembles all 7 UfxSolverDeck sections.
    Multi-STL: if source_files provided, sets geometry.source_files list.
    Probe instances: builds ProbeFileInstance per probe_files config.
    Partial surface/volume: builds instances dynamically from template output config.
    pca_axes: {"porous": {part_name: ndarray}, "rim": {part_name: ndarray}} from extract_pca_axes().
    """

def extract_pca_axes(
    stl_paths: list[Path],
    porous_patterns: list[str],
    rim_patterns: list[str],
) -> dict:
    """Re-scan ASCII STL files to collect vertices for parts matching the given patterns.
    Binary STL files are skipped (graceful fallback to bbox axis).
    Returns: {"porous": {part_name: np.ndarray[N,3]}, "rim": {part_name: np.ndarray[N,3]}}
    Memory-efficient: only collects vertices for matching parts.
    Called from configuration_service._generate_xml_task() before assemble_ufx_solver_deck().
    """

def _find_rim_vertices_for_wheel(
    wheel_info: dict,
    rim_vertices_map: dict[str, np.ndarray],
) -> np.ndarray | None:
    """Returns vertices of the rim part whose centroid is closest to the wheel centroid.
    Used to pass the correct rim vertices to compute_wheel_kinematics() per wheel.
    """

def build_probe_csv_files(template_settings: TemplateSettings) -> dict[str, bytes]:
    """Returns {filename: csv_bytes} for each probe_file_instance.
    CSV format: x_pos;y_pos;z_pos;description (no header).
    Called by configuration_service after XML generation — CSVs saved beside output.xml.
    """

def resolve_compute_flags(template_flags: ComputeOption, overrides: ComputeOverrides) -> ComputeOption:
    """Apply Config overrides to Template defaults with dependency rules."""

def compute_dt(coarsest_mesh_size: float, mach_factor: float, temperature_k: float) -> float:
    """LBM time step: dt = coarsest_mesh_size * mach_factor / (Cs * sqrt(3))
    where Cs = sqrt(gamma * R_specific * T_kelvin) = sqrt(1.4 * 287.05 * T_k).
    IMPORTANT: formula uses speed of sound, NOT inflow_velocity.
    Verified against AUR_v1.2_EXT_1.99_corrected.xml (3870 iter, dx=0.192, mach=2, T=293.15K).
    """

def compute_domain_bbox(vehicle_bbox: dict, multipliers: list[float]) -> dict:
    """Apply 6 relative multipliers to vehicle bbox → absolute domain bounding box."""

def classify_wheels(analysis_result: dict, target_names: TargetNames) -> dict:
    """Sort wheel parts into FR_LH/FR_RH/RR_LH/RR_RH by centroid vs COG."""

def compute_wheel_kinematics(wheel_info: dict, inflow_velocity: float, rim_vertices: np.ndarray | None = None) -> dict:
    """PCA on rim vertices (vt[2] = min variance = rotation axis) → axis; rpm = inflow_velocity / (2π×radius) × 60.
    Falls back to Y-axis (0,1,0) when rim_vertices is None."""

def compute_porous_axis(part_info: dict, vertices: np.ndarray | None = None) -> dict:
    """PCA on porous part vertices: vt[2] (min variance = face normal = flow direction) → PorousAxis xyz.
    Falls back to bbox thinnest-axis when vertices is None."""

def _build_belt5_wall_instances(
    wheel_kin_map, belt5_cfg, vbbox, velocity_dir,
    FluidBCMoving, XYZDir, WallInstance,
    DomainPartInstance, BoundingRange,
) -> tuple[list, float, list]:
    """Returns (wall_instances, center_xmin, domain_part_instances).
    Builds 5 moving WallInstances (FR_LH/FR_RH/RR_LH/RR_RH + Belt_Center) and
    corresponding DomainPartInstances (location="z_min", export_mesh=True) with
    computed bounding_range per belt from wheel kinematics and belt5 config.
    """
```

**Ground BC and `domain_part_instances` assembly** (in `assemble_ufx_solver_deck`):

Ground wall BC logic:
```
ground_mode == "full_moving":
  → WallInstance(name="uFX_moving_ground",       parts=["uFX_domain_z_min"], type="moving")

ground_mode != "full_moving" (all other modes):
  → WallInstance(name="uFX_slip_ground",          parts=["uFX_domain_z_min"], type="slip")  [always]

  BL suction ON (bl_suction.apply=True):
    ground_mode == "rotating_belt_1":
      → WallInstance(name="uFX_moving_ground_patch", parts=["uFX_ground"], type="moving")  [belt speed]
    ground_mode == "rotating_belt_5" or "static":
      → WallInstance(name="uFX_static_ground",       parts=["uFX_ground"], type="static")
```

Belt DomainPartInstances (`belt_dpis`):
```
ground_mode == "rotating_belt_5":
  → _build_belt5_wall_instances() returns belt_dpis:
      Belt_Wheel_FR_LH, Belt_Wheel_FR_RH, Belt_Wheel_RR_LH, Belt_Wheel_RR_RH  (z_min, export_mesh=True)
      Belt_Center  (z_min, export_mesh=True, x=[center_xmin, center_xmin+bsc.x], y=[-bsc.y/2, bsc.y/2])

ground_mode == "rotating_belt_1":
  → belt_dpis = [DomainPartInstance(name="Belt", location="z_min", export_mesh=True,
        bounding_range=BoundingRange(x_min=no_slip_xmin, x_max=vbbox["x_max"],
            y_min=-b1.belt_size.y/2, y_max=b1.belt_size.y/2))]
```

`uFX_ground` DomainPartInstance (BL suction patch):
```
Condition: ground_mode != "full_moving" AND bl_suction.apply=True AND no_slip_xmin is not None
  ground_patch_active=True  → y_min/y_max = floor_dims (vehicle body bbox ±25% width)
  ground_patch_active=False → y_min/y_max = full domain_bb width

DomainPartInstance(name="uFX_ground", location="z_min", export_mesh=False,
    bounding_range=BoundingRange(x_min=no_slip_xmin, x_max=floor_dims["x_max"],
        y_min=gnd_y_min, y_max=gnd_y_max))
```

Final assembly:
```python
domain_part_instances = belt_dpis[:] + ([ground_dpi] if ground_dpi else [])
domain_part = DomainPart(export_mesh=bool(domain_part_instances), domain_part_instances=domain_part_instances)
```

`passive_parts` additions (beyond windtunnel + wheel belt forces):
```
BL suction ON (non-full_moving):  passive_parts.append("uFX_ground")
rotating_belt_5:                   passive_parts.append("Belt_Center")
```

> **Official Ultrafluid docs basis**: "BL suction entries can be replaced by setting the domain ground to a 'slip' ground and adding a `domain_part_instance` with 'static' BC starting at the suction position. This static patch needs to be excluded from the force coefficient calculation by making it a passive part."

**Partial surface/volume build logic** (in `assemble_ufx_solver_deck`):
- `ps_instances` loop: filters `all_part_names` by `include_parts` / `exclude_parts` patterns; auto-excludes baffles when `baffle_export_option` is set.
- `pv_instances` loop: builds `BoundingBox` per mode — `from_meshing_box` (finds matching box in template meshing setup), `around_parts` (union of part bboxes from analysis_result), `user_defined` (literal bbox list).
- `probe_instances` loop: builds `ProbeFileInstance` with `source_file = f"{name}.csv"` (relative, written by `build_probe_csv_files`).

### Compute Flag Dependency Rules

```
All flags are auto-derived in compute_engine (ComputeOption is now empty):

rotate_wheels / moving_ground:
  → derived from ground_mode: static → False, otherwise → True

porous_media:
  → derived from bool(template_settings.porous_coefficients)
  → empty list → no porous sources

turbulence_generator:
  → derived from tg_cfg.enable_ground_tg or tg_cfg.enable_body_tg
  → both off → no TG instances

adjust_ride_height:
  → NOT a compute flag anymore — triggered per-condition in CreateCaseFromBuilderModal
  → uses Template's RideHeightTemplateConfig ("how") + Condition's RideHeightConditionConfig ("targets")
```

### Excel Settings Classification (from AUR_v1.2_EXT.xlsx / CX1_v1.2_GHN.xlsx)

| Excel Sheet | Setting | Layer |
|---|---|---|
| General | `DATA_FOLDER`, `list_stl_files`, `simulationName` | VAM managed |
| General | `inflow_velocity`, `yaw_angle_vehicle`, `ground_height` | **Configuration** |
| General | `simulation_time`, `output_start_time`, `output_interval_time` | Config (optional override) |
| General | `opt_moving_floor`, `osm_wheels`, `activate_body_tg` | Config `compute_overrides` |
| General | `opt_belt_system`, `wall_model`, `solution_type`, `output_format` | **Template** |
| General | `density`, `dynamic_viscosity`, `temperature` | **Template** |
| Wheels_baffles | `WheelPartsNames`, `RimPartsNames`, `BafflePartsName` | Template `target_names` |
| Wheels_baffles | `WheelTireParts_FR/RR_LH/RH` | Template `target_names.wheel_tire_*` |
| Wheels_baffles | `OversetMeshPartsName_FR/RR_*` | Template `target_names.overset_*` |
| Wheels_baffles | `windtunnel_parts` | Template `target_names.windtunnel` |
| Belts | `belt_size_*`, `belt_center_position_*` | Template `setup.boundary_condition_input` |
| Heat_exchangers | part `name` | Template `target_names.porous` |
| Heat_exchangers | `coeffs_inertia`, `coeffs_viscous` | **Configuration** `porous_coefficients` |
| Ride_Height | `front/rear_wheel_axis_RH` | Configuration `ride_height` (target values) |
| Ride_Height | `adjust_body_wheel_separately`, `use_original_wheel_position`, `reference_parts` | Template `setup_option.ride_height` (how-to config) |
| Mesh_Control | `triangleSplitting`, `coarsest_voxel_size`, `transitionLayers` | **Template** |
| Additional_offset_refinement | all rows | Template `setup.meshing.offset_refinement` |
| Custom_refinement | all rows (GHN only) | Template `setup.meshing.custom_refinement` |
| Output sheets (all) | all output variable flags | **Template** |

### Frontend Components

- `src/components/maps/MapList.tsx` — Condition Maps table; per-map drawer opens `ConditionSection`; shows ride height badge per condition row + edit button
- `src/components/maps/MapCreateModal.tsx` — create map (name + description)
- `src/components/maps/ConditionFormModal.tsx` — create/edit condition; two Accordions:
  - **Ride Height Transform**: enabled switch → target front/rear wheel axis heights → optional per-wheel RH targets (only active when Template's `adjust_body_wheel_separately=True`; note shown in UI)
  - **Yaw Center Configuration**: `center_mode` Select (`wheel_center` / `user_input`) → center X/Y inputs when `user_input`
- `src/components/cases/CaseList.tsx` — folder-grouped table; row click navigates to `/cases/{id}` (dedicated page); **Compare mode**: toggle activates row-selection mode (up to 2 rows), "Compare" → `CaseCompareModal`; Duplicate button → `CaseDuplicateModal`
- `src/components/cases/CaseDetailPage.tsx` — dedicated page at `/cases/:caseId`; 4 tabs:
  - **Information** tab: case number (read-only), editable Name/Description/Template/Assembly/Map; Parent Case display (badge + link when `parent_case_id` exists)
  - **Runs** tab: create-run form (Condition Select + Comment TextInput + auto-name preview + "+ New Run"); run table with per-run actions: Generate (with "Geom only" checkbox when `parent_case_id` exists) / Download XML / Download STL / Reset (→ pending) / Delete
  - **Compare** tab: "Compare with" Case Select (pre-filled with parent case); Template Settings diff table (yellow-highlighted rows); Map Conditions diff table; Assembly Parts three-column view (Added green / Removed red / Common gray)
  - **Viewer** tab: placeholder ("coming soon")
- `src/components/cases/CaseCreateModal.tsx` — Two-tab modal: **New Case** (Template + Assembly + optional Map + `withRuns` Switch) / **Copy from Case** (source Case select + auto-fill name → `casesApi.duplicate()`)
- `src/components/cases/CaseDuplicateModal.tsx` — standalone duplicate form; newly created case has `parent_case_id` automatically set to source case
- `src/components/cases/CaseCompareModal.tsx` — 2-column `Grid` showing `CaseColumn` per selected case; each column: case info badges + scrollable Run list table (`run_number` / `condition_name` / velocity / yaw / status badge)
- `src/components/cases/CreateCaseFromBuilderModal.tsx` — Modal opened from Template Builder to bulk-create a Case + Runs from a Condition Map; auto-generates case name; for `ride_height.enabled=True` conditions, fires `transformApi.transform()` using Template's `RideHeightTemplateConfig` then patches `Run.geometry_override_id` via `runsApi.update()`; navigates to `/cases` on success
- `src/components/runs/RunList.tsx` — legacy run list used in old Drawer (kept for reference); main run UI is now in `CaseDetailPage.tsx` Runs tab
- `src/components/runs/DiffView.tsx` — side-by-side or diff-list view of two Run settings
- Navigation: `AppShell.tsx` adds `Condition Maps` (IconList) and `Cases` (IconCar)
- Routes: `/cases` → `CaseList`; `/cases/:caseId` → `CaseDetailPage`

**`TemplateSettingsForm.tsx`** (used inside Create/Edit/View modals):

Form state is managed by `src/hooks/useTemplateSettingsForm.ts` (`useTemplateSettingsForm` hook). Key interfaces:
```typescript
interface OffsetRefinementFormItem          { name, level, normal_distance, parts: string[] }  // TagsInput
interface CustomRefinementFormItem          { name, level, parts: string[] }                     // TagsInput
interface PorousCoeffFormItem               { part_name, inertial_resistance, viscous_resistance }
interface TriangleSplittingInstanceFormItem { name, active, max_absolute_edge_length, max_relative_edge_length, parts: string[] }  // TagsInput
interface PartialSurfaceFormItem    { name, output_start_time, output_interval, file_format, include_parts: string[], exclude_parts: string[], baffle_export_option, output_variables, ... }
interface PartialVolumeFormItem     { name, bbox_mode, bbox_source_box_name, bbox, bbox_source_parts: string[], bbox_offset_xmin/xmax/ymin/ymax/zmin/zmax, output_variables, ... }
interface SectionCutFormItem        { name, output_start_time, output_interval, file_format, axis_x/y/z, point_x/y/z, bbox, output_variables, ... }
interface ProbeFileFormItem         { name, probe_type, radius, output_frequency, output_variables, points: ProbePointFormItem[] }
interface ProbePointFormItem        { x_pos, y_pos, z_pos, description }
```

**Props:**
- `form: UseFormReturnType<FormValues>` — Mantine form instance
- `simType: string` — `"aero"` / `"ghn"` / `"fan_noise"`
- `generalContent?: ReactNode` — when provided, a **General** tab is prepended as the first tab (used by Create/Version/View modals to embed Name/Description/Application/comment fields)
- `readOnly?: boolean` — when `true`, wraps each `Tabs.Panel` content in `<fieldset disabled>` so all inputs are disabled; `Tabs.List` (tab buttons) is **not** wrapped and remains clickable

`TemplateSettingsForm.tsx` tab sections:

| Tab | Contents |
|---|---|
| General *(conditional)* | Rendered from `generalContent` prop — Name, Description, Application, Version comment |
| Simulation Run Parameters | **Accordion**: Run Time (run time, averaging, mach factor, yaw, ramp-up) · Physical Properties (velocity, temp, density, viscosity, gas constant) · Options (°C switch, FP mode) |
| Meshing | **Accordion**: General (coarsest voxel, num RL, transition layers) · Triangle Splitting (global ON/OFF switch → when ON: max rel/abs edge + per-part instances) · Box Refinement (porous switch + dynamic list; each row: name/level + `SegmentedControl` for `box_type`: vehicle_bbox_factors/around_parts/user_defined) · Offset Refinement (dynamic list, "Apply body defaults") · Custom Refinement (dynamic list) |
| Boundary Conditions | **Accordion**: Flow Domain Configuration (ground height definition + domain bbox factors) · Ground Condition (ground mode select + wheel/rim part names + OSM parts + BL suction; aero has Select, non-aero has simple BL suction only) · Belt Configuration (aero only; isBelt5: belt settings + **required** tire part names tn_wt_*; isBelt1: belt size) · Turbulence Generator (aero only; enable switches + per-TG: `intensity` + `length scale (m)` [placeholder="auto", auto = 4 × RL6 voxel size; `num_eddies` hardcoded 800, not in UI]) · Porous Media Coefficients (dynamic list, template defaults) |
| *(Belt size label convention)* | x = vehicle longitudinal = **Length (x)**; y = vehicle lateral = **Width (y)**. Applied to all 3 belt size inputs (wheel belt, center belt, belt_1). |
| Output | **Accordion**: Full Data Output (time fields, format, merge, coarsening [Coarsest RL max=number_of_resolution, Coarsen by SegmentedControl "1"|"2"], bbox select/coords, output vars 24+15 checkboxes) · Aero Coefficients (aero only; ref area/length auto, along-axis) · Partial Surfaces · Partial Volumes (coarsening same SegmentedControl) · Section Cuts · Probe Files |
| Part Specification | `tn_baffle` + `tn_windtunnel` only |
| Ride Height | `rh_reference_parts` TagsInput · `rh_adjust_body_wheel_separately` Switch · `rh_use_original_wheel_position` Switch (disabled when `adjust_body_wheel_separately=false`) |

**Key notes:**
- Modal `size="95%"` for all 3 create/edit modals
- `merge_output` default is `false` for all output config classes (FullData, PartialSurface, PartialVolume, SectionCut) — both backend Pydantic and frontend helpers
- `FORM_VALIDATE` exported from `useTemplateSettingsForm.ts` — validates `tn_wt_fr/rr_lh/rh` as required when `ground_mode === "rotating_belt_5"`
- All create/version modals import and pass `validate: FORM_VALIDATE` to `useForm()`
- `tn_wheel` / `tn_rim` moved to BC tab > Ground Condition accordion (aero only)
- `tn_wt_*` tire parts moved to BC tab > Belt Configuration accordion (isBelt5, marked `required`)
- `tn_osm_*` OSM parts moved to BC tab > Ground Condition, shown when `overset_wheels` is ON
- Ride Height tab: `rh_reference_parts` (TagsInput) + `rh_adjust_body_wheel_separately` + `rh_use_original_wheel_position` — maps to `setup_option.ride_height` in Template settings
- **Part name list fields use `TagsInput`** (not `TextInput`) — `tn_wheel`, `tn_rim`, `tn_baffle`, `tn_windtunnel`, `offset_refinements[].parts`, `custom_refinements[].parts`, `box_refinements[].parts` (around_parts mode), `triangle_splitting_instances[].parts`, `partial_surfaces[].include_parts/exclude_parts`, `partial_volumes[].bbox_source_parts`. All backed by `string[]` — no `joinList`/`splitList` needed.
- **Part name pattern matching** (`compute_engine._matches_pattern`): `*` あり → `fnmatch` glob (`Body_*` = starts-with, `*_Body_*` = contains, `*_Body` = ends-with); `*` なし → `startswith OR endswith`; case-insensitive。`offset_refinement[]`, `custom_refinement[]`, `triangle_splitting_instances[]` の `parts` は `part_info` に対して展開済み実パーツ名を XML に書き出す（B案）。

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

## Phase 2A: 3D Viewer / Template Builder — Implementation Details (Complete)

### Overview

A 3D viewer for pre-processing (STL geometry + Template overlay) accessible at `/template-builder`. Backend converts ASCII STL to decimated GLB and caches it. Frontend renders with React Three Fiber.

### Geometry Status Flow

```
upload / link
      ↓
  pending         → yellow badge "Pending"
      ↓
  analyzing       → blue badge "Analyzing…"
      ↓
ready-decimating  → violet badge "Building 3D…"  ← GLB pre-generation (skipped when decimation_ratio >= 1.0)
      ↓
  ready           → green badge "Complete"
 (error)          → red badge "Failed"
```

### Backend

**`backend/app/services/ride_height_service.py`** (new — Phase 2A-5)
- `compute_transform(analysis_result, rh_cfg, yaw_angle_deg, yaw_cfg) -> dict` — pure math, no file I/O:
  - Derives `front_x/z_orig`, `rear_x/z_orig` from `part_info` centroids matching `wheel` patterns
  - Computes `wheelbase`, `pitch_angle_orig/target`, `delta_pitch`, `tz` (Z-translation)
  - Yaw center: midpoint of FR/RR wheel axes (mode=`wheel_center`) or user XY (mode=`user_input`)
  - **Transform order**: Yaw (Z-axis) → Pitch (Y-axis, Rodrigues) → Z-translate
  - Returns `transform_snapshot` dict with keys:
    - `transform`: `{yaw_angle_deg, yaw_center_xy, pitch_angle_deg, rotation_pivot, translation}`
    - `wheel_transforms`: per-corner `{translation}` or `null` (when `adjust_body_wheel_separately=False`)
    - `landmarks`: `{front_wheel_center, rear_wheel_center, wheelbase_center, vehicle_bbox_z_min}` — each has `before`/`after`
    - `targets`: `{front_wheel_axis_rh, rear_wheel_axis_rh, yaw_angle_deg}`
    - `verification`: `{front_wheel_z_actual, front_wheel_z_target, front_error_m, rear_...}`
- `_rodrigues_y(vertices, angle_deg, pivot)` — Y-axis rotation matrix (Rodrigues formula, pure NumPy)
- `_rotate_z(vertices, angle_deg, center_xy)` — Z-axis rotation
- `transform_vertices(vertices, tr) -> np.ndarray` — apply yaw→pitch→translate
- `_transform_stl_buffered(source_path, out_path, body_transform, wheel_part_transforms, wheel_patterns)` — streaming ASCII STL transform; applies per-part transforms when `wheel_part_transforms` is set; other parts use `body_transform`
- `create_system_and_geometry(db, source_geometry, transform_snapshot, name, current_user, condition_id, background_tasks) -> (System, Geometry)` — creates result `Geometry` row (`is_linked=False`, status=`pending`), creates `System` record, triggers `run_analysis()` background task
- `adjust_body_wheel_separately` branch: body uses body pitch+translate; each wheel uses its own transform so that wheels land at `target_front/rear_wheel_rh` or are restored to original position (`use_original_wheel_position=True`)

**`backend/app/services/viewer_service.py`** — `build_landmarks_glb(transform_snapshot: dict) -> bytes` (Phase 2A-5 addition)
- Before: grey translucent spheres `(0.5, 0.5, 0.5, 0.5)` at original positions
- After front: red `(1.0, 0.15, 0.15, 1.0)` · After rear: blue `(0.15, 0.4, 1.0, 1.0)` · After wheelbase: white
- Uses `_make_sphere_solid()` + `GLBExporter.export()`

**`backend/scripts/test_ride_height.py`** (new)
- CLI: `uv run python scripts/test_ride_height.py [<stl_path>] [front_rh] [rear_rh] [yaw_deg]`
- Runs `analyze_stl()` + `compute_transform()`, prints landmark table + verification errors, saves `test_ride_height_result.json`

---

**`backend/app/services/viewer_service.py`** (new)
- `DEFAULT_RATIO: float = 0.05` — global default (keep 5% of faces)
- `build_viewer_glb(geometry, ratio=DEFAULT_RATIO) -> bytes`: (1) `STLReader.read(stl_path)` (ASCII+Binary auto-detect) → (2) `ProcessPoolExecutor` parallel `_decimate_worker` (each part independently with same `ratio`) → (3) `GLBExporter.export(valid_solids, cache_path)` → read bytes → return. **No trimesh or fast-simplification dependency.**
- `get_cached_glb(geometry_id, ratio) -> bytes | None`: returns cached GLB bytes if cache file exists
- `invalidate_cache(geometry_id)`: removes all cache files for a geometry via glob `{id}_*.glb`
- Cache path: `{viewer_cache_dir}/{geometry_id}_{ratio:.3f}.glb` (e.g. `abc123_0.050.glb`)
- **No `fast-simplification` or `trimesh` dependency** — `stl_decimator.QEMDecimator` is the sole decimation engine (pure Python + NumPy)
- `build_axes_glb(template_settings, analysis_result, stl_paths, inflow_velocity) -> bytes` — on-demand GLB of wheel/porous axes (no disk cache — payload is small):
  - `_rotation_matrix_to_direction(d)` — Rodrigues formula: 3×3 R that maps +Z → unit vector `d` (pure NumPy)
  - `_make_arrow_solid(name, origin, direction, length, shaft_radius, n_seg=16) -> Solid` — cylinder shaft + cone tip, built along +Z then rotated to `direction` via Rodrigues
  - `_make_sphere_solid(name, center, radius) -> Solid` — UV sphere (lat/lon grid, pure NumPy)
  - Per wheel corner (`fr_lh / fr_rh / rr_lh / rr_rh`): coloured arrow + centre sphere
    - Colors: FR_LH=red, FR_RH=blue, RR_LH=orange, RR_RH=green
    - `arrow_len = radius * 0.80`, `shaft_r = arrow_len * 0.06`
  - Per porous part: purple arrow from part centroid in flow-axis direction
  - Raises `ValueError` if no wheel or porous geometry found
  - Uses `tempfile.NamedTemporaryFile` → `GLBExporter.export(solids, tmp, colors=colors)` → returns bytes, deletes temp file

**`backend/app/config.py`**: `viewer_cache_dir: Path = _BACKEND_DIR / "data" / "viewer_cache"`

**`backend/app/database.py`**: `settings.viewer_cache_dir.mkdir(parents=True, exist_ok=True)` on startup

**`backend/app/services/geometry_service.py`** — `run_analysis()` changes:
- Signature: `run_analysis(db, geometry_id, decimation_ratio: float = 0.05) -> None`
- After STL analysis succeeds → sets `status = "ready-decimating"` → commits
- If `decimation_ratio >= 1.0` → skips GLB build entirely, sets `status = "ready"` immediately
- Otherwise pre-generates GLB via `build_viewer_glb(geometry, ratio=decimation_ratio)` (blocking, runs in background task)
- Sets `status = "ready"` in `finally` block regardless of GLB success/failure
- `delete_geometry()` calls `invalidate_cache(geometry.id)` before DB delete; also performs `shutil.rmtree(upload_subdir)` on the geometry’s upload directory (with absolute/relative path resolution and safety guard against deleting `upload_dir` root); deletion failures are logged as `WARNING` rather than silently ignored

**`backend/app/api/v1/geometries.py`** — new endpoints:
| Method | Path | Description |
|---|---|---|
| `GET` | `/geometries/{id}/file` | Download original STL (`FileResponse`) |
| `GET` | `/geometries/{id}/glb?ratio=0.05` | Get decimated GLB — serves from cache, generates if missing |

- `ratio` query param: `float` 0.01–1.0 (default `0.05`); frontend requests with the geometry's stored ratio
- Upload endpoint: `decimation_ratio: float = Form(0.05)` — passed to `run_analysis()` background task
- Link endpoint: `data.decimation_ratio` passed to `run_analysis()` background task
- Returns `Response(content=glb_bytes, media_type="model/gltf-binary")`
- 400 if geometry `status != "ready"`

**`backend/app/api/v1/configurations.py`** — new Run endpoint:
| Method | Path | Description |
|---|---|---|
| `GET` | `/cases/{case_id}/runs/{run_id}/axes-glb` | On-demand axis-visualisation GLB — no cache, computed every request |

- Calls `configuration_service.get_axes_glb(db, case_id, run_id)` → `Response(content=bytes, media_type="model/gltf-binary")`
- 400 if `run.status != "ready"`

**`backend/app/services/configuration_service.py`** — `get_axes_glb(db, case_id, run_id) -> bytes`:
- Resolves Run → Case → active TemplateVersion → Assembly → `_merge_analysis_results()`
- Resolves `stl_paths` (same logic as `_generate_xml_task`)
- Calls `viewer_service.build_axes_glb(template_settings, merged_analysis, stl_paths, condition.inflow_velocity)`
- Raises 400 on `ValueError` (no geometry found)

### Frontend

**`src/stores/viewerStore.ts`** (Zustand)
```typescript
partStates: Record<string, { visible, color, opacity }>  // per-part 3D state
resetParts: () => void            // clears partStates entirely (all parts revert to defaults)
showAllParts: () => void          // sets visible:true for all entries in partStates, preserves color/opacity
searchQuery: string
searchMode: "include" | "exclude"
selectedAssemblyId: string | null  // setSelectedAssemblyId also resets glbLoaded=false
selectedTemplateId: string | null
ratio: 0.05                          // decimation ratio used for GLB fetch
// GLB load completion flag
glbLoaded: boolean                   // false on Assembly change; set true by GLBModel after first Mesh detected; reset to false by CameraFitter after fitting
setGlbLoaded: (v: boolean) => void
cameraProjection: "perspective" | "orthographic"  // toggled by floating toolbar; **default: "perspective"**
cameraPreset: string | null          // trigger: "top" | "front" | "side" | "iso" | "rear" | null
viewerTheme: "dark" | "light"
flatShading: boolean                 // default false; MeshStandardMaterial.flatShading
showEdges: boolean                   // default false; THREE.EdgesGeometry overlay
// Per-item overlay visibility — key absent = visible (true) by default
// Key naming: "domain_box" | "ground_plane" | "box_{name}" | "pv_{name}" | "sc_{name}" | "probe_{name}"
overlayVisibility: Record<string, boolean>;
setOverlayVisibility: (key: string, value: boolean) => void;
// Global master switch — hides ALL template overlays in SceneCanvas (OverlayObjects returns null)
overlaysAllVisible: boolean;          // default true
setOverlaysAllVisible: (v: boolean) => void;
// Legacy overlay object kept for axesGlbUrl / landmarksGlbUrl feature flags
overlays: ViewerOverlays  // wheelAxes, landmarks remain here
// NOTE: selectedCaseId, selectedRunId, axesGlbUrl, selectedConditionMapId,
//       selectedConditionId, landmarksGlbUrl removed — no longer used by Template Builder
//       (kept in store only if Case UI 3D step is implemented later)
// Part selection (click highlight)
selectedPartName: string | null      // name of currently selected part; highlighted yellow (#ffff00) in 3D
setSelectedPartName: (name: string | null) => void
// Fit camera to part
fitToTarget: { center: [number, number, number]; radius: number } | null
setFitToTarget: (t: ...) => void     // triggers FitToPartController inside Canvas
```

**`src/api/systems.ts`** (new)
- `systemsApi.list()`, `.get(id)`, `.delete(id)`, `.getLandmarksGlbUrl(id)` — fetch as blob → `createObjectURL()`
- `transformApi.transform(geometryId, data: TransformRequest) -> TransformResult`
- `TransformResult`: `{ system_id, geometry_id, geometry_name, geometry_status, transform_snapshot }`
- `RideHeightConditionConfig`, `RideHeightTemplateConfig`, `YawConditionConfig`, `TransformRequest` re-exported from `schema.d.ts`

**`src/api/geometries.ts`** — helpers:
- `geometriesApi.getGlbBlobUrl(id, ratio?)`: fetches GLB with auth header → `Blob` → `URL.createObjectURL()`, returns URL string. Caller must `URL.revokeObjectURL()` on cleanup. Default `ratio = 0.05`.
- `geometriesApi.upload(..., decimationRatio: number = 0.05)`: appends `decimation_ratio` to FormData before sending.
- `GeometryLinkRequest` type extended with `decimation_ratio?: number`.

**`src/api/configurations.ts`** — `runsApi` additions:
- `runsApi.update(caseId, runId, data: RunUpdate) -> Promise<RunResponse>`: `PATCH /cases/{id}/runs/{id}` — used to set `geometry_override_id` after ride-height transform
- `runsApi.getAxesGlbUrl(caseId, runId) -> Promise<string>`: fetches `/cases/{id}/runs/{id}/axes-glb` with auth header → `createObjectURL(blob)`. Caller must `revokeObjectURL()` on cleanup.

**`src/schemas/geometry.py`** — `GeometryLinkRequest`:
- Added `decimation_ratio: float = 0.05` — passed to `run_analysis()` background task

**`src/stores/jobs.ts`** — `JobStatus` now includes `"ready-decimating"`

**`src/hooks/useJobsPoller.ts`** — polls while `pending | analyzing | ready-decimating`

**`src/components/layout/JobsDrawer.tsx`** — `"ready-decimating"` status: violet, 85%, "Building 3D…"

**`src/components/geometries/GeometryList.tsx`** — violet badge + "Building 3D viewer cache..." text + refetchInterval triggers on `ready-decimating`

**`src/components/viewer/SceneCanvas.tsx`**
- Outer `<div>` wrapper containing `<Canvas>`; **no** ContextMenuPanel (removed)
- R3F `<Canvas>` + `<OrbitControls makeDefault>` + lights + `<Grid>`
- `<GLBModel>`: loads GLB via `useGLTF(blobUrl)` → three separate `useEffect` hooks:
  - **`[scene, flatShading]`** (dedicated): re-creates `new THREE.MeshStandardMaterial({ flatShading })` for every Mesh, copying `color/opacity/transparent/emissive` from the old material and calling `.dispose()` on it. This bypasses WebGL shader-program cache (which ignores `mat.flatShading = x; mat.needsUpdate = true` on already-compiled materials).
  - **`[scene, partStates, selectedPartName]`** (partStates): applies `visible/color/opacity/selectedPartName` highlight. Does NOT touch `flatShading` (delegated to the dedicated effect above).
  - **`[scene]`** (glbLoaded detection): `scene.traverse` checks `isMesh`; if any Mesh found → `setGlbLoaded(true)`. This replaces the old `setTimeout(300)` approach — CameraFitter now fires only after Mesh presence is confirmed.
  - `showEdges` adds/removes `THREE.LineSegments(EdgesGeometry)` children tagged `userData.isEdgeLine`; `selectedPartName === obj.name` → yellow highlight (`#ffff00`, emissive `#444400`)
- `<CameraFitter>`: no props; reads `glbLoaded` from store; two `useEffect` hooks:
  - **`[glbLoaded=false]`**: resets `fitted.current = false` so next Assembly triggers a new fit.
  - **`[glbLoaded=true]`**: calls `threeScene.updateMatrixWorld(true)` then `Box3.setFromObject(scene)` → `maxDim = max(x,y,z)`; iso position `(center + maxDim×1.2, center − maxDim×1.2, center + maxDim×0.6)` (≈8m standoff for 5m vehicle); sets `near/far`; sets `fitted.current = true`. **No `setTimeout`. Does NOT call `setGlbLoaded(false)` — Loading overlay stays hidden after fit.**
- **Loading overlay**: rendered outside `<Canvas>` inside the wrapper `<div>`; shown when `!glbLoaded && blobEntries.length > 0`; semi-transparent black background + Mantine `<Loader>` + "Loading 3D model…"; `pointerEvents: none` so OrbitControls still work if overlay lingers
- `<AxesGLBModel>`: loads axes GLB → renders as-is; shown when `axesGlbUrl && overlays.wheelAxes`
- `<LandmarksGLBModel>`: loads landmarks GLB → renders as-is; shown when `landmarksGlbUrl && overlays.landmarks`
- `<CameraPresetController>`: watches `cameraPreset` store value via **`useFrame` + `useViewerStore.getState()`** (not `useEffect`) — fires every render frame so button presses respond immediately even with heavy models; calls `threeScene.updateMatrixWorld(true)` before `Box3`; dist multiplier `* 1.2` (same as `CameraFitter`); clears preset after apply
- `<CameraTypeController>`: watches `cameraProjection` → swaps `PerspectiveCamera` ↔ `OrthographicCamera` in R3F using `useThree().set()`; copies `position/quaternion/up` on switch; **dist uses `camera.position.distanceTo(controls.target)`** (not `position.length()`) to compute correct ortho frustum size; ortho `near/far = [-farRange, +farRange]` where `farRange = max(halfH, dist) × 500` — negative near prevents clipping when zooming; **re-applies `controls.target` after switch** to avoid rotation snap; `prevProjection` starts as `"perspective"` so initial store default `"orthographic"` triggers immediate switch on first mount
- `<PointerEventHandler>`: attaches `click` (Raycaster → `setSelectedPartName`), `dblclick` (Raycaster → `controls.target.copy(hitPoint)` to change orbit pivot), and `contextmenu` (`e.preventDefault()` only — no popup menu) on `gl.domElement`
- `<FitToPartController>`: watches `fitToTarget` store value via **`useFrame` + `useViewerStore.getState()`** (not `useEffect`) — fires every render frame for immediate response; **Perspective**: moves camera toward target **preserving current viewing angle** (direction = `normalize(camera.pos − oldTarget)`); **Orthographic**: keeps camera position, sets `camera.zoom = currentHalfH / radius × 0.8` so the part fills ~80% of viewport height; pre-positions camera at same direction/distance from new center **before** `controls.update()` to prevent OrbitControls from recomputing position and causing clipping; both modes copy `controls.target` to part center; clears after apply
- `<OriginAxes vehicleBbox?>`: shown when `showOriginAxes=true`; renders `<axesHelper>` (red=X, green=Y, blue=Z) + semi-transparent XY plane (`z=0`, `color=#aaaaaa, opacity=0.08, DoubleSide`); axis length = `maxDim × 0.15` (fallback 1 m); plane size = `maxFootprint × 2` (fallback 10 m)
- `<GizmoHelper>` + `<GizmoViewport>` at bottom-left
- Accepts array of `GeometryResponse` (Assembly support) — fetches and overlays all GLBs in parallel
- Shows `<Loader>` while fetching, error text on failure, placeholder text when no assembly selected

**`src/components/viewer/OverlayObjects.tsx`**
- Renders Three.js overlays from `templateSettings` + `vehicleBbox` + `partInfo`
- `partInfo` prop: merged `analysis_result.part_info` from all assembly geometries (passed from `TemplateBuilderPage` via `SceneCanvas`)
- `matchesPattern(partName, pattern)`: TS helper mirroring backend `_matches_pattern` — `*` in pattern → ordered-segment wildcard; no `*` → `startsWith OR endsWith`; case-insensitive. `matchesAny(partName, patterns[])` checks any match.
- Visibility controlled per-item via `overlayVisibility` store (key absent = visible by default):
  - **Domain Box** (key `"domain_box"`): `setup.domain_bounding_box` × vehicle bbox → white wireframe `<boxGeometry>`
  - **Refinement Boxes** (key `"box_{name}"`): `setup.meshing.box_refinement` — per-level color (RL1=light blue → RL7=red) wireframe boxes; each box individually toggleable
  - **Porous Boxes** (key `"box_{entryName}"` or `"box_{entryName}_{coeff_part_name}"`): `setup.meshing.part_based_box_refinement` — rendered only when `setup_option.meshing.box_refinement_porous=true` and `partInfo` available; per-level color; per-coefficient=false → 1 box (union of all matched parts), visibility key `box_{entryName}`; per-coefficient=true → 1 box per `porous_coefficients` entry (parts matching both `pbr.parts` AND `coeff.part_name`), visibility key `box_{entryName}_{coeff.part_name.replace("*","")}` — each sub-box has its own toggle; offsets `pbr.offset_x/y/zmin/max` applied
  - **TG Ground** (key `"tg_ground"`): cyan semi-transparent YZ plane at `x_pos = noSlipXminPos − 0.01` (or `vb.x_min − 0.01` as fallback), extents `y ≈ ±42.5% vehicle width`, `z = [groundZ, groundZ + coarsest/8]`; shown only when `enable_ground_tg = true`. Matches `TurbulenceInstance.point.x_pos` in XML.
  - **TG Body** (key `"tg_body"`): cyan semi-transparent YZ plane at `x_pos = vb.x_min − 5%`, extents `y = car_center ± 45%`, `z = vb.z_min + 10%…65%`; shown only when `enable_body_tg = true`. Both TG overlays are **YZ planes only** (not 3D boxes) — matches the ultraFluidX spec where `<point><x_pos>` defines the x-position and `<bounding_box>` contains only y/z extents.
  - **Probe Spheres** (key `"probe_{name}"`): `output.probe_files[].points[]` → yellow sphere (r=0.04) per point; per-probe-file toggle
  - **Partial Volume Boxes** (key `"pv_{name}"`): `output.partial_volumes[]` → orange wireframe boxes; `bbox_mode` selects coordinates (`user_defined`: `[xm,xp,ym,yp,zm,zp]` vehicle-relative multipliers applied as `bMin=vb_min+m*vLen`, `bMax=vb_max+p*vLen`; `from_meshing_box`: looks up `bbox_source_box_name` key in `setup.meshing.box_refinement` dict, applies same multiplier formula; `around_parts`: not rendered in 3D viewer); per-volume toggle; **field name**: `bbox_source_box_name` (not `bbox_source_box`)
  - **Section Cuts** (key `"sc_{name}"`): `output.section_cuts[]` → magenta semi-transparent `PlaneGeometry` (10×10 m); per-cut toggle
- `vehicleBbox` is union of all geometries in the assembly (computed in `TemplateBuilderPage`)
- `partInfo` is merged `part_info` from all assembly geometries (computed in `TemplateBuilderPage`)

**`src/components/viewer/PartListPanel.tsx`**
- Props: `parts: string[]`; `partInfo?: Record<string, unknown> | null` (merged `analysis_result.part_info` from all assembly geometries)
- Full part list from `analysis_result.parts`, with count badge
- Per-part row: **click name text** → `setSelectedPartName` toggle; row shows **yellow tint** + top+bottom border when `selectedPartName === name`; `IconFocusCentered` ActionIcon (visible when `partInfo[name]?.bbox` exists) → `setFitToTarget` to zoom to part bbox (preserves camera angle, calls `invalidate()`); `IconEyeCheck` ActionIcon per row → "Show only this part" (hides all other parts); eye toggle; **color `ColorSwatch`** (22px square, click → `Popover` with `ColorPicker withPicker={false}`, 96 swatches = 12 hues × 8 lightness, `swatchesPerRow={12}`); **opacity `Popover`** (`Button` showing `α XX%` → `Popover.Dropdown` with `Slider`); part name uses `size="sm"`
- Search bar + `SegmentedControl` (Include / Exclude) — filters visible list
- Toolbar buttons: **Toggle all filtered** (eye/eye-off) · **Show Only** (`IconEyeCheck` — hide everything except filtered parts) · **Invert** (`IconArrowsExchange` — flip visibility of all parts) · **Show all** (`IconEye` → `parts.forEach(n => setPartState(n, { visible: true }))` — correctly handles parts never clicked, unlike `showAllParts()` which only acts on existing `partStates` entries)

**`src/components/viewer/OverlayPanel.tsx`** (new — 2A-13)
- 4-tab `Tabs` component (`pills` variant) rendered inside `ControlPanel`; replaces old flat Switch list
- **Parts tab**: reads `setup.meshing.offset_refinement[].parts`, `setup.meshing.custom_refinement[].parts`, `target_names.wheel/rim/baffle/windtunnel`, `setup_option.ride_height.reference_parts`, `porous_coefficients[].part_name`, `setup_option.meshing.triangle_splitting_instances[].parts` → groups of pattern `Badge` elements. Click any badge → `setSearchQuery(pattern)` → `PartListPanel` search bar filters to matching parts.
- **Box tab**: `OverlaySwitch` rows for Domain Bounding Box (key `"domain_box"`), each `box_refinement` item (key `"box_{name}"`), `part_based_box_refinement` items — when `per_coefficient=False`: one switch per entry (key `"box_{entryName}"`); when `per_coefficient=True`: one switch per porous coefficient (key `"box_{entryName}_{coeff.part_name}"`), label `"{entryName} / {coeff.part_name}"`; each `partial_volumes` item (key `"pv_{name}"`). **`TabMasterSwitch`** at top toggles all items at once.
- **Plane tab**: `OverlaySwitch` for TG Ground (key `"tg_ground"`, sub-text shows `x_pos = noSlipXminPos − 0.01`, shown when `enable_ground_tg=true`), TG Body (key `"tg_body"`, shown when `enable_body_tg=true`), each `section_cuts` item (key `"sc_{name}"`). Ground Plane removed — domain bounding box in Box tab is sufficient for ground height reference. **`TabMasterSwitch`** at top.
- **Probe tab**: `OverlaySwitch` per `probe_files` item (key `"probe_{name}"`) — sub-text shows point count. **`TabMasterSwitch`** at top.
- `OverlaySwitch` reads/writes `overlayVisibility` store directly; key-absent → default visible.
- **`TabMasterSwitch({ visKeys })`**: computes `allVisible = visKeys.every(k => overlayVisibility[k] !== false)`; single `Switch` toggles all keys; placed at top of Box/Plane/Probe tabs.
- No template selected → placeholder text shown.

**`src/components/viewer/TemplateBuilderPage.tsx`**
- Route: `/template-builder`
- **3-column layout**: 275px `ControlPanel` | 255px `PartListPanel` | flex-1 `<SceneCanvas>`
- **`ViewerToolbar`** (floating, top-right of 3D panel, `position:absolute`): `SegmentedControl` Persp/Ortho → `setCameraProjection()` · `Switch` Flat → `setFlatShading()` · `Switch` Edges → `setShowEdges()`
- **`CameraOverlay`** (floating, bottom-right of 3D panel, `position:absolute`, `bottom:8, right:4`): camera preset buttons (iso/front/rear/side/top) + **theme toggle** (`IconSun`/`IconMoon`) + **origin axes toggle** (`IconAxisX`, filled=blue when ON, light when OFF → `setShowOriginAxes()`)
- `ControlPanel` sections (275px left, scrollable) — receives `geometries` + `templateSettings` props:
  1. Assembly `Select` (+ `IconPackage` ActionIcon → `AssemblyGeometriesDrawer`) → Template `Select` (+ `IconPencil` ActionIcon → `TemplateVersionEditModal` for active version; enabled only when template + version loaded)
  2. **Create Case** button (`IconPlus`, enabled when both assembly + template selected) → `CreateCaseFromBuilderModal`
  3. **Overlays** header (`Group`: `Text` + `Divider` + `Switch` → `setOverlaysAllVisible`, global on/off for all 3D overlays) → `<OverlayPanel templateSettings={templateSettings} />`
  4. **Camera** — preset buttons (iso / front / rear / side / top) + theme toggle
- `PartListPanel` receives `allParts` (all part names from assembly geometries) + `partInfo` (merged `analysis_result.part_info` — used for per-part Fit-to camera function)
- Template overlay: fetches `["templates", id, "versions"]`, finds active version, passes `settings` (as `templateSettings`) to `ControlPanel` and `<OverlayObjects>`
- `vehicleBbox`: union of `analysis_result.vehicle_bbox` across all geometries in selected assembly
- `TemplateVersionEditModal` gated on `editTemplateOpen` (mounted only when open) to avoid TagsInput `_value.map` error
- Query key for template versions: `["templates", selectedTemplateId, "versions"]` — matches `TemplateVersionEditModal`'s `invalidateQueries` so saves auto-refresh 3D overlays

**`src/components/geometries/GeometryUploadModal.tsx`** — Decimation Ratio Slider:
- `form.initialValues.decimationRatio: 0.05`
- `Slider` (min=0.01, max=1.0, step=0.01) with marks at 5% / 25% / 50% / Skip
- Badge shows "Keep X% of faces" or "Skip — no 3D preview" when `>= 1.0`
- Warning text shown when Skip is selected: "3D preview will not be generated."
- `decimationRatio` passed as last arg to `geometriesApi.upload()`

**`src/components/geometries/GeometryLinkModal.tsx`** — Decimation Ratio Slider:
- Same Slider UI as UploadModal
- `decimation_ratio: form.values.decimationRatio` included in `geometriesApi.link({...})`

**Navigation**: `AppShell.tsx` → `IconCube` + "Template Builder" → `/template-builder`  
**Route**: `App.tsx` → `<Route path="/template-builder" element={<TemplateBuilderPage />} />`

### Decimation Pipeline

`viewer_service.build_viewer_glb()` pipeline:
1. **STL read** — `stl_decimator.STLReader.read(stl_path)` auto-detects ASCII vs Binary; no `trimesh.load()`. Returns `list[Solid]` (per-part numpy arrays).
2. **Parallel pure-Python QEM** — `ProcessPoolExecutor` → `_decimate_worker(idx, solid, ratio)` per solid (top-level function, Windows spawn-safe); each part processed **independently with same `ratio`** (fraction to keep). `QEMDecimator.simplify` uses heap-based edge-collapse QEM; minimum face count = `max(4, int(n_faces * ratio))`.
3. **GLB export** — `GLBExporter.export(valid_solids, cache_path, colors=None)` writes a spec-compliant GLB 2.0 with flat normals. Colors: if `colors[i]` (RGBA float tuple) is provided, uses it for solid `i`; otherwise falls back to auto-cycling `PALETTE`.
4. If decimation fails for a part → logged as error, part excluded from GLB; if all parts fail → `ValueError` raised, geometry remains `status="ready"` (GLB not cached).

**`stl_decimator.py`** lives at `backend/app/services/stl_decimator.py`. It is also a standalone CLI tool (`python stl_decimator.py input.stl output.glb --ratio 0.2`). No `fast-simplification` or `trimesh` dependency — pure Python + NumPy only.

---

## Phase 2+ Roadmap

### Phase 2A: 3D Viewer / Template Builder — ✅ Complete

See **Phase 2A: 3D Viewer / Template Builder** implementation details section below.

### Phase 2B: Post-Processing EnSight Viewer — 🔲 Planned

**Two modes of post-processing are planned:**

1. **GUI post-processing** (Three.js / React Three Fiber — reuse Phase 2A `SceneCanvas`)
   - 3D CFD result datasets (EnSight `.case` / `.h3d`) loaded in the existing viewer
   - Data coarsening to handle multiple full datasets efficiently
   - Robust multi-dataset comparison with synchronized camera state (Zustand)
   - Simulation info inherited from Ultrafluid log files
   - Photo-realistic rendering (low priority)

2. **Lightweight post-processing with viewer**
   - Predefined post-process settings (values, positions, views, legend, GSP settings)
   - Automated image/movie generation from Ultrafluid output
   - Image viewer with view/position sync and overlay mode for case comparison
   - GSP dataset viewer (probe results, area-weighted power spectrum) — eliminates need for Excel

**Implementation approach for 2B:**
- `uv add pyvista` — backend reads 8-partition EnSight via `pv.EnSightReader`
- Surface extraction + field data baked to vertex colors → GLB export (reuse `viewer_service` pattern)
- `GET /api/v1/runs/{run_id}/result-glb?field=pressure&timestep=last`
- Multiple synchronized viewports: shared `cameraState` in Zustand

**Note**: A lightweight post-processing viewer prototype already exists and can be provided when needed.

### Post-Processing Template

Separate from the simulation template — defines post-processing settings (visualization parameters, section cut positions, legend ranges, view angles, etc.).

### Data Management System

Cross-domain data lifecycle management throughout the CFD process:
- **Pre**: CAD data from structural section, scan data from design team
- **Solve**: Ultrafluid setting files, Ultrafluid results (.case/h3d)
- **Post**: Result tables, images/movies via viewer, report generation, GSP data

### Job Scheduler Integration

Integration with HPC job schedulers (PBS, Slurm) to:
- Submit solver jobs from the application
- Automate file transfer between local storage and compute nodes
- Track job status and retrieve results
