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
│       │   ├── viewer_service.py  # GLB generation, decimation, cache management
│       ├── storage/             # StorageBackend abstraction
│       └── ultrafluid/          # XML schema (Pydantic), parser, serializer — isolated module
├── frontend/
│   └── src/
│       ├── api/                 # API client — generated schema.d.ts + templateDefaults.ts + typed wrappers
│       ├── components/          # UI components
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
    <moment_reference_system>     # Type, origin, roll/pitch/yaw axis
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
        "Box_Porous_RL6": {"level": 6, "parts": ["Porous_"], "offset_xmin": 0.5, "offset_xmax": 0.5, ...}
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
        "bbox": [-1, 5, -1.5, 1.5, 0, 1.5], "output_variables": {...} }
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
| `GeometryAssembly` | Named collection of Geometries — optionally linked to a Template and an AssemblyFolder |
| `assembly_geometry_link` | Many-to-many association table |

**Part swap workflow**: change which `Geometry` objects are members of a `GeometryAssembly`.
**Folder workflow**: purely organisational — both Geometry and Assembly hierarchies use the same folder pattern.

### Backend

**Models** (`app/models/geometry.py`)
- `GeometryFolder`: `id`, `name`, `description`, `created_by`, `created_at`, `updated_at`; `geometries` one-to-many relationship
- `Geometry`: `id`, `name`, `description`, `folder_id` (nullable FK→geometry_folders), `file_path` (upload時: `upload_dir` 相対パス / link時: 絶対パス), `original_filename`, `file_size`, `is_linked: bool` (default `False` — `True` の場合消死時にファイルを肝ない), `status` (`pending`/`analyzing`/`ready`/`error`), `analysis_result` (JSON string), `error_message`, `uploaded_by` (FK→users), `created_at`, `updated_at`
- `AssemblyFolder`: `id`, `name`, `description`, `created_by`, `created_at`, `updated_at`; `assemblies` one-to-many relationship
- `GeometryAssembly`: `id`, `name`, `description`, `template_id` (nullable FK→templates), `folder_id` (nullable FK→assembly_folders), `created_by`, `created_at`, `updated_at`; `geometries` many-to-many relationship; `folder` many-to-one relationship
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
- `delete_geometry()`: `is_linked=False` の時のみ `shutil.rmtree` 実行。`is_linked=True` の場合は DB 行のみ削除し元ファイルはそのまま
- `list_folders`, `create_folder`, `update_folder`, `delete_folder` — folder delete sets `geometry.folder_id = None` for all children
- `_folder_or_404(db, folder_id)` helper validates folder existence
- All CRUD for both `Geometry` and `GeometryAssembly`
- Assembly folder CRUD: `list_assembly_folders`, `create_assembly_folder`, `update_assembly_folder`, `delete_assembly_folder` — delete sets `assembly.folder_id = None` for all children
- `_assembly_folder_or_404(db, folder_id)` helper validates assembly folder existence
- `create_assembly()` accepts `folder_id`; `update_assembly()` handles `folder_id` via `model_fields_set`
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
| `AssemblyCreateModal.tsx` | Create assembly with optional template link (dropdown from templates list) + optional folder select (`assemblyFoldersApi.list()`) |
| `AssemblyGeometriesDrawer.tsx` | Right-side drawer: shows current geometries (with remove button), lists available `ready` geometries to add (multi-checkbox select) |

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
| `meshing.overset.rotating` (wheel center/axis) | PCA on rim vertices → axis = 3rd principal component | `trimesh` + `numpy` |
| `sources.porous.porous_axis` | PCA on porous media vertices → face normal direction | `trimesh` + `numpy` |
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
- Wheel grouping: classify FR-LH / FR-RH / RR-LH / RR-RH by comparing part centroid to vehicle COG (x, y)
- RPM calculation: `rpm = (inflow_velocity / wheel_circumference) × 60` — needs wheel radius from bbox
- `analyze_stl(file_path, verbose=False)` — pass `verbose=True` to print step-by-step progress logs (used by `backend/scripts/test_compute_engine.py`)

