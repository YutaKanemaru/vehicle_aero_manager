# Phase 2A: 3D Viewer / Template Builder — Spec (Complete)

## Overview

A 3D viewer for pre-processing (STL geometry + Template overlay) at `/template-builder`. Backend converts ASCII STL to decimated GLB and caches it. Frontend renders with React Three Fiber.

## Geometry Status Flow

```
upload / link
      ↓
  pending         → yellow badge "Pending"
      ↓
  analyzing       → blue badge "Analyzing…"
      ↓
ready-decimating  → violet badge "Building 3D…"  ← GLB pre-generation (skipped when ratio >= 1.0)
      ↓
  ready           → green badge "Complete"
 (error)          → red badge "Failed"
```

## Backend Services

### `viewer_service.py`

- `DEFAULT_RATIO: float = 0.05`
- `build_viewer_glb(geometry, ratio=DEFAULT_RATIO) -> bytes`: `STLReader.read()` → `ProcessPoolExecutor` parallel QEM decimation → `GLBExporter.export()`
- `get_cached_glb(geometry_id, ratio) -> bytes | None`
- `invalidate_cache(geometry_id)`: removes all cache files via glob `{id}_*.glb`
- Cache path: `{viewer_cache_dir}/{geometry_id}_{ratio:.3f}.glb`
- `build_axes_glb(template_settings, analysis_result, stl_paths, inflow_velocity) -> bytes` — on-demand; wheel (FR_LH=red, FR_RH=blue, RR_LH=orange, RR_RH=green) + porous (purple) arrows + center spheres
- `build_landmarks_glb(transform_snapshot) -> bytes` — before=grey, after-front=red, after-rear=blue, after-wheelbase=white

### `ride_height_service.py`

- `compute_transform(analysis_result, rh_cfg, yaw_angle_deg, yaw_cfg) -> dict` — pure math, no file I/O
  - **Transform order**: Yaw (Z-axis) → Pitch (Y-axis, Rodrigues) → Z-translate
  - Returns `transform_snapshot` with keys: `transform`, `wheel_transforms`, `landmarks`, `targets`, `verification`
- `create_system_and_geometry(db, source_geometry, transform_snapshot, name, current_user, condition_id, background_tasks) -> (System, Geometry)` — **returns immediately**, schedules background task; result geometry inherits `decimation_ratio` from `source_geometry.decimation_ratio`
- `_transform_and_analyze_task()` — background: STL write → `analyze_stl_to_json()` → `build_viewer_glb()` → `status="ready"`

### `preview_service.py`

- `extract_overlay_data(deck, template_settings, all_part_names, analysis_result=None, target_names=None) -> OverlayData` — converts assembled solver deck to absolute-coordinate viewer primitives. `target_names` enables `classify_wheels()`-based RH reference point detection (most accurate); falls back to `extract_wheel_reference_z()` when `None`. Also extracts `axes` from the deck: wheel rotation axes from `FluidBCRotating.axis/center` (per wall instance with `type=="rotating"`; corner detected via name substring `fr_lh`/`fr_rh`/`rr_lh`/`rr_rh`; length from part bbox y-span/2) and porous flow axes from `PorousInstance.porous_axis` (center from `analysis_result` part centroid; length = max bbox span × 0.5).
- `compute_overlay_data(db, template_id, assembly_id) -> OverlayData` — XML cache-through pipeline:
  1. Build `stl_paths` from assembly ready geometries; call `extract_pca_axes(stl_paths, porous_patterns, rim_patterns)` for accurate wheel center (rim vertex centroid) and porous axis
  2. Assemble solver deck via `assemble_ufx_solver_deck(..., pca_axes=pca_axes)`
  3. Serialise to `preview_cache_dir/{version_id}_{assembly_id}.xml` via `serialize_ufx()` (skip if cached)
  4. Parse back via `parse_ufx()` — ensures overlay is derived from identical XML structure as real generation
  5. Call `extract_overlay_data(..., analysis_result=merged, target_names=template_settings.target_names)` — Axis tab is populated; Template Builder shows wheel rotation axes and porous flow axes
- `invalidate_preview_cache(version_id)` — deletes all `{version_id}_*.xml` files from `preview_cache_dir`; called by `template_service.update_version_settings()` on every in-place settings save
- Cache path helper: `_preview_cache_path(version_id, assembly_id)` → `preview_cache_dir/{version_id}_{assembly_id}.xml`

### `app/schemas/overlay.py`

