# Case / Configuration / Run — Spec (Step 5 — Complete)

> **Note**: The original `Configuration` model has been refactored into `ConditionMap` + `Condition`. The term "Configuration" no longer exists in the codebase.

## Data Model (4-layer hierarchy)

| Model | File | Purpose |
|---|---|---|
| `ConditionMap` | `app/models/configuration.py` | Named collection of run conditions (e.g. "40m/s sweep") |
| `Condition` | `app/models/configuration.py` | Single run condition: velocity + yaw + ride_height_json + yaw_config_json |
| `Case` | `app/models/configuration.py` | Bundles Template × Assembly; optionally linked to a ConditionMap |
| `Run` | `app/models/configuration.py` | Execution unit: links Case + Condition → generates XML |
| `System` | `app/models/system.py` | STL transform record: source_geometry → result_geometry + transform_snapshot |

**Design decision**: ConditionMaps are independent of Cases — reusable across multiple Cases.

## Backend Models

**`app/models/configuration.py`**
- `ConditionMap`: `id`, `name`, `description`, `created_by`, `created_at`, `updated_at`; `conditions` one-to-many (cascade delete)
- `Condition`: `id`, `map_id` (FK), `name`, `inflow_velocity`, `yaw_angle`, `ride_height_json` (Text, nullable), `yaw_config_json` (Text, nullable), `created_by`, `created_at`, `updated_at`
- `Case`: `id`, `case_number`, `name`, `description`, `template_id`, `assembly_id`, `map_id` (nullable), `folder_id` (nullable), `parent_case_id` (nullable self-FK, ondelete SET NULL), `created_by`, `created_at`, `updated_at`
- `Run`: `id`, `run_number`, `name`, `case_id` (FK, CASCADE), `condition_id`, `xml_path`, `stl_path`, `geometry_override_id` (nullable FK→geometries, ondelete SET NULL), `status` (`pending`/`generating`/`ready`/`error`), `error_message`, `created_by`, `created_at`, `updated_at`

**`app/models/system.py`**
- `System`: `id`, `name`, `source_geometry_id`, `result_geometry_id` (nullable), `condition_id` (nullable), `transform_snapshot` (Text/JSON), `created_by`, `created_at`

## Schemas (`app/schemas/configuration.py`)

```python
class RideHeightConditionConfig(BaseModel):
    enabled: bool = False
    target_front_wheel_axis_rh: float | None = None  # m from ground
    target_rear_wheel_axis_rh: float | None = None
    target_front_wheel_rh: float | None = None       # used when adjust_body_wheel_separately=True
    target_rear_wheel_rh: float | None = None

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
```

- `RunCreate`: `{ name: str = "", condition_id, comment: str = "" }` — auto-name = `{case_number}_{case_name}_R{N:02d}_{condition_name}[_{comment}]`
- `RunResponse`: includes `xml_path`, `stl_path`, `status`, `run_number`, `condition_name`, `condition_velocity`, `condition_yaw`, `geometry_override_id`, `needs_transform`, `transform_applied`
- `RunUpdate`: `{ geometry_override_id: str | None }`
- `CaseResponse`: includes `run_count`, `case_number`, `template_name`, `assembly_name`, `map_name`, `parent_case_id`, `parent_case_number`, `parent_case_name`
- `CaseDuplicateRequest`: `{ name, description }` — copies template/assembly/map; sets `parent_case_id`
- `CaseCompareResult`: template settings diff, map conditions diff, assembly parts diff

## Service (`app/services/configuration_service.py`)

Key functions:
- `delete_map()`: raises HTTP 400 if any `Case.map_id` references this map
- `delete_condition()`: raises HTTP 400 if any `Run.condition_id` references this condition
- `update_case()`: **template/assembly/map locked** — HTTP 400 when non-pending runs exist and change requested; map change triggers `sync_runs_for_map()`
- `delete_case()`: cascades DB delete to Runs; deletes `data/runs/{run_id}/` output directories
- `create_run()`: auto-formats name when `data.name` is empty
- `reset_run()`: deletes run output dir; if `geometry_override_id` is set → deletes associated `System` record(s) (by `result_geometry_id`) + override `Geometry` (file on disk + DB row) + clears `geometry_override_id`; sets `status="pending"`, clears `xml_path`/`stl_path`/`error_message`
- `trigger_xml_generation()`: **guarded** — HTTP 400 when `ride_height.enabled || yaw_angle != 0` but `geometry_override_id` not set or geometry not `ready`
- `transform_run()`: derives params from Run's Condition + Case; calls `ride_height_service.compute_transform()` + `create_system_and_geometry()`; **calls `db.commit()` internally**; **returns within milliseconds**
  - ⚠️ `transform_snapshot["verification"]["front_wheel_z_actual"]` is **absolute Z coordinate**, not ride height. RH = `actual_z − vehicle_bbox_z_min`
