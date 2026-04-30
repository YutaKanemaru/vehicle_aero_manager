# Phase 2+ Roadmap

## Phase 2A: 3D Viewer / Template Builder — ✅ Complete

See [viewer-3d-spec.md](viewer-3d-spec.md) for full implementation details.

---

## Phase 2B: Post-Processing EnSight Viewer — 🔲 Planned

**Two modes of post-processing are planned:**

1. **GUI post-processing** (Three.js / React Three Fiber — reuse Phase 2A `SceneCanvas`)
   - 3D CFD result datasets (EnSight `.case` / `.h3d`) loaded in the existing viewer
   - Data coarsening to handle multiple full datasets efficiently
   - Robust multi-dataset comparison with synchronized camera state (Zustand)
   - Simulation info inherited from Ultrafluid log files

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

> Note: A lightweight post-processing viewer prototype already exists and can be provided when needed.

---

## Post-Processing Template

Separate from the simulation template — defines post-processing settings (visualization parameters, section cut positions, legend ranges, view angles, etc.).

---

## Data Management System

Cross-domain data lifecycle management throughout the CFD process:
- **Pre**: CAD data from structural section, scan data from design team
- **Solve**: Ultrafluid setting files, Ultrafluid results (.case/h3d)
- **Post**: Result tables, images/movies via viewer, report generation, GSP data

---

## Job Scheduler Integration

Integration with HPC job schedulers (PBS, Slurm) to:
- Submit solver jobs from the application
- Automate file transfer between local storage and compute nodes
- Track job status and retrieve results