**Test script**: `backend/scripts/test_compute_engine.py` — runs `analyze_stl()` standalone and prints vehicle bbox, dimensions, and per-part summary. Run with `uv run python scripts/test_compute_engine.py [<stl_path>]`. Auto-detects first STL in `data/uploads/geometries/` if no argument given. Saves full result to `test_compute_engine_result.json`.

---

## Step 5: Case / Configuration / Run — Implementation Details (Complete)

### Data Model (3-layer hierarchy)

| Model | Purpose |
|---|---|
| `Case` | Top-level container: bundles Template × 1 + Assembly × 1 + Configurations |
| `Configuration` | Stores UserInput per test condition (speed, yaw, porous coefficients, compute flags) |
| `Run` | Execution unit: picks one Configuration → generates XML → links to scheduler job |

**Design decision**: Cases represent geometry/template combos. Cross-geometry comparison = separate Cases with Runs compared via Diff view.

### Backend

**Models** (`app/models/configuration.py`)
- `Case`: `id`, `name`, `description`, `template_id` (FK→templates), `assembly_id` (FK→geometry_assemblies), `created_by`, `created_at`, `updated_at`; `configurations` and `runs` relationships
- `Configuration`: `id`, `name`, `description`, `case_id` (FK→cases), `settings` (JSON Text — `ConfigurationSettings`), `created_by`, `created_at`, `updated_at`
- `Run`: `id`, `name`, `case_id` (FK→cases), `configuration_id` (FK→configurations), `xml_path` (nullable), `status` (`pending`/`generating`/`ready`/`error`), `error_message` (nullable), `scheduler_job_id` (nullable — PBS/Slurm future), `created_by`, `created_at`, `updated_at`

**Schemas** (`app/schemas/configuration.py`)

```python
class PorousInput(BaseModel):
    part_name: str
    inertial_resistance: float   # 1/m — required per porous part
    viscous_resistance: float    # 1/s — required per porous part

class ComputeOverrides(BaseModel):
    """Override Template's ComputeOption per Configuration. None = use Template default."""
    porous_media: bool | None = None
    turbulence_generator: bool | None = None
    adjust_ride_height: bool | None = None

class RideHeightInput(BaseModel):
    front_wheel_axis_rh: float | None = None   # m — front wheel centre height from ground
    rear_wheel_axis_rh: float | None = None    # m
    adjust_body_wheel_separately: bool = True

class ConfigurationSettings(BaseModel):
    inflow_velocity: float | None = None       # None = use Template default
    yaw_angle: float = 0.0                     # degrees
    simulation_time: float | None = None       # None = use Template default
    porous_coefficients: list[PorousInput] = []
    compute_overrides: ComputeOverrides = Field(default_factory=ComputeOverrides)
    ride_height: RideHeightInput = Field(default_factory=RideHeightInput)
```

- `CaseCreate`, `CaseUpdate`, `CaseResponse` (includes `configuration_count`, `run_count`)
- `ConfigurationCreate`, `ConfigurationUpdate`, `ConfigurationResponse`
- `RunCreate`, `RunResponse` (includes `xml_path`, `status`)
- `DiffResult`: list of changed fields between two Runs

**Service** (`app/services/configuration_service.py`)
- `list_cases`, `get_case`, `create_case`, `update_case`, `delete_case`
- `list_configurations(case_id)`, `get_configuration`, `create_configuration`, `update_configuration`, `delete_configuration`
- `create_run(case_id, configuration_id)`, `list_runs(case_id)`
- `generate_xml(run_id, db, background_tasks)` — background task: `assemble_ufx_solver_deck()` → `serialize_ufx()` → save to `data/runs/{run_id}/output.xml`; then `build_probe_csv_files()` writes one CSV per probe_file_instance beside the XML → update `run.status`
- Multi-STL: if Assembly has 1 geometry → `source_file`; if multiple → `source_files` list passed to `assemble_ufx_solver_deck`
- `get_diff(run_id_a, run_id_b, db)` → `DiffResult`
- Permission check: `resource.created_by == current_user.id OR current_user.is_admin`

**API Endpoints** (`app/api/v1/configurations.py`):

