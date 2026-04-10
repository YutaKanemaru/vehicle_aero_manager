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

### Scale-trigger technologies

**DO NOT introduce in Phase 1–2:**
- PostgreSQL, MinIO, Keycloak, Celery, Redis, Kubernetes, Helm

**Introduce when implementation requires it** (no fixed phase restriction):
- Three.js / React Three Fiber — for 3D check-setup visualization and post-processing viewer
- VTK / PyVista — for server-side geometry and result processing

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

**All Phase 1 steps are complete. Next work will be Phase 2 (post-processing) or incremental improvements.**

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
│       ├── storage/             # StorageBackend abstraction
│       └── ultrafluid/          # XML schema (Pydantic), parser, serializer — isolated module
├── frontend/
│   └── src/
│       ├── api/                 # API client — generated schema.d.ts + typed wrappers
│       ├── components/          # UI components
│       ├── hooks/               # Custom React hooks
│       ├── stores/              # Zustand stores only
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

The TypeScript API schema is auto-generated from FastAPI's OpenAPI spec:

```bash
npm run generate-api
```

This produces `src/api/schema.d.ts`. Write typed wrappers in `src/api/`:

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
- Run `npm run generate-api` after every backend schema change
- Never call `fetch()` or `axios` directly in components — use `src/api/` wrappers

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
        <active>                  # bool
        <max_absolute_edge_length>
        <max_relative_edge_length>
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
    <probe_file/>                 # typically empty
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
| `Computed` | Derived from STL geometry analysis (trimesh/NumPy) | `geometry.domain_bounding_box`, `meshing.overset.rotating` |
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
- `TemplateSettings`: 4-section Pydantic model (`setup_option`, `simulation_parameter`, `setup`, `target_names`)
- `TemplateCreate`, `TemplateUpdate`, `TemplateVersionCreate`, `TemplateForkRequest` (requests)
- `TemplateResponse`, `TemplateVersionResponse` (responses — include `active_version`, `version_count`)
- `@field_validator("settings", mode="before")` parses JSON string from DB automatically

**Service** (`app/services/template_service.py`)
- `list_templates`, `get_template`, `create_template`, `update_template`, `delete_template`
- `list_versions`, `create_version`, `activate_version`
- `fork_template` — copies active version settings to a new template
- Permission check: `template.created_by == current_user.id OR current_user.is_admin`
- `create_version` / `activate_version`: deactivates all existing versions before setting new active