- `_generate_xml_task(run_id, geometry_only=False)`: background task; `geometry_only=True` + `parent_case_id` set → finds parent's ready Run, swaps STL only
- `duplicate_case()`: copies Case row; sets `parent_case_id = source_case_id`; does NOT copy Runs
- `create_case_with_runs()`: creates Case + one Run per Condition
- `compare_cases()`: deep-diffs template settings JSON, map condition values, assembly parts sets
- `sync_runs_for_map()`: re-links kept runs, creates new pending runs, deletes orphan pending runs, preserves generated orphans
- `compute_sync_preview()`: previews keep/add/orphan by `(name, inflow_velocity, yaw_angle)` matching
- `get_axes_glb()`: Run → Condition → Assembly → `viewer_service.build_axes_glb()`
- `get_run_overlay()`: `parse_ufx(xml_path)` → `extract_overlay_data()`

## API Endpoints (`app/api/v1/configurations.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/maps/` | List all condition maps |
| `POST` | `/maps/` | Create condition map |
| `GET` | `/maps/{map_id}` | Get map (includes condition_count) |
| `PATCH` | `/maps/{map_id}` | Update map |
| `DELETE` | `/maps/{map_id}` | Delete map + cascade conditions |
| `GET` | `/maps/{map_id}/conditions/` | List conditions |
| `POST` | `/maps/{map_id}/conditions/` | Create condition |
| `GET` | `/maps/{map_id}/conditions/{cid}` | Get condition |
| `PATCH` | `/maps/{map_id}/conditions/{cid}` | Update condition |
| `DELETE` | `/maps/{map_id}/conditions/{cid}` | Delete condition |
| `GET` | `/cases/` | List all cases |
| `POST` | `/cases/` | Create case |
| `GET` | `/cases/{id}` | Get case |
| `PATCH` | `/cases/{id}` | Update; **template/assembly/map locked** when non-pending runs exist |
| `DELETE` | `/cases/{id}` | Delete case + cascade |
| `GET` | `/cases/{id}/compare?with={id2}` | Compare two cases |
| `GET` | `/cases/{id}/sync-preview?new_map_id={id}` | Preview map change (no data modification) |
| `GET` | `/cases/{id}/runs/` | List runs |
| `POST` | `/cases/{id}/runs/` | Create run |
| `POST` | `/cases/{id}/runs/{rid}/generate?geometry_only=false` | Trigger XML generation |
| `POST` | `/cases/{id}/runs/{rid}/transform` | Apply ride-height + yaw transform |
| `PATCH` | `/cases/{id}/runs/{rid}` | Update run (set `geometry_override_id`) |
| `DELETE` | `/cases/{id}/runs/{rid}` | Delete Run + output directory |
| `POST` | `/cases/{id}/runs/{rid}/reset` | Reset Run to pending; **also deletes System + override Geometry if transform was applied** |
| `GET` | `/cases/{id}/runs/{rid}/download` | Download generated XML |
| `GET` | `/cases/{id}/runs/{rid}/download-stl` | Download input STL |
| `GET` | `/cases/{id}/runs/{rid}/axes-glb` | On-demand axis-visualisation GLB |
| `GET` | `/cases/{id}/runs/{rid}/overlay` | OverlayData from generated XML |
| `POST` | `/cases/{id}/duplicate` | Duplicate Case; sets `parent_case_id` |
| `GET` | `/runs/diff?a={rid}&b={rid}` | Diff two runs' settings |

