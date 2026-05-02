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

- `extract_overlay_data(deck: UfxSolverDeck, template_settings, all_part_names) -> OverlayData` — absolute coords; **reusable** for Case Viewer via `parse_ufx(xml_path)`
- `compute_overlay_data(db, template_id, assembly_id) -> OverlayData` — loads from DB, calls `assemble_ufx_solver_deck()` in memory, then `extract_overlay_data()`

### `app/schemas/overlay.py`

- `OverlayBoxItem`: `name`, `vis_key`, `level`, bbox coords, `color`, `category` (`"domain"` / `"refinement"` / `"porous"` / `"partial_volume"`)
- `OverlayPlaneItem`: `name`, `vis_key`, `type` (`"tg_ground"` / `"tg_body"` / `"section_cut"`), `position`, `normal`, `width`, `height`, `color`
- `OverlayDomainPartItem`: `name`, `vis_key`, `location`, `export_mesh`, bbox, `z_position`, `color`
- `OverlayProbeItem`: `name`, `vis_key`, `points`, `radius`
- `OverlayData`: `boxes`, `planes`, `domain_parts`, `probes`, `parts_groups`, `ground_z`

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/geometries/{id}/glb?ratio=` | Decimated GLB (cache or generate); `ratio` optional — defaults to `geometry.decimation_ratio` if omitted |
| `GET` | `/preview/overlay` | OverlayData for Template × Assembly |
| `GET` | `/cases/{id}/runs/{rid}/axes-glb` | On-demand axes GLB |
| `GET` | `/cases/{id}/runs/{rid}/overlay` | OverlayData from generated XML |

### Decimation Pipeline

1. `STLReader.read(stl_path)` — ASCII+Binary auto-detect → `list[Solid]`
2. `ProcessPoolExecutor` → `_decimate_worker(idx, solid, ratio)` per solid — parallel pure-Python QEM
3. `GLBExporter.export(valid_solids, cache_path)` — GLB 2.0, flat normals, PALETTE colors

`stl_decimator.py` lives at `backend/app/services/stl_decimator.py` — pure Python + NumPy, no trimesh/fast-simplification.

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
```

`partColor(name)` — deterministic per-part color (djb2 hash → 12-color SWATCHES palette).

### Key Frontend Components

**`SceneCanvas.tsx`**
- Props: `geometries: GeometryResponse[]`, `overlayData?: OverlayData | null`, `vehicleBbox?`. **No `ratio` prop** — GLB is fetched with `getGlbBlobUrl(g.id, g.decimation_ratio)` per geometry
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

**`OverlayPanel.tsx`** (backend-driven)
- 4-tab `Tabs` (pills): Parts / Box / Plane / Probe
- Parts tab: `parts_groups[]` badges → click to filter `PartListPanel`
- Box tab: `OverlaySwitch` per box item + Domain Parts section; `TabMasterSwitch`
- Plane tab: TG Ground / TG Body / section cuts; `TabMasterSwitch`
- Probe tab: per probe with point count; `TabMasterSwitch`

**`PartListPanel.tsx`**
- Per-part row: click name → `setSelectedPartName`; `IconFocusCentered` → `setFitToTarget`; eye toggle; `ColorSwatch` (96 swatches); opacity Popover
- Toolbar: Toggle all filtered · Show Only · Invert · Show all
- Search bar + `SegmentedControl` (Include / Exclude)

**`TemplateBuilderPage.tsx`** (route: `/template-builder`)
- 3-column layout: 275px ControlPanel | 255px PartListPanel | flex-1 SceneCanvas
- Overlay data flow: `useQuery(["preview", "overlay", templateId, assemblyId])` → `previewApi.getOverlayData()` → `OverlayData` → passed to `OverlayPanel` + `OverlayObjects`
- `AssemblyGeometriesDrawer` opened via `IconPackage` ActionIcon
- `TemplateVersionEditModal` opened via `IconPencil` ActionIcon (gated on `editTemplateOpen`)
- `CreateCaseFromBuilderModal` opened via `IconPlus` button

### API Client

**`src/api/preview.ts`**
- `previewApi.getOverlayData(templateId, assemblyId) -> Promise<OverlayData>`

**`src/api/systems.ts`**
- `systemsApi.list()`, `.get(id)`, `.delete(id)`, `.getLandmarksGlbUrl(id)`
- `transformApi.transform(geometryId, data: TransformRequest) -> TransformResult`

## Geometry Upload / Link Decimation Slider

- `Slider` (min=0.01, max=1.0, step=0.01) with marks at 5%/25%/50%/Skip
- `>= 1.0` → "Skip — no 3D preview" warning; no GLB generated
- `decimationRatio` passed to `geometriesApi.upload()` / `geometriesApi.link()`