**API Endpoints** (`app/api/v1/templates.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/templates/` | List all templates |
| `POST` | `/api/v1/templates/` | Create template (creates v1 simultaneously) |
| `GET` | `/api/v1/templates/{id}` | Get template with active version |
| `PATCH` | `/api/v1/templates/{id}` | Update name/description |
| `DELETE` | `/api/v1/templates/{id}` | Delete template + cascade versions |
| `GET` | `/api/v1/templates/{id}/versions` | List all versions |
| `POST` | `/api/v1/templates/{id}/versions` | Create new version (becomes active) |
| `PATCH` | `/api/v1/templates/{id}/versions/{vid}/activate` | Activate specific version |
| `POST` | `/api/v1/templates/{id}/fork` | Fork: copy active version to new template |

**Migration**: `alembic/versions/40849f49edd9_add_templates_and_template_versions.py`

### Frontend

**API layer** (`src/api/`)
- `client.ts`: `get`, `post`, `put`, `patch`, `delete` wrappers; handles 204 No Content; exports `client` (primary) and `api` (backward-compat alias)
- `templates.ts`: All 9 endpoints wrapped; all types from `schema.d.ts` (never manual)
- `auth.ts` `UserResponse` + `stores/auth.ts` `User`: both include `is_admin: boolean` and `is_superadmin: boolean`

**Components** (`src/components/templates/`)

| File | Description |
|---|---|
| `TemplateList.tsx` | Table view with Versions / Fork / Delete action icons per row |
| `TemplateCreateModal.tsx` | Full settings form for creating a new template |
| `TemplateVersionsDrawer.tsx` | Right-side drawer showing version history; contains New Version button (owner/admin only) and per-version 👁 / `</>` icons |
| `TemplateVersionCreateModal.tsx` | Settings form pre-filled from active version; creates a new version |
| `TemplateSettingsViewModal.tsx` | Read-only (disabled) settings form for inspecting any version's parameters |
| `TemplateForkModal.tsx` | Form to fork a template: enter new name, description, comment; copies active version settings |

**Permission model (frontend)**
- Fork button: visible to all authenticated users
- Delete button: visible only when `user.id === template.created_by || user.is_admin`
- New Version / Activate buttons: visible only when `user.id === template.created_by || user.is_admin`

---

## Template JSON Schema (Step 3 Reference)

Based on prototype implementation in concept_vam, a Template's `settings` JSON field follows this 4-section structure:

```json
{
  "setup_option": {
    "simulation": {
      "temperature_degree": true,         // temperature input is °C (converted to K)
      "simulation_time_with_FP": false     // use flow-passage time instead of fixed time
    },
    "meshing": {
      "triangle_splitting": true,
      "domain_bounding_box_relative": true, // bbox defined relative to car dimensions
      "box_offset_relative": true,
      "box_refinement_porous": true
    },
    "boundary_condition": {
      "ground": { "moving_ground": true, "no_slip_static_ground_patch": true,
                  "ground_zmin_auto": true, "boundary_layer_suction_position_from_belt_xmin": true },
      "belt": { "opt_belt_system": true, "num_belts": 5,
                "include_wheel_belt_forces": true, "wheel_belt_location_auto": true },
      "turbulence_generator": { "activate_body_tg": true, "activate_ground_tg": true }
    }
  },
  "simulation_parameter": {
    "inflow_velocity": 38.88,             // m/s (Fixed)
    "density": 1.2041,                   // kg/m³ (Fixed)
    "dynamic_viscosity": 1.8194e-5,      // kg/(s·m) (Fixed)
    "temperature": 20,                   // °C (Fixed)
    "specific_gas_constant": 287.05,     // J/(kg·K) (Fixed)
    "mach_factor": 2,                    // (Fixed)
    "num_ramp_up_iter": 200,             // (Fixed)
    "finest_resolution_size": 0.0015,    // m — determines coarsest mesh size (Fixed)
    "number_of_resolution": 7,           // coarsest = finest × 2^N (Fixed)
    "simulation_time": 2,                // seconds (Fixed)
    "simulation_time_FP": 30             // flow passages (Fixed, if time_with_FP=true)
  },
  "setup": {
    "domain_bounding_box": [-5, 15, -12, 12, 0, 20],  // relative multipliers (Fixed)
    "meshing": {
      "box_refinement": { "Box_RL1": {"level": 1, "box": [...]}, ... },
      "part_box_refinement": { ... },
      "offset_refinement": { ... },
      "custom_refinement": { ... }
    },
    "boundary_condition_input": {
      "belts": { "belt_size_wheel": {"x": 0.4, "y": 0.3}, ... },
      "boundary_layer_suction_xpos": -1.1
    }
  },
  "target_names": {
    "wheel":            ["Wheel_"],          // part name matching patterns
    "rim":              ["_Spokes_"],
    "porous":           ["Porous_Media_"],
    "car_bounding_box": [""],
    "baffle":           ["_Baffle_"],
    "triangle_splitting": [""]
  }
}
```

**Key principle**: `setup_option` (bool flags) and `simulation_parameter` (physical values) are Fixed and stored in the Template. `setup` contains geometry-relative sizing rules. `target_names` maps solver concepts to part naming conventions.

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
- `analyze_stl(file_path: Path) -> dict`: `trimesh.load(str(path), force="scene")` → processes each solid in `Scene.geometry`
- Extracts per-part: centroid, bbox (x/y/z min/max), vertex_count, face_count
- Computes vehicle bbox (union of all parts) and dimensions (length, width, height)
- Returns JSON-serializable dict matching `AnalysisResult` schema
- Multi-solid ASCII STL fully supported via `force="scene"`

**Service** (`app/services/geometry_service.py`)
- `upload_geometry(db, name, description, file, current_user, folder_id=None)`: saves file to `upload_dir/geometries/{id}/{filename}`, stores relative path, triggers `BackgroundTasks`
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
| `GeometryList.tsx` | Folder-hierarchy view: geometries grouped into collapsible `FolderSection` panels (Paper + Collapse). Uncategorized geometries shown last. Each geometry row has expand-for-analysis-details + move-to-folder Popover (Select dropdown). Header has "New Folder" + "Upload STL" buttons. Auto-refreshes every 3s when any item is `pending`/`analyzing`. |
| `GeometryUploadModal.tsx` | Upload form: name, description, folder select (from `foldersApi.list()`), STL file input. Uses XHR upload with progress callback — button shows "Uploading…" and all fields disabled during transfer. On success: registers job via `addJob` then `updateJob` to `pending`. |
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
export type JobStatus = "uploading" | "pending" | "analyzing" | "ready" | "error";

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

**Actions**: `addJob(id, name, type)` — starts as `uploading` · `updateJob(id, status, error_message?)` · `updateUploadProgress(id, progress)` · `removeJob(id)` · `clearCompleted()`

**Selectors**: `selectActiveJobs(s)` · `selectActiveCount(s)` — both include `uploading` + `pending` + `analyzing`

**Persistence**: `zustand/middleware persist` with `partialize` — stores only jobs younger than 24 hours

### Upload Flow
1. `addJob(tempId, name, "stl_analysis")` — job immediately appears as "Uploading…" in drawer
2. XHR `upload.onprogress` → `updateUploadProgress(tempId, pct)` — progress bar updates in real time
3. On XHR success → `removeJob(tempId)` + `addJob(realId, name, ...)` + `updateJob(realId, "pending")`
4. `useJobsPoller` picks up the real ID and polls until `ready`/`error`

### Poller Hook (`src/hooks/useJobsPoller.ts`)
- Mounted in `AppShell` — runs for the lifetime of the app
- Polls `GET /geometries/` every 3 s when any job is `pending` or `analyzing`
- **Does NOT poll** `uploading` jobs — those are tracked entirely via XHR callbacks
- Uses `useInterval` from `@mantine/hooks`
- **Deleted geometry cleanup**: if a `pending`/`analyzing` job ID is not found in the API response (geometry was deleted mid-analysis), `removeJob()` is called immediately. `ready`/`error` jobs for deleted geometries are also removed on the same poll cycle.

### Jobs Drawer (`src/components/layout/JobsDrawer.tsx`)
- Triggered from AppShell header button with active-count `Indicator` badge
- Status configs: `uploading` (cyan, real progress %) · `pending` (yellow, 15% animated) · `analyzing` (blue, 60% striped) · `ready` (green, 100%) · `error` (red, 100%)
- Badge for `uploading` status shows live `XX%` instead of label text
- "Clear" button removes `ready` + `error` jobs

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
- Use `trimesh` + `numpy` only — already in `pyproject.toml`
- Do NOT use `numpy-stl` or `scikit-learn` (used in concept_vam prototype but not in this stack)
- STL files may be multi-solid ASCII format — parse by solid name
- `trimesh.load()` must always pass `process=False` — skips normal recalculation, vertex deduplication, and BVH build (~20–40% faster for large vehicle STL files); normals are not needed for bbox/centroid analysis
- Wheel grouping: classify FR-LH / FR-RH / RR-LH / RR-RH by comparing part centroid to vehicle COG (x, y)
- RPM calculation: `rpm = (inflow_velocity / wheel_circumference) × 60` — needs wheel radius from bbox
- `analyze_stl(file_path, verbose=False)` — pass `verbose=True` to print step-by-step progress logs (used by `backend/test_compute_engine.py`)

**Test script**: `backend/test_compute_engine.py` — runs `analyze_stl()` standalone and prints vehicle bbox, dimensions, and per-part summary. Run with `uv run python test_compute_engine.py [<stl_path>]`. Auto-detects first STL in `data/uploads/geometries/` if no argument given. Saves full result to `test_compute_engine_result.json`.

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
    rotate_wheels: bool | None = None
    porous_media: bool | None = None
    turbulence_generator: bool | None = None
    moving_ground: bool | None = None
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
- `generate_xml(run_id, db, background_tasks)` — background task: `assemble_ufx_solver_deck()` → `serialize_ufx()` → save to `data/runs/{run_id}/output.xml` → update `run.status`
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

New `ComputeOption` added to `SetupOption`:
```python
class ComputeOption(BaseModel):
    rotate_wheels: bool = True          # overset rotating + rotating wall BC
    porous_media: bool = True           # porous sources + box refinement for porous
    turbulence_generator: bool = True   # sources.turbulence (Aero only)
    moving_ground: bool = True          # belt BC moving (Auto False if rotate_wheels=False)
    adjust_ride_height: bool = False    # ride height adjustment (Config can override)
```

New fields added to `TargetNames`:
```python
wheel_tire_fr_lh: str = ""   # individual tyre PID — required for OSM + belt auto-position
wheel_tire_fr_rh: str = ""
wheel_tire_rr_lh: str = ""
wheel_tire_rr_rh: str = ""
overset_fr_lh: str = ""      # OSM region PID
overset_fr_rh: str = ""
overset_rr_lh: str = ""
overset_rr_rh: str = ""
windtunnel: list[str] = []   # passive parts — excluded from force calc + bbox
```

New fields added to `SimulationParameter`:
```python
start_averaging_time: float = 1.5    # seconds
avg_window_size: float = 0.3         # seconds
output_start_time: float | None = None   # None = auto (= simulation_time)
output_interval_time: float | None = None  # None = auto (= simulation_time)
yaw_angle: float = 0.0              # Template default yaw (Config can override)
```

### Compute Engine Extensions (`app/services/compute_engine.py`)

New functions added for XML assembly:

```python
def resolve_compute_flags(template_flags: ComputeOption, overrides: ComputeOverrides) -> ComputeOption:
    """Apply Config overrides to Template defaults. Enforce dependency rules:
       rotate_wheels=False → moving_ground belt auto disabled
       moving_ground=False → turbulence_generator ground disabled"""

def compute_domain_bbox(vehicle_bbox: dict, multipliers: list[float]) -> dict:
    """Apply 6 relative multipliers to vehicle bbox → absolute domain bounding box"""

def classify_wheels(analysis_result: dict, target_names: TargetNames) -> dict:
    """Sort parts matching target_names.wheel into FR_LH/FR_RH/RR_LH/RR_RH by centroid vs COG"""

def compute_wheel_kinematics(wheel_parts: dict, inflow_velocity: float) -> list[dict]:
    """PCA on rim vertices → axis; rpm = inflow_velocity / (2π×radius) × 60"""

def compute_porous_axis(part_info: dict) -> dict:
    """PCA on porous part vertices → face normal direction → PorousAxis xyz"""

def compute_coarsest_mesh_size(finest_res: float, n_levels: int) -> float:
    """Return finest_res × 2^n_levels"""

def assemble_ufx_solver_deck(
    template_settings: TemplateSettings,
    analysis_result: dict,
    config_settings: ConfigurationSettings,
) -> UfxSolverDeck:
    """Top-level orchestrator:
       1. resolve_compute_flags()
       2. Resolve effective inflow_velocity / simulation_time (Config > Template)
       3. compute_domain_bbox()
       4. classify_wheels() + compute_wheel_kinematics()  [if rotate_wheels]
       5. compute_porous_axis() per porous part           [if porous_media]
       6. compute_coarsest_mesh_size()
       7. Assemble all 7 UfxSolverDeck sections
    """
```

### Compute Flag Dependency Rules

```
rotate_wheels = False
  → meshing.overset.rotating = []
  → boundary_conditions.wall rotating instances = removed
  → belt auto-position disabled (belt coords from Template setup)

moving_ground = False
  → all belt BCs → static (not moving)
  → turbulence_generator.ground = False (forced)

porous_media = False
  → sources.porous = []
  → box_refinement_porous skipped

turbulence_generator = False
  → sources.turbulence = []
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
| 走行条件 | `inflow_velocity` (Template default shown), `yaw_angle`, `simulation_time` (optional override) |
| Compute Options | Nested checkbox tree with dependency grayout (rotate_wheels → moving_ground/OSM, etc.) |
| Porous Coefficients | Auto-generated from Assembly porous parts — `inertial/viscous_resistance` per part (shown only if porous_media=ON) |
| Ride Height | `front/rear_wheel_axis_rh`, `adjust_body_wheel_separately` (shown only if adjust_ride_height=ON) |

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

---

## Phase 2+ Roadmap

The following features are planned for future phases. They are documented here for context but **must not be implemented during Phase 1**.

### Post-Processing

**Two modes of post-processing are planned:**

1. **GUI post-processing** (Three.js / React Three Fiber)
   - 3D result datasets loaded in a GUI session for detailed analysis
   - Data coarsening to handle multiple full datasets efficiently
   - Robust multi-dataset comparison
   - Simulation info inherited from Ultrafluid log files
   - Photo-realistic rendering (low priority)

2. **Lightweight post-processing with viewer**
   - Predefined post-process settings (values, positions, views, legend, GSP settings)
   - Automated image/movie generation from Ultrafluid output
   - Image viewer with view/position sync and overlay mode for case comparison
   - GSP dataset viewer (probe results, area-weighted power spectrum) — eliminates need for Excel

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