| Method | Path | Description |
|---|---|---|
| `GET` | `/cases/` | List all cases |
| `POST` | `/cases/` | Create case (template_id + assembly_id required) |
| `GET` | `/cases/{id}` | Get case with configuration_count + run_count |
| `PATCH` | `/cases/{id}` | Update name/description |
| `DELETE` | `/cases/{id}` | Delete case + cascade |
| `GET` | `/cases/{id}/configurations/` | List configurations |
| `POST` | `/cases/{id}/configurations/` | Create configuration |
| `GET` | `/cases/{id}/configurations/{cid}` | Get configuration |
| `PATCH` | `/cases/{id}/configurations/{cid}` | Update configuration |
| `DELETE` | `/cases/{id}/configurations/{cid}` | Delete configuration |
| `GET` | `/cases/{id}/runs/` | List runs |
| `POST` | `/cases/{id}/runs/` | Create run (configuration_id required) |
| `POST` | `/cases/{id}/runs/{rid}/generate` | Trigger XML generation (background task) |
| `GET` | `/cases/{id}/runs/{rid}/download` | Download generated XML |
| `GET` | `/runs/diff?a={rid}&b={rid}` | Diff two runs' settings |

**Migration**: new Alembic revision for `cases`, `configurations`, `runs` tables.

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
    offset_xmin: float = 0.5   # m — absolute distance beyond matched parts bbox in -X
    offset_xmax: float = 0.5   # m — absolute distance beyond matched parts bbox in +X
    offset_ymin: float = 0.5   # m — absolute distance beyond matched parts bbox in -Y
    offset_ymax: float = 0.5   # m — absolute distance beyond matched parts bbox in +Y
    offset_zmin: float = 0.5   # m — absolute distance beyond matched parts bbox in -Z
    offset_zmax: float = 0.5   # m — absolute distance beyond matched parts bbox in +Z
