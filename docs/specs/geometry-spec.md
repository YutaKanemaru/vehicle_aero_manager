# Geometry, Assembly, Background Jobs & Compute Engine — Spec (Step 4 — Complete)

## Data Model (5-layer hierarchy)

| Model | Purpose |
|---|---|
| `GeometryFolder` | Optional organisational folder for grouping Geometries |
| `Geometry` | Single STL file entity — stores file path, status, and analysis results |
| `AssemblyFolder` | Optional organisational folder for grouping Assemblies |
| `GeometryAssembly` | Named collection of Geometries — optionally linked to an AssemblyFolder |
| `assembly_geometry_link` | Many-to-many association table |

## Backend

**Models** (`app/models/geometry.py`)
- `GeometryFolder`: `id`, `name`, `description`, `created_by`, `created_at`, `updated_at`; `geometries` one-to-many
- `Geometry`: `id`, `name`, `description`, `folder_id` (nullable FK), `file_path`, `original_filename`, `file_size`, `is_linked: bool`, `status` (`pending`/`analyzing`/`ready`/`error`), `analysis_result` (JSON string), `error_message`, `uploaded_by`, `created_at`, `updated_at`
- `AssemblyFolder`: `id`, `name`, `description`, `created_by`, `created_at`, `updated_at`
- `GeometryAssembly`: `id`, `name`, `description`, `folder_id`, `created_by`, `created_at`, `updated_at`; `geometries` many-to-many
- `assembly_geometry_link`: association table (`assembly_id`, `geometry_id`)
- Class ordering in file: `assembly_geometry_link` → `GeometryFolder` → `Geometry` → `AssemblyFolder` → `GeometryAssembly`

**Schemas** (`app/schemas/geometry.py`)
- `PartInfo`: `centroid [x,y,z]`, `bbox dict`, `vertex_count`, `face_count`
- `AnalysisResult`: `parts`, `vehicle_bbox`, `vehicle_dimensions`, `part_info dict`
- `GeometryResponse`: full response including parsed `analysis_result`, `folder_id: str | None`, `is_linked: bool`
- `GeometryUpdate`: `name`, `description`, `folder_id` — uses `model_fields_set` to distinguish explicit null from field not sent
- `GeometryLinkRequest`: `name`, `description`, `file_path` (server absolute path), `folder_id`, `decimation_ratio: float = 0.05`

**Compute Engine** (`app/services/compute_engine.py`)
- `_detect_stl_format(file_path)`: reads 84 bytes — detects binary by magic bytes OR `80 + 4 + n*50 == file_size`
- `_parse_stl_ascii_streaming(file_path, verbose)`: line-by-line streaming — never allocates vertex arrays; centroid = bbox center `(min+max)/2`
- `analyze_stl(file_path: Path)`: raises `ValueError` if binary; calls streaming parser; computes vehicle bbox
- **Binary STL not supported** — users must convert to ASCII
- Multi-solid ASCII STL fully supported

**Service** (`app/services/geometry_service.py`)
- `upload_geometry()`: saves to `upload_dir/geometries/{id}/{filename}` via chunked `shutil.copyfileobj` (8MB), triggers background analysis
- `link_geometry()`: creates `Geometry` row with `is_linked=True` and absolute `file_path`; triggers background analysis
- `run_analysis(db, geometry_id, decimation_ratio=0.05)`: `pending` → `analyzing` → `ready-decimating` → `ready`/`error`; if `ratio >= 1.0` skips GLB
- `delete_geometry()`: `is_linked=False` のみファイル削除。`_rmtree_force()` ヘルパー (Windows read-only 属性対策)。`invalidate_cache(geometry.id)` も呼ぶ
- `delete_assembly()`: raises HTTP 400 if any `Case.assembly_id` references this assembly