- `OverlayBoxItem`: `name`, `vis_key`, `level`, bbox coords, `color`, `category` (`"domain"` / `"refinement"` / `"porous"` / `"partial_volume"`)
- `OverlayPlaneItem`: `name`, `vis_key`, `type` (`"tg_ground"` / `"tg_body"` / `"section_cut"`), `position`, `normal`, `width`, `height`, `color`
- `OverlayDomainPartItem`: `name`, `vis_key`, `location`, `export_mesh`, bbox, `z_position`, `color`
- `OverlayProbeItem`: `name`, `vis_key`, `points`, `radius`
- `OverlayAxisItem`: `name`, `category` (`"wheel"` / `"porous"`), `center: [x,y,z]`, `direction: [x,y,z]` (unit vector), `length: float`, `color: str`
- `OverlayData`: `domain_box`, `refinement_boxes`, `porous_boxes`, `partial_volume_boxes`, `domain_parts`, `tg_planes`, `section_cut_planes`, `probes`, `parts_groups`, `ground_z`, `ride_height_ref`, `axes: list[OverlayAxisItem]`

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/geometries/{id}/glb?ratio=` | Decimated GLB (cache or generate); `ratio` optional — defaults to `geometry.decimation_ratio` if omitted |
| `GET` | `/preview/overlay` | OverlayData for Template × Assembly |
| `GET` | `/cases/{id}/runs/{rid}/axes-glb` | On-demand axes GLB |
| `GET` | `/cases/{id}/runs/{rid}/belt-glb` | On-demand belt STL → GLB (no decimation); 404 if `belt_stl_path` not set |
| `GET` | `/cases/{id}/runs/{rid}/overlay` | OverlayData from generated XML |

### Decimation Pipeline

1. `STLReader.read(stl_path)` — ASCII+Binary auto-detect → `list[Solid]`
2. `ProcessPoolExecutor` → `_decimate_worker(idx, solid, ratio)` per solid — parallel pure-Python QEM
3. `GLBExporter.export(valid_solids, cache_path)` — GLB 2.0, flat normals, PALETTE colors

`stl_decimator.py` lives at `backend/app/services/stl_decimator.py` — pure Python + NumPy, no trimesh/fast-simplification.

**Boundary-Preserving QEM** (`QEMDecimator.simplify(ratio, boundary_penalty=1000.0)`):
- After edge_set is built, boundary edges (edges shared by exactly 1 face) are detected
- Boundary edges receive a `×boundary_penalty` cost in both initial heap build and neighbour recomputation
- Default `boundary_penalty=1000.0` — collapses boundary edges last, preserving solid outlines and reducing visible gaps between parts in the 3D viewer
- `boundary_penalty=1.0` restores original unconstrained QEM behaviour

## Frontend

### `src/stores/viewerStore.ts` (Zustand)

Key state:
```typescript
partStates: Record<string, { visible, color, opacity }>
selectedAssemblyId: string | null   // changing resets glbLoaded=false
selectedTemplateId: string | null
glbLoaded: boolean                  // set true by GLBModel after first Mesh detected
cameraProjection: "perspective" | "orthographic"
cameraPreset: string | null         // "top" | "front" | "side" | "iso" | "rear" | null
flatShading: boolean
showEdges: boolean
overlayVisibility: Record<string, boolean>  // key absent = visible (true)
overlaysAllVisible: boolean         // global master switch
selectedPartName: string | null
fitToTarget: { center, radius } | null
rhRefVisible: boolean               // default false — ride height reference points visibility
```

`partColor(name)` — deterministic per-part color (djb2 hash → 12-color SWATCHES palette).

### Key Frontend Components

**`SceneCanvas.tsx`**
- Props: `geometries: GeometryResponse[]`, `overlayData?: OverlayData | null`, `vehicleBbox?`, `axesGlbUrl?: string | null`, `landmarksGlbUrl?: string | null`, `beltGlbUrl?: string | null`. **No `ratio` prop** — GLB is fetched with `getGlbBlobUrl(g.id, g.decimation_ratio)` per geometry
- `beltGlbUrl` renders the belt STL (when available on a Run) via `<AxesGLBModel>` inside the Canvas Suspense block
- `<GLBModel>`: 3 separate `useEffect` hooks for flatShading, partStates, and glbLoaded detection
- `<CameraFitter>`: fires after `glbLoaded=true`; iso position `center + maxDim×1.2`
- `<CameraPresetController>`: `useFrame` + `getState()` — fires every frame for immediate response
- `<CameraTypeController>`: swaps Perspective ↔ Orthographic; copies position/quaternion; ortho `near/far = [-farRange, +farRange]`
- `<FitToPartController>`: `useFrame` + `getState()`; Perspective preserves viewing angle; Orthographic sets `camera.zoom = frustumHalfH / radius × 0.8` — **must NOT divide by `camera.zoom`**
- `<PointerEventHandler>`: click → select part; dblclick → change orbit pivot
- `<OriginAxes vehicleBbox?>`: axesHelper + semi-transparent XY plane at z=0
- `showEdges` → `THREE.LineSegments(EdgesGeometry)` tagged `userData.isEdgeLine`
- Loading overlay: shown when `!glbLoaded && blobEntries.length > 0`; `pointerEvents: none`

**`OverlayObjects.tsx`** (backend-driven — zero calculation logic)
- Receives `overlayData: OverlayData | null` (pre-computed absolute coords from backend)
- Per `overlayVisibility` key: domain box (white wireframe) · refinement boxes (per-level color) · porous boxes · partial volume boxes (orange) · TG planes (cyan, YZ only) · section cuts (magenta) · probe spheres (yellow) · domain parts (FloorRect: green=belt, orange=uFX_ground)
- Axis arrows (`axes` list): `AxisArrow` renders each item as `CylinderGeometry` (shaft) + `ConeGeometry` (head); shaft extends bidirectionally — from `center - dir×len` to `center + dir×shaftLen` (total shaft length = `shaftLen + len`); cone head on +direction side only; length=`item.length×2`, shaft radius=`len×0.03`, head radius=`shaftR×3`, head length=`len×0.25`; per-item visibility key `axis_{name}`; dimmed opacity 0.25 when `rhRefActive`

**`OverlayPanel.tsx`** (backend-driven)
- 5-tab `Tabs` (pills): Parts / Box / Plane / Point / Axis (Axis tab hidden when `axes.length === 0`)
- Parts tab: `parts_groups[]` badges → click to filter `PartListPanel`
- Box tab: `OverlaySwitch` per box item + Domain Parts section; `TabMasterSwitch`
- Plane tab: TG Ground / TG Body / section cuts; `TabMasterSwitch`
- Point tab: per probe with point count; `TabMasterSwitch`
- Axis tab: **Wheels** section (FR_LH=red, FR_RH=blue, RR_LH=orange, RR_RH=green) + **Porous** section (purple); per-item `ColorSwatch` + `OverlaySwitch`; sub-label shows `center (x, y, z) m  |  axis [dx, dy, dz]`; `TabMasterSwitch`
- **RH Ref toggle is NOT in this panel** — it lives in `ViewerToolbar` (see below)

**`PartListPanel.tsx`**
- Per-part row: click name → `setSelectedPartName`; `IconFocusCentered` → `setFitToTarget`; eye toggle; `ColorSwatch` (96 swatches); opacity Popover
- Toolbar: Toggle all filtered · Show Only · Invert · Show all
- Search bar + `SegmentedControl` (Include / Exclude); `matchesPattern()` matching rules:
  - No `*` → **substring match** (case-insensitive) — `"wheel"` matches `_wheel`, `wheels_body`, `front_wheels_lh`
  - With `*` → glob: `Body_*` = startsWith, `*_Body` = endsWith, `*_Body_*` = contains

**`RunViewer.tsx`** (embedded in `CaseDetailPage`, Runs tab)
- Fetches overlay data via `GET /cases/{id}/runs/{rid}/overlay` → `OverlayData`
- Fetches belt GLB via `GET /cases/{id}/runs/{rid}/belt-glb` when `run.belt_stl_path` is set; passes `beltGlbUrl` to `SceneCanvas`
- Fetches axes GLB via `GET /cases/{id}/runs/{rid}/axes-glb` when run is ready; passes `axesGlbUrl` to `SceneCanvas`
- Inline toolbar (top-right of canvas): Persp/Ortho toggle, Flat shading, Edges, Show Overlay, Show RH Ref (conditional on `overlayData?.ride_height_ref`)
- Also renders `<OverlayPanel>` below the canvas and `<OverlayObjects>` inside the canvas

**`TemplateBuilderPage.tsx`** (route: `/template-builder`)
- 3-column layout: 275px ControlPanel | 255px PartListPanel | flex-1 SceneCanvas
- Overlay data flow: `useQuery(["preview", "overlay", templateId, assemblyId])` → `previewApi.getOverlayData()` → `OverlayData` → passed to `OverlayPanel` + `OverlayObjects`
- `AssemblyGeometriesDrawer` opened via `IconPackage` ActionIcon
- `TemplateVersionEditModal` opened via `IconPencil` ActionIcon (gated on `editTemplateOpen`); **invalidates `["preview", "overlay"]` query on save** so viewer refreshes
- `TemplateVersionsDrawer`: **invalidates `["preview", "overlay"]` query on version activate**
- `CreateCaseFromBuilderModal` opened via `IconPlus` button
- `ViewerToolbar`: floating overlay (top-right of canvas); accepts `overlayData: OverlayData | null`; controls Persp/Ortho `SegmentedControl`, Flat shading Switch, Edges Switch; shows **RH Ref Switch** (reads/sets `rhRefVisible` from `viewerStore`) only when `overlayData.ride_height_ref` is present

### API Client

**`src/api/preview.ts`**
- `previewApi.getOverlayData(templateId, assemblyId) -> Promise<OverlayData>`
- Exports: `OverlayData`, `OverlayBoxItem`, `OverlayPlaneItem`, `OverlayDomainPartItem`, `OverlayProbeItem`, `OverlayPartsGroup`, `OverlayRideHeightRef`, `OverlayAxisItem`

**`src/api/systems.ts`**
- `systemsApi.list()`, `.get(id)`, `.delete(id)`, `.getLandmarksGlbUrl(id)`
- `transformApi.transform(geometryId, data: TransformRequest) -> TransformResult`

## Geometry Upload / Link Decimation Slider

- `Slider` (min=0.01, max=1.0, step=0.01) with marks at 5%/25%/50%/Skip
- `>= 1.0` → "Skip — no 3D preview" warning; no GLB generated
- `decimationRatio` passed to `geometriesApi.upload()` / `geometriesApi.link()`