```


**`SetupOption.compute`** (ComputeOption):
```python
class ComputeOption(BaseModel):
    # All other flags removed — auto-derived in compute_engine:
    #   rotate_wheels / moving_ground → from ground_mode
    #   porous_media → from bool(template_settings.porous_coefficients)
    #   turbulence_generator → from tg_cfg.enable_ground_tg | enable_body_tg
    adjust_ride_height: bool = False
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
) -> UfxSolverDeck:
    """Top-level orchestrator — assembles all 7 UfxSolverDeck sections.
    Multi-STL: if source_files provided, sets geometry.source_files list.
    Probe instances: builds ProbeFileInstance per probe_files config.
    Partial surface/volume: builds instances dynamically from template output config.
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

def compute_wheel_kinematics(wheel_parts: dict, inflow_velocity: float) -> list[dict]:
    """PCA on rim vertices → axis; rpm = inflow_velocity / (2π×radius) × 60."""

def compute_porous_axis(part_info: dict) -> dict:
    """PCA on porous part vertices → face normal → PorousAxis xyz."""

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
All flags except adjust_ride_height are auto-derived in compute_engine:

rotate_wheels / moving_ground:
  → derived from ground_mode: static → False, otherwise → True

porous_media:
  → derived from bool(template_settings.porous_coefficients)
  → empty list → no porous sources

turbulence_generator:
  → derived from tg_cfg.enable_ground_tg or tg_cfg.enable_body_tg
  → both off → no TG instances
```

### Excel Settings Classification (from AUR_v1.2_EXT.xlsx / CX1_v1.2_GHN.xlsx)

| Excel Sheet | Setting | Layer |
|---|---|---|
| General | `DATA_FOLDER`, `list_stl_files`, `simulationName` | VAM managed |
| General | `inflow_velocity`, `yaw_angle_vehicle`, `ground_height` | **Configuration** |
| General | `simulation_time`, `output_start_time`, `output_interval_time` | Config (optional override) |
| General | `opt_moving_floor`, `osm_wheels`, `activate_body_tg`, `adjust_ride_height` | Config `compute_overrides` |
| General | `opt_belt_system`, `wall_model`, `solution_type`, `output_format` | **Template** |
| General | `density`, `dynamic_viscosity`, `temperature` | **Template** |
| Wheels_baffles | `WheelPartsNames`, `RimPartsNames`, `BafflePartsName` | Template `target_names` |
| Wheels_baffles | `WheelTireParts_FR/RR_LH/RH` | Template `target_names.wheel_tire_*` |
| Wheels_baffles | `OversetMeshPartsName_FR/RR_*` | Template `target_names.overset_*` |
| Wheels_baffles | `windtunnel_parts` | Template `target_names.windtunnel` |
| Belts | `belt_size_*`, `belt_center_position_*` | Template `setup.boundary_condition_input` |
| Heat_exchangers | part `name` | Template `target_names.porous` |
| Heat_exchangers | `coeffs_inertia`, `coeffs_viscous` | **Configuration** `porous_coefficients` |
| Ride_Height | `front/rear_wheel_axis_RH`, `adjust_body_wheel_separately` | Configuration `ride_height` |
| Mesh_Control | `triangleSplitting`, `coarsest_voxel_size`, `transitionLayers` | **Template** |
| Additional_offset_refinement | all rows | Template `setup.meshing.offset_refinement` |
| Custom_refinement | all rows (GHN only) | Template `setup.meshing.custom_refinement` |
| Output sheets (all) | all output variable flags | **Template** |

### Frontend Components

- `src/components/cases/CaseList.tsx` — table with Template/Assembly badges, config count, Run button
- `src/components/cases/CaseCreateModal.tsx` — Template + Assembly selector
- `src/components/configurations/ConfigurationList.tsx` — list within Case detail
- `src/components/configurations/ConfigurationCreateModal.tsx` — multi-section form (below)
- `src/components/runs/RunList.tsx` — status badge, XML download link, Diff selector
- `src/components/runs/DiffView.tsx` — side-by-side or diff-list view of two Run settings
- Navigation: `AppShell.tsx` adds `Cases` (IconCar)

**`ConfigurationCreateModal` sections:**

| Section | Fields |
|---|---|
| Conditions | `inflow_velocity` (Template default shown), `yaw_angle`, `simulation_time` (optional override) |
| Compute Options | Checkbox tree — porous_media, turbulence_generator, adjust_ride_height (rotate_wheels/moving_ground derived from ground_mode) |
| Porous Coefficients | Auto-generated from Assembly porous parts — `inertial/viscous_resistance` per part (shown only if porous_media=ON) |
| Ride Height | `front/rear_wheel_axis_rh`, `adjust_body_wheel_separately` (shown only if adjust_ride_height=ON) |

**`TemplateSettingsForm.tsx`** (used inside Create/Edit/View modals):

Form state is managed by `src/hooks/useTemplateSettingsForm.ts` (`useTemplateSettingsForm` hook). Key interfaces:
```typescript
interface OffsetRefinementFormItem          { name, level, normal_distance, parts: string }
interface CustomRefinementFormItem          { name, level, parts: string }
interface PorousCoeffFormItem               { part_name, inertial_resistance, viscous_resistance }
interface TriangleSplittingInstanceFormItem { name, active, max_absolute_edge_length, max_relative_edge_length, parts: string }
interface PartialSurfaceFormItem    { name, output_start_time, output_interval, file_format, include_parts, exclude_parts, baffle_export_option, output_variables, ... }
interface PartialVolumeFormItem     { name, bbox_mode, bbox_source_box, bbox, bbox_offset_xmin/xmax/ymin/ymax/zmin/zmax, output_variables, ... }
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
| Ride Height | `compute_adjust_ride_height` Switch only (placeholder) |

**Key notes:**
- Modal `size="95%"` for all 3 create/edit modals
- `merge_output` default is `false` for all output config classes (FullData, PartialSurface, PartialVolume, SectionCut) — both backend Pydantic and frontend helpers
- `FORM_VALIDATE` exported from `useTemplateSettingsForm.ts` — validates `tn_wt_fr/rr_lh/rh` as required when `ground_mode === "rotating_belt_5"`
- All create/version modals import and pass `validate: FORM_VALIDATE` to `useForm()`
- `tn_wheel` / `tn_rim` moved to BC tab > Ground Condition accordion (aero only)
- `tn_wt_*` tire parts moved to BC tab > Belt Configuration accordion (isBelt5, marked `required`)
- `tn_osm_*` OSM parts moved to BC tab > Ground Condition, shown when `overset_wheels` is ON
- `compute_adjust_ride_height` moved from BC tab to Ride Height tab

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
ready-decimating  → violet badge "Building 3D…"  ← GLB pre-generation for `medium` LOD only
      ↓
  ready           → green badge "Complete"
 (error)          → red badge "Failed"
```

### Backend

**`backend/app/services/viewer_service.py`** (new)
- `_parse_solids_for_decimation(stl_path) -> list[tuple[str, np.ndarray, np.ndarray]]`: streaming ASCII STL parser — same token logic as `compute_engine._parse_stl_ascii_streaming` but **retains** `vertices_buf` and `faces_buf` per solid as numpy arrays; peak memory = O(largest single solid), not O(file). Returns `[(name, vertices_float32, faces_int32), ...]`.
- `_decimate_solid(name, vertices, faces, target_reduction, min_faces, agg) -> tuple[str, Trimesh]`: constructs `trimesh.Trimesh(vertices, faces, process=False)` directly (no `trimesh.load()`). Decimation priority chain:
  1. `fast_simplification.simplify(points, triangles, target_reduction, agg=agg)` — curvature-aware QEM; lower `agg` preserves curved surfaces / edges more aggressively (0=most precise, 5=default, 10=fastest)
  2. `mesh.simplify_quadric_decimation(face_count=target_faces)` — trimesh QEM fallback
  3. numpy uniform subsampling (`faces[::step]`) — last resort
- `build_viewer_glb(geometry, lod) -> bytes`: resolves `LOD_DECIMATION_PARAMS[lod]` → (1) `STLReader.read(stl_path)` (ASCII+Binary auto-detect) → (2) `ProcessPoolExecutor` parallel `_decimate_worker` (each part independently with same `ratio`) → (3) `GLBExporter.export(valid_solids, cache_path)` → read bytes → return. **trimesh and fast-simplification are not used.**
- `get_cached_glb(geometry_id, lod) -> bytes | None`: returns cached GLB bytes if exists
- `invalidate_cache(geometry_id)`: removes all LOD cache files for a geometry
- `LOD_DECIMATION_PARAMS`: per-LOD dict with `ratio` (fraction to keep, 0.0–1.0) and `min_faces` (per-part lower bound, enforced inside `QEMDecimator.simplify`)
  - `low`:    `{ratio: 0.50, min_faces: 1000}` — **(production default, same as medium)**
  - `medium`: `{ratio: 0.50, min_faces: 1000}` — balanced **(production default)**
  - `high`:   `{ratio: 0.50, min_faces: 1000}` — **(same as medium; tune ratio to differentiate)**
- Cache path: `{viewer_cache_dir}/{geometry_id}_{lod}.glb`
- **No `fast-simplification` dependency** — `stl_decimator.QEMDecimator` is the sole decimation engine (pure Python + NumPy)

**`backend/app/config.py`**: `viewer_cache_dir: Path = _BACKEND_DIR / "data" / "viewer_cache"`

**`backend/app/database.py`**: `settings.viewer_cache_dir.mkdir(parents=True, exist_ok=True)` on startup

**`backend/app/services/geometry_service.py`** — `run_analysis()` changes:
- After STL analysis succeeds → sets `status = "ready-decimating"` → commits
- Pre-generates GLB for **`medium` LOD only** via `build_viewer_glb(geometry, lod="medium")` (blocking, runs in background task)
- Sets `status = "ready"` in `finally` block regardless of GLB success/failure
- `delete_geometry()` calls `invalidate_cache(geometry.id)` before DB delete

**`backend/app/api/v1/geometries.py`** — new endpoints:
| Method | Path | Description |
|---|---|---|
| `GET` | `/geometries/{id}/file` | Download original STL (`FileResponse`) |
| `GET` | `/geometries/{id}/glb?lod=low` | Get decimated GLB — serves from cache, generates if missing |

- `lod` query param: `"low" | "medium" | "high"` (default `"medium"`); frontend always requests `"medium"`
- Returns `Response(content=glb_bytes, media_type="model/gltf-binary")`
- 400 if geometry `status != "ready"` or `"ready-decimating"` when cache already exists

### Frontend

**`src/stores/viewerStore.ts`** (new — Zustand)
```typescript
partStates: Record<string, { visible, color, opacity }>  // per-part 3D state
searchQuery: string
searchMode: "include" | "exclude"
overlays: { domainBox, refinementBoxes, wheelAxes, groundPlane }
selectedAssemblyId: string | null
selectedTemplateId: string | null
lod: "medium"  // fixed — no UI selector; medium is production default (ratio=0.50, min_faces=1000)
```

**`src/api/geometries.ts`** — new helper:
- `geometriesApi.getGlbBlobUrl(id, lod?)`: fetches GLB with auth header → `Blob` → `URL.createObjectURL()`, returns URL string. Caller must `URL.revokeObjectURL()` on cleanup.

**`src/stores/jobs.ts`** — `JobStatus` now includes `"ready-decimating"`

**`src/hooks/useJobsPoller.ts`** — polls while `pending | analyzing | ready-decimating`

**`src/components/layout/JobsDrawer.tsx`** — `"ready-decimating"` status: violet, 85%, "Building 3D…"

**`src/components/geometries/GeometryList.tsx`** — violet badge + "Building 3D viewer cache..." text + refetchInterval triggers on `ready-decimating`

**`src/components/viewer/SceneCanvas.tsx`** (new)
- R3F `<Canvas>` + `<OrbitControls>` + lights + `<Grid>`
- `<GLBModel>`: loads GLB via `useGLTF(blobUrl)` → `scene.traverse()` applies `partStates` (visible / color / opacity) to each `Mesh` node
- `<CameraFitter>`: `Box3.setFromObject(scene)` → positions camera to fit all geometry on first load
- Accepts array of `GeometryResponse` (Assembly support) — fetches and overlays all GLBs in parallel
- Shows `<Loader>` while fetching, error text on failure, placeholder text when no assembly selected

**`src/components/viewer/OverlayObjects.tsx`** (new)
- Renders Three.js overlays from `templateSettings` + `vehicleBbox`:
  - **Domain Box** (`overlays.domainBox`): `setup.domain_bounding_box` × vehicle bbox → white wireframe `<boxGeometry>`
  - **Refinement Boxes** (`overlays.refinementBoxes`): `setup.meshing.box_refinement` — per-level color (RL1=light blue → RL7=red) wireframe boxes
  - **Ground Plane** (`overlays.groundPlane`): semi-transparent green plane at `z = vehicle_bbox.z_min`
- `vehicleBbox` is union of all geometries in the assembly (computed in `TemplateBuilderPage`)

**`src/components/viewer/PartListPanel.tsx`** (new)
- Full part list from `analysis_result.parts`, grouped with count badge
- Per-part: eye toggle / `ColorInput` / opacity `Slider`
- Search bar + `SegmentedControl` (Include / Exclude) — filters visible list
- "Toggle all filtered" + "Reset all" toolbar buttons

**`src/components/viewer/TemplateBuilderPage.tsx`** (new)
- Route: `/template-builder`
- Layout: fixed 300px left panel + flex-1 right `<SceneCanvas>`
- Left panel: Assembly `Select` → Template `Select` → overlay `Switch` group → `<PartListPanel>` (LOD selector removed; always uses `"medium"`)
- Template overlay: fetches `listVersions`, finds active version, passes `settings` to `<OverlayObjects>`
- `vehicleBbox`: union of `analysis_result.vehicle_bbox` across all geometries in selected assembly

**Navigation**: `AppShell.tsx` → `IconCube` + "Template Builder" → `/template-builder`  
**Route**: `App.tsx` → `<Route path="/template-builder" element={<TemplateBuilderPage />} />`

### Decimation Pipeline

`viewer_service.build_viewer_glb()` pipeline:
1. **STL read** — `stl_decimator.STLReader.read(stl_path)` auto-detects ASCII vs Binary; no `trimesh.load()`. Returns `list[Solid]` (per-part numpy arrays).
2. **Parallel pure-Python QEM** — `ProcessPoolExecutor` → `_decimate_worker(idx, solid, ratio)` per solid (top-level function, Windows spawn-safe); each part processed **independently with same `ratio`** (fraction to keep). `QEMDecimator.simplify` uses heap-based edge-collapse QEM; minimum face count = `max(4, int(n_faces * ratio))`.
3. **GLB export** — `GLBExporter.export(valid_solids, cache_path)` writes a spec-compliant GLB 2.0 with flat normals and PALETTE auto-coloring (pure stdlib, no pygltflib).
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