**API Endpoints** (`app/api/v1/systems.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/systems/` | List all systems |
| `GET` | `/systems/{id}` | Get system |
| `DELETE` | `/systems/{id}` | Delete system |
| `GET` | `/systems/{id}/landmarks-glb` | GLB with before/after landmark spheres |

## Template Settings Extensions

### Compute Engine key functions for XML assembly

```python
def assemble_ufx_solver_deck(
    template_settings, analysis_result, sim_type, inflow_velocity, yaw_angle,
    source_file=None, source_files=None, pca_axes=None,
) -> UfxSolverDeck

def extract_pca_axes(stl_paths, porous_patterns, rim_patterns) -> dict
def build_probe_csv_files(template_settings) -> dict[str, bytes]
def compute_dt(coarsest_mesh_size, mach_factor, temperature_k) -> float
def compute_domain_bbox(vehicle_bbox, multipliers) -> dict
def classify_wheels(analysis_result, target_names) -> dict
def compute_wheel_kinematics(wheel_info, inflow_velocity, rim_vertices=None) -> dict
def compute_porous_axis(part_info, vertices=None) -> dict
def _build_belt5_wall_instances(...) -> tuple[list, float, list]
```

### Ground BC assembly logic

```
ground_mode == "full_moving":
  → WallInstance("uFX_moving_ground", type="moving")

ground_mode != "full_moving":
  → WallInstance("uFX_slip_ground", type="slip")  [always]

  BL suction ON:
    rotating_belt_1  → WallInstance("uFX_moving_ground_patch", type="moving")
    rotating_belt_5 / static → WallInstance("uFX_static_ground", type="static")

belt_5 → _build_belt5_wall_instances() → 5 belt DomainPartInstances
belt_1 → single Belt DomainPartInstance

passive_parts:
  BL suction ON → "uFX_ground"
  rotating_belt_5 → "Belt_Center"
```

### Compute Flag Dependency Rules

```
rotate_wheels / moving_ground → derived from ground_mode
porous_media → bool(template_settings.porous_coefficients)
turbulence_generator → enable_ground_tg or enable_body_tg
adjust_ride_height → per-Run via POST /transform (not a compute flag)
```

### Excel Settings Classification

| Excel Sheet | Setting | Layer |
|---|---|---|
| General | `inflow_velocity`, `yaw_angle`, `ground_height` | **Configuration** |
| General | `opt_belt_system`, `wall_model`, `output_format` | **Template** |
| General | `density`, `dynamic_viscosity`, `temperature` | **Template** |
| Wheels_baffles | Part names | Template `target_names` |
| Heat_exchangers | `coeffs_inertia`, `coeffs_viscous` | **Configuration** `porous_coefficients` |
| Ride_Height | `front/rear_wheel_axis_RH` | Configuration `ride_height` |
| Ride_Height | `adjust_body_wheel_separately`, `reference_parts` | Template `setup_option.ride_height` |
| Mesh_Control | `coarsest_voxel_size`, `transitionLayers` | **Template** |
| Output sheets | all output variable flags | **Template** |

## Frontend Components

- `src/components/maps/MapList.tsx` — Condition Maps table; per-map drawer with `ConditionSection`
- `src/components/maps/ConditionFormModal.tsx` — create/edit condition; Ride Height + Yaw Center accordions
- `src/components/cases/CaseList.tsx` — folder-grouped; row click → `/cases/{id}`; Compare mode (up to 2 rows)
- `src/components/cases/CaseDetailPage.tsx` — 2 tabs:
  - **Case Info & Compare**: editable fields; template/assembly/map locked when non-pending runs exist; Compare with Parent Case accordion
  - **Runs**: per-run Apply Transform / Generate XML / Download / Reset / Delete; Transform All / Generate All bulk buttons; Open 3D Viewer
    - Reset button shown when `status === "ready" | "error"`, or when `status === "pending" && transform_applied` (clears transform too); confirm message varies by `transform_applied`
- `src/components/cases/MapChangeSyncModal.tsx` — previews keep/add/orphan; confirms `PATCH` + `sync_runs_for_map()`
- `src/components/cases/RunViewer.tsx` — 3D viewer for ready Run; overlay from `GET /runs/{id}/overlay`
- `src/components/cases/RunViewerPage.tsx` — `/cases/:caseId/runs/:runId/viewer`; opened in new tab
- `src/components/cases/CaseCreateModal.tsx` — New Case tab + Copy from Case tab
- `src/components/cases/CreateCaseFromBuilderModal.tsx` — bulk-create Case + Runs from Condition Map

### `runsApi` helpers (`src/api/configurations.ts`)
- `runsApi.update(caseId, runId, data)` — PATCH to set `geometry_override_id`
- `runsApi.getAxesGlbUrl(caseId, runId)` — fetch axes GLB → `createObjectURL()`
- `runsApi.download(caseId, runId)` — fetch XML blob (auth header)
- `runsApi.downloadStl(caseId, runId)` — fetch STL blob (auth header)

## Test Scripts

- `backend/scripts/test_transform_run.py` — calls `configuration_service.transform_run()` directly against DB
  ```
  uv run python scripts/test_transform_run.py            # list runs
  uv run python scripts/test_transform_run.py <run_id>   # run transform
  uv run python scripts/test_transform_run.py <run_id> --dry   # skip GLB generation
  ```
  - `InlineBackgroundTasks` stub runs `_transform_and_analyze_task()` synchronously
  - `logging.basicConfig(INFO)` enabled — shows per-step progress (`[bg] Transforming STL`, `[bg] Analyzing`, etc.)
  - `db.commit()` is called inside `transform_run()`, so **DB changes are always persisted** regardless of `--dry`
  - Outputs `test_transform_run_result.json` to `backend/`

## Migrations

- `4a08074381f4` — ConditionMap + Condition tables
- `8949ff1689b0` — systems table; `ride_height_json` + `yaw_config_json` on conditions
- `ff0265eeeb01` — `stl_path` column on `runs`
- `0601bb149381` — `geometry_override_id` FK on `runs` (batch_alter_table)
- `100503ac21a7` — `parent_case_id` self-FK on `cases` (batch_alter_table)