**API Endpoints** (`app/api/v1/geometries.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/geometries/folders/` | List all folders |
| `POST` | `/geometries/folders/` | Create folder |
| `PATCH` | `/geometries/folders/{folder_id}` | Update folder |
| `DELETE` | `/geometries/folders/{folder_id}` | Delete folder (children → uncategorized) |
| `GET` | `/geometries/` | List all geometries |
| `POST` | `/geometries/` | Upload STL (multipart: `name`, `description`, `folder_id`, `file`, `decimation_ratio`) |
| `POST` | `/geometries/link` | Link only (JSON: `GeometryLinkRequest`) |
| `GET` | `/geometries/{id}` | Get geometry with analysis result |
| `PATCH` | `/geometries/{id}` | Update name/description/folder_id |
| `DELETE` | `/geometries/{id}` | Delete + file cleanup |
| `GET` | `/geometries/{id}/file` | Download original STL |
| `GET` | `/geometries/{id}/glb?ratio=0.05` | Get decimated GLB (cache or generate) |

**Route order**: folder endpoints MUST be declared before `/{geometry_id}`.

**API Endpoints** (`app/api/v1/assemblies.py`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/assemblies/folders/` | List all assembly folders |
| `POST` | `/assemblies/folders/` | Create assembly folder |
| `PATCH` | `/assemblies/folders/{folder_id}` | Update |
| `DELETE` | `/assemblies/folders/{folder_id}` | Delete (children → uncategorized) |
| `GET` | `/assemblies/` | List all assemblies |
| `POST` | `/assemblies/` | Create assembly |
| `GET` | `/assemblies/{id}` | Get assembly with geometries (selectinload) |
| `PATCH` | `/assemblies/{id}` | Update name/description/folder_id |
| `DELETE` | `/assemblies/{id}` | Delete assembly |
| `POST` | `/assemblies/{id}/geometries/{gid}` | Add geometry |
| `DELETE` | `/assemblies/{id}/geometries/{gid}` | Remove geometry |

**Migrations**:
- `f46197300d43` — geometry and assembly tables
- `d4be3f102eac` — geometry_folders + folder_id FK (batch_alter_table)
- `bd293b1f57fc` — assembly_folders
- `b6662ad9ba21` — is_linked boolean column

## Frontend

**API layer** (`src/api/geometries.ts`)
- `geometriesApi.upload(name, description, folderId, file, onProgress?, decimationRatio=0.05)` — uses `XMLHttpRequest` for `upload.onprogress`
- `geometriesApi.link(data: GeometryLinkRequest)` — JSON POST
- `geometriesApi.getGlbBlobUrl(id, ratio?)` — fetches GLB with auth → `createObjectURL()`
- `assemblyFoldersApi`, `assembliesApi` — full CRUD

**Components**

| File | Description |
|---|---|
| `GeometryList.tsx` | Folder-hierarchy view; auto-refresh every 3s when `pending`/`analyzing`/`ready-decimating` |
| `GeometryUploadModal.tsx` | Modal closes immediately; XHR continues in background; Decimation Ratio Slider (5%/25%/50%/Skip) |
| `GeometryLinkModal.tsx` | JSON POST; same Decimation Ratio Slider |
| `AssemblyList.tsx` | Folder-hierarchy view; manage-geometries action per row |
| `AssemblyGeometriesDrawer.tsx` | SegmentedControl: Current / Add geometries tabs; folder-grouped with select-all per folder |

**Implementation notes**
- Upload uses `XMLHttpRequest` (not `fetch`) for progress support
- `is_linked=True` geometries show cyan "Linked" badge; delete only removes DB row
- SQLite FK workaround: use `op.batch_alter_table()` in Alembic for FK constraints

---

## Background Jobs System

### Zustand Store (`src/stores/jobs.ts`)

```typescript
export type JobStatus = "uploading" | "pending" | "analyzing" | "ready-decimating" | "ready" | "error";
```

**Actions**: `addJob` · `updateJob` · `updateUploadProgress` · `removeJob` · `clearCompleted`

**Upload Flow**:
1. `addJob(tempId, ...)` → job appears as "Uploading…"
2. Modal closes immediately
3. XHR `onprogress` → `updateUploadProgress(tempId, pct)`
4. XHR success → `removeJob(tempId)` + `addJob(realId, ...)` + `updateJob(realId, "pending")`
5. `useJobsPoller` polls until `ready`/`error`

### Jobs Drawer (`src/components/layout/JobsDrawer.tsx`)
- Status configs: uploading (cyan) · pending (yellow, 15%) · analyzing (blue, 60%) · ready-decimating (violet, 85%) · ready (green, 100%) · error (red, 100%)
- Per-job ✕ button for manual dismissal

---

## Compute Engine Notes

Key calculations:

| Output | Method |
|---|---|
| `domain_bounding_box` | Vehicle bbox × relative multipliers |
| Wheel rotation axis | PCA on rim vertices (`vt[2]` = min variance = rotation axis) |
| Porous flow axis | PCA on porous vertices (`vt[2]` = min variance = face normal) |
| RPM | `inflow_velocity / wheel_circumference × 60` |

**Implementation rules**:
- ASCII STL only — binary raises `ValueError`
- `analyze_stl` never allocates vertex arrays — O(parts) memory, not O(file size)
- Centroid = bbox center `(min+max)/2` — NOT vertex average
- `_normalize_stl_part_name(name)` strips `COMMENT: ...` suffixes — keep in sync between `compute_engine.py` and `stl_decimator.STLReader._read_ascii`
- `rim: []` in `target_names` → falls back to wheel part vertices for PCA (lower accuracy); specifying rim patterns improves axis detection but is optional
- `extract_pca_axes()` is a separate STL re-scan (memory-efficient: collects only matching vertices)
- Porous axis: `vt[2]` (min variance = face normal = flow direction through flat surface)
- Rim axis: `vt[2]` (min variance = rotation axis of flat disk); flip sign if `y < 0`
- Porous matching: glob pattern — `HX_Rad_*` matches multiple parts

**Compute Engine key functions** (`app/services/compute_engine.py`):
```python
assemble_ufx_solver_deck(template_settings, analysis_result, sim_type, inflow_velocity, yaw_angle, source_file, pca_axes) -> UfxSolverDeck
extract_pca_axes(stl_paths, porous_patterns, rim_patterns) -> dict
compute_wheel_kinematics(wheel_info, inflow_velocity, rim_vertices=None) -> dict
compute_porous_axis(part_info, vertices=None) -> dict
compute_dt(coarsest_mesh_size, mach_factor, temperature_k) -> float
build_probe_csv_files(template_settings) -> dict[str, bytes]
```

**Test scripts**:
- `backend/scripts/test_compute_engine.py` — `uv run python scripts/test_compute_engine.py [<stl_path>]`
- `backend/scripts/test_ride_height.py` — compute_transform() + transform_stl() smoke test
  ```
  uv run python scripts/test_ride_height.py [<stl_path>] [front_rh] [rear_rh] [yaw_deg]
  uv run python scripts/test_ride_height.py --unit    # no STL needed: single case
  uv run python scripts/test_ride_height.py --suite   # no STL needed: 12-pattern suite
  ```
  - `--unit` mode: dummy analysis_result + `reference_mode="user_input"` (ref_front=ref_rear=0.4 → target 0.3/0.35); verifies round-trip error < 1 mm
  - `--suite` mode: runs 12 posture-change patterns (identity / heave / pitch / heave+pitch / yaw / yaw+heave / yaw+pitch / full-3-axis / sep-orig-wheel / sep-indep-wheel / user-input-ref / rear-only); exits 1 if any case fails. `_SUITE_CASES` table in script; `sep_orig_wheel` (Pattern I) skips RH error check (wheel stays at original Z by design)
  - STL mode: `reference_parts=["Wheel_"]` hardcoded; outputs `test_ride_height_result.json` + `{stl_stem}_transformed.stl` to `backend/`
  - Verification display: shows both `actual_rh` (= actual_z − ground_z) and `actual_z` (absolute) to make the coordinate system explicit
