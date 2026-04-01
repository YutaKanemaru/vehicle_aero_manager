# VAM (Vehicle Aero Manager) - Software Architecture & Specification

## 1. Overview

VAM is a web browser-based application that helps automotive engineers manage vehicle external aerodynamics (Aero) and greenhouse noise (GHN: cabin noise) simulation setup and post-processing for day-to-day vehicle development.

### Core Principles
- **Consistency** in simulation settings across the team
- **Efficiency** of the CFD workflow from setup to post-processing
- **Ease of collaborative work** across domains (CAE, design, management)

### Constraints
- **Users**: 20-30+ engineers, asynchronous collaboration with authentication
- **Deployment**: On-premise and cloud (Docker-based)
- **Data**: 1GB+ per simulation case
- **Solver**: Ultrafluid (commercial LBM CFD solver, XML config-driven)
- **Development**: 1-person team, Python-focused, incremental delivery

---

## 2. Tech Stack

### MVP (Phase 1-2): Minimal Infrastructure

| Layer | Technology | Reason |
|-------|-----------|--------|
| Frontend | React 18+ / TypeScript / Vite | Required for Three.js 3D viewer integration |
| UI Library | Mantine UI | Lightweight, strong forms/tables, good docs |
| Backend | Python FastAPI | Leverages Python expertise, auto OpenAPI generation |
| Validation | Pydantic v2 | Ultrafluid XML schema modeling + API validation |
| DB | SQLite (→ PostgreSQL) | Zero setup for MVP; migrate via SQLAlchemy |
| File Storage | Local FS (→ MinIO/S3) | Simple start; abstract via StorageBackend interface |
| Auth | FastAPI + JWT (→ Keycloak) | Minimal auth for MVP; abstract via AuthBackend |
| Task Queue | BackgroundTasks (→ Celery) | Built-in async for MVP; scale with Celery later |
| Deploy | Docker Compose | Single command to start full environment |

### Scale Triggers

| Component | When to Upgrade | Migration Path |
|-----------|----------------|----------------|
| PostgreSQL | >10 concurrent users or JSONB search needed | SQLAlchemy DB swap only |
| MinIO/S3 | >100GB files or multi-server | StorageBackend interface swap |
| Keycloak | LDAP/AD integration required | AuthBackend interface swap |
| Celery + Redis | Parallel background tasks needed | TaskRunner interface swap |
| Kubernetes | Multi-node production deployment | Docker Compose → Helm charts |

---

## 3. System Architecture

### MVP Architecture
```
[Browser - React SPA]
    |
    |--- REST API (JSON) --- [FastAPI Server]
                                |
                          +-----+-----+
                          |           |
                      [SQLite]   [Local FS]
                                  /uploads
                                  /results
```

### Scaled Architecture
```
[Browser - React SPA]
    |
    |--- REST/WebSocket --- [Nginx]
                               |
                   +-----------+-----------+
                   |                       |
             [FastAPI Server]        [MinIO / S3]
                   |
         +---------+---------+
         |         |         |
   [PostgreSQL] [Redis]  [Celery Workers]
```

---

## 4. API Design

```
/api/v1/auth/              # Login, refresh, user info
/api/v1/projects/          # CRUD projects
/api/v1/templates/         # CRUD setting templates (Aero/GHN)
  /{id}/versions           # Template version history
  /{id}/export             # Export as JSON
  /import                  # Import from JSON
/api/v1/configurations/    # CRUD configurations
  /{id}/apply-template     # POST: Apply template to geometry
  /{id}/diff               # POST: Compare with another config
  /{id}/compute            # POST: Run computation pipeline
  /{id}/generate-xml       # POST: Generate Ultrafluid XML
  /{id}/export-xml         # GET: Download generated XML
/api/v1/geometry/          # Geometry file management
  /{id}/parts              # GET: Extracted part list
  /{id}/bbox               # GET: Computed bounding boxes
/api/v1/tasks/             # Async job status
  /{id}/status             # GET: Task progress
/api/v1/files/             # File upload/download
```

---

## 5. Ultrafluid XML Schema Design

### Root Structure (Pydantic)

```python
class UfxSolverDeck(BaseModel):
    version: Version
    simulation: Simulation          # general, material, wall_modeling
    geometry: Geometry              # source_file, baffle, domain_bbox, domain_parts
    meshing: Meshing                # general, refinement (box/offset), overset (rotating)
    boundary_conditions: BoundaryConditions  # inlet, outlet, static, wall
    sources: Sources                # porous, mrf, turbulence
    output: Output                  # general, aero_coefficients, partial_surface/volume
    model_data: ModelData           # GUI metadata (wheels, porous, belts)
```

### Template Strategy: Fixed vs Computed Fields

| Field | Classification | Data Source |
|-------|---------------|-------------|
| simulation.general.* | Fixed | Defined in template |
| simulation.material.* | Fixed | Defined in template |
| geometry.domain_bounding_box | Computed | STL bbox × scaling factor |
| meshing.refinement.box | Mixed | RL fixed, bbox range computed |
| meshing.overset.rotating | Computed | Wheel center/axis from STL |
| boundary_conditions.inlet.velocity | Fixed | Template (wind speed) |
| boundary_conditions.wall (rotating) | Computed | Linked to wheel data |
| sources.porous.porous_axis | Computed | Normal direction from porous media STL |
| sources.porous.resistance | User Input | Via UI |
| output.* | Fixed | Defined in template |

