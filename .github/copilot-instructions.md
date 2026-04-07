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
| Step 3 (W6-8) | Template CRUD with versioning (Aero/GHN) | 🔄 **Current target** |
| Step 4 (W9-12) | Geometry upload + STL analysis + Compute engine + Kinematics | ⬜ Not started |
| Step 5 (W13-16) | XML generation + Configuration management + Diff view + Porous coefficients UI | ⬜ Not started |

**When generating code, focus on the current step. Do not implement features from future steps.**

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
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

Rules:
- UUID primary keys as `str(36)` — do not use integer PKs
- Always use `Mapped[T]` + `mapped_column()` — never use `Column()` directly
- Do not put business logic in models

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
- Wheel grouping: classify FR-LH / FR-RH / RR-LH / RR-RH by comparing part centroid to vehicle COG (x, y)
- RPM calculation: `rpm = (inflow_velocity / wheel_circumference) × 60` — needs wheel radius from bbox

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

---

## Phase 2+ Roadmap

The following features are planned for future phases. They are documented here for context but **must not be implemented during Phase 1**.

### Case Management

All datasets related to a simulation case are managed by the application: input STL, simulation setup, check-setup results, solver results, and post-processed data. This enables:
- Easier comparison between cases and table data extraction
- Job launch script integration with schedulers (PBS, Slurm) for automated file transfer to/from compute nodes
- Manual file transfer is also supported as a fallback

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
