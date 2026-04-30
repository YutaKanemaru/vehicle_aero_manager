# Template CRUD — Spec (Step 3 — Complete)

## Backend

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

## Frontend

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
      "domain_bounding_box_relative": true,
      "box_offset_relative": true,
      "box_refinement_porous": true,
      "box_refinement_porous_per_coefficient": false,
      "triangle_splitting_instances": [
        { "name": "TS_Body", "active": true, "max_absolute_edge_length": 0.0, "max_relative_edge_length": 5.0, "parts": ["Body_"] }
      ]
    },
    "boundary_condition": {
      "ground": {
        "ground_height_mode": "from_geometry",
        "ground_mode": "rotating_belt_5",
        "overset_wheels": true,
        "ground_patch_active": true,
        "bl_suction": { "apply": true, "no_slip_xmin_from_belt_xmin": true, "bl_xmin_offset": 0.0 },
        "belt5": { "wheel_belt_location_auto": true, "belt_size_wheel": {"x": 0.4, "y": 0.3} }
      },
      "turbulence_generator": {
        "enable_ground_tg": true, "enable_body_tg": true,
        "ground_tg_intensity": 0.05, "body_tg_intensity": 0.01,
        "ground_tg_length_scale": null, "body_tg_length_scale": null
      }
    },
    "compute": {}
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
    "domain_bounding_box": [-5, 10, -12, 12, 0, 20],
    "meshing": {
      "box_refinement": {
        "Box_RL1": {"level": 1, "box": [-1, 3, -1, 1, -0.2, 1.5]},
        "Box_RL2": {"level": 2, "box": [-0.5, 1.5, -0.75, 0.75, -0.2, 1.0]}
      },
      "part_box_refinement": {},
      "part_based_box_refinement": {
        "Box_Porous_RL7": {"level": 7, "parts": ["Porous_"], "offset_xmin": 0.0, "offset_xmax": 0.0}
      },
      "offset_refinement": {
        "Body_Offset_ALL_RL7": {"level": 7, "normal_distance": 0.012, "parts": []},
        "Body_Offset_ALL_RL6": {"level": 6, "normal_distance": 0.036, "parts": []}
      },
      "custom_refinement": {}
    }
  },
  "output": {
    "full_data": {
      "output_start_time": 1.5, "output_interval": 0.3,
      "file_format": "h3d",
      "output_coarsening_active": false,
      "bbox_mode": "from_meshing_box",
      "output_variables_full": { "pressure": false },
      "output_variables_surface": { "pressure": false }
    },
    "partial_surfaces": [
      { "name": "PS_Body", "output_start_time": 1.5, "output_interval": 0.3, "file_format": "h3d",
        "include_parts": ["Body_"], "exclude_parts": [], "baffle_export_option": null }
    ],
    "partial_volumes": [
      { "name": "PV_Wake", "bbox_mode": "user_defined", "bbox": [-1, 5, -1.5, 1.5, 0, 1.5] },
      { "name": "PV_RL5", "bbox_mode": "from_meshing_box", "bbox_source_box_name": "Box_RL5" }
    ],
    "section_cuts": [
      { "name": "SC_Center", "axis_x": 0, "axis_y": 1, "axis_z": 0,
        "point_x": 0, "point_y": 0, "point_z": 0.5 }
    ],
    "probe_files": [
      { "name": "front_probes", "probe_type": "volume", "radius": 0.05,
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

### Key principles
- `setup_option` (flags) + `simulation_parameter` (physical values) + `setup` (geometry-relative rules) are **Fixed** in Template.
- `output` fully defines all output instances (full data, partial surface/volume, section cuts, probe files).
- `target_names` maps solver concepts to part-naming patterns.
- `porous_coefficients` provides default porous resistance values (can be overridden per Configuration).

### TemplateSettings Pydantic model

```python
class TemplateSettings(BaseModel):
    setup_option:          SetupOption
    simulation_parameter:  SimulationParameter
    setup:                 Setup = Field(default_factory=_aero_setup)  # NOT Setup()
    output:                OutputSettings
    target_names:          TargetNames
    porous_coefficients:   list[PorousMedia] = []
```

### `_aero_setup()` — aero default meshing setup

```python
def _aero_setup() -> Setup:
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

To change defaults: update `_aero_setup()` and run `npm run generate-api`.

### MeshingSetup key fields

```python
class MeshingSetup(BaseModel):
    box_refinement: dict[str, BoxRefinement]
    part_box_refinement: dict[str, BoxRefinement]              # legacy (unused)
    part_based_box_refinement: dict[str, BoxRefinementAroundParts]
    offset_refinement: dict[str, OffsetRefinement]
    custom_refinement: dict[str, CustomRefinement]             # GHN only
```

### BoxRefinementAroundParts

```python
class BoxRefinementAroundParts(BaseModel):
    level: int
    parts: list[str]
    offset_xmin: float = 0.0
    offset_xmax: float = 0.0
    offset_ymin: float = 0.0
    offset_ymax: float = 0.0
    offset_zmin: float = 0.0
    offset_zmax: float = 0.0
```

### RideHeightTemplateConfig

```python
class RideHeightTemplateConfig(BaseModel):
    reference_mode: Literal["wheel_axis", "user_input"] = "wheel_axis"
    reference_z_front: float | None = None
    reference_z_rear:  float | None = None
    reference_parts: list[str] = []
    adjust_body_wheel_separately: bool = False
    use_original_wheel_position: bool = False
```

`SetupOption` includes `ride_height: RideHeightTemplateConfig = Field(default_factory=RideHeightTemplateConfig)`.

### TargetNames key fields

```python
wheel: list[str] = []
rim: list[str] = []        # optional — improves wheel rotation axis accuracy via PCA; omit for heuristic fallback
baffle: list[str] = []
wheel_tire_fr_lh: str = ""
wheel_tire_fr_rh: str = ""
wheel_tire_rr_lh: str = ""
wheel_tire_rr_rh: str = ""
overset_fr_lh: str = ""
overset_fr_rh: str = ""
overset_rr_lh: str = ""
overset_rr_rh: str = ""
windtunnel: list[str] = []
tire_roughness: float = 0.0
```

Note: `porous` and `car_bounding_box` fields have been removed from `TargetNames`.

### ProbeFileConfig

```python
class ProbeFileConfig(BaseModel):
    name: str = "probe"
    probe_type: str = "volume"       # "volume" | "surface"
    radius: float = 0.0
    output_frequency: float = 1.0
    output_start_iteration: int = 0
    scientific_notation: bool = True
    output_precision: int = 7
    output_variables: ProbeFileOutputVariables
    points: list[ProbePointConfig]
```

### TemplateSettingsForm.tsx Tab Sections

| Tab | Contents |
|---|---|
| General *(conditional)* | From `generalContent` prop — Name, Description, Application, Version comment |
| Simulation Run Parameters | Run Time · Physical Properties · Options |
| Meshing | General · Triangle Splitting · Box Refinement · Offset Refinement · Custom Refinement |
| Boundary Conditions | Flow Domain · Ground Condition · Belt Configuration · Turbulence Generator · Porous Media Coefficients |
| Output | Full Data · Aero Coefficients · Partial Surfaces · Partial Volumes · Section Cuts · Probe Files |
| Part Specification | `tn_baffle` + `tn_windtunnel` only |
| Ride Height | `rh_reference_parts` · `rh_adjust_body_wheel_separately` · `rh_use_original_wheel_position` |

Key notes:
- Modal `size="95%"` for all create/edit modals
- `FORM_VALIDATE` exported from `useTemplateSettingsForm.ts` — validates `tn_wt_fr/rr_lh/rh` as required when `ground_mode === "rotating_belt_5"`
- Part name list fields use `TagsInput` (backed by `string[]`)
- Part name pattern matching: `*` → `fnmatch` glob; no `*` → `startswith OR endswith`; case-insensitive