### XML Generation Pipeline
```
Template (JSON) + GeometrySet (STL) + UserInput
    ↓
[Compute Engine]
  - trimesh: STL analysis (bbox, wheel axis, porous direction)
  - NumPy: Coordinate transforms, kinematics
    ↓
[Pydantic Model Assembly]
  - Merge: template fixed values + computed values + user input
  - Pydantic validation
    ↓
[XML Serialization]
  - lxml.etree: Pydantic model → XML output
  - Preserve original XML format (indentation, element order)
    ↓
Output: Ultrafluid XML file
```

---

## 6. Data Model

```
Project
 |-- members: User[] (role: admin/engineer/viewer)
 |-- configurations: Configuration[]
 |-- geometry_sets: GeometrySet[]

Template
 |-- type: AERO_SETUP | GHN_SETUP | POST_PROCESS
 |-- settings: JSON (structured Ultrafluid XML data)
 |-- computed_field_rules: JSON (computation rule definitions)
 |-- naming_convention: JSON (part name mapping rules)
 |-- versions: TemplateVersion[]

GeometrySet
 |-- project: Project
 |-- files: GeometryFile[] (STL)
 |-- part_mapping: JSON {part_name: file_path}
 |-- kinematics: JSON {ride_height_front, ride_height_rear, ...}
 |-- computed: JSON (bbox, wheel_centers, wheel_axes, porous_dirs)

Configuration (Central Entity)
 |-- project: Project
 |-- template: Template + version
 |-- geometry_set: GeometrySet
 |-- user_overrides: JSON (manually modified values)
 |-- computed_params: JSON (compute engine output)
 |-- generated_xml: TEXT (final Ultrafluid XML)
 |-- status: DRAFT → COMPUTING → READY → EXPORTED

Task
 |-- configuration: Configuration
 |-- type: COMPUTE | XML_GENERATE | POST_PROCESS
 |-- status: PENDING → RUNNING → SUCCESS | FAILURE
 |-- progress: float (0-100)

Result
 |-- configuration: Configuration
 |-- type: TABLE | IMAGE | MOVIE | REPORT | GSP
 |-- file_path: TEXT
 |-- metadata: JSON
```

---

## 7. Implementation Phases

### Phase 1: MVP Core - Template + XML Generator (Month 1-4)
- Project foundation (FastAPI + React + Docker Compose + SQLite + JWT)
- Ultrafluid Pydantic schema (XML ↔ Pydantic round-trip)
- Template CRUD with versioning (Aero/GHN)
- Geometry upload + STL analysis (trimesh: part IDs, bbox, wheel axis)
- Compute engine (kinematics, coordinate transforms, porous direction)
- XML generation + Configuration management + Diff view

### Phase 2: Setup Check + 3D Visualization (Month 5-7)
- React Three Fiber 3D viewer (STL display, LOD)
- Setup check visualization (part highlighting, refinement boxes, wheel axes)
- Interactive part selection → settings inspection
- Validation warnings for missing/conflicting settings

### Phase 3: Lightweight Post-Processing (Month 8-10)
- Post-processing templates (views, scalar fields, legends)
- Automated image/movie generation (VTK/PyVista)
- Image viewer with case comparison sync and overlay
- GSP data viewer (time series, power spectrum charts)

### Phase 4: GUI Post-Processing + Data Management (Month 11-15)
- 3D result data overlay (scalar/vector fields)
- Multi-dataset support + LOD for 1GB+ data
- Project-level data management (Pre/Solve/Post)
- Report generation + collaboration features

### Phase 5: Enterprise Features (Month 16+)
- Keycloak (LDAP/AD) authentication
- MinIO/S3 storage migration
- HPC integration (SLURM/PBS)
- PLM integration
- Photo-realistic rendering

---

## 8. Repository Structure

```
vam/
├── docker-compose.yml
├── docker-compose.prod.yml
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── auth/           # JWT, deps, user model
│       ├── api/v1/         # Route handlers
│       ├── models/         # SQLAlchemy ORM
│       ├── schemas/        # Pydantic request/response
│       ├── services/       # Business logic
│       ├── storage/        # StorageBackend abstraction
│       └── ultrafluid/     # XML schema, parser, serializer, template engine
├── frontend/
│   └── src/
│       ├── api/            # Auto-generated from OpenAPI
│       ├── components/     # layout, templates, geometry, configuration, viewer, postprocess
│       ├── hooks/
│       ├── stores/         # Zustand
│       └── types/
├── tests/
└── docs/
```

---

## 9. Key Technical Decisions

### Large File Handling (1GB+)
- Chunked upload from browser
- STL simplification on upload (trimesh → 10% mesh for preview)
- LOD meshes generated server-side for 3D viewer
- Future: MinIO presigned URLs for direct upload

### On-Prem / Cloud Dual Deployment
- Phase 1-2: Docker Compose only (identical for both)
- Phase 3+: Abstraction layers (StorageBackend, AuthBackend) with env var switching
- Phase 5: Helm charts for Kubernetes

### Frontend Strategy (Solo Developer)
- OpenAPI auto-generated TypeScript client (eliminates API boilerplate)
- Mantine UI components for complex forms/tables
- Claude Code assistance for frontend development
