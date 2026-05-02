"""
Belt STL generation service.

Creates a multi-solid ASCII STL file containing 5 thin-box belt geometries
(4 wheel belts + 1 center belt) for the rotating_belt_5 ground mode.
Each belt is a 0.002mm thick box centered on vehicle ground_z.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from app.schemas.template_settings import Belt5Config

logger = logging.getLogger(__name__)

# Belt thickness: ±0.001mm from ground_z (total 0.002mm)
_HALF_THICKNESS: float = 0.000001  # 0.001mm in metres


# ─── STL geometry helpers ────────────────────────────────────────────────────

def _write_box_solid(
    name: str,
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    z_min: float, z_max: float,
) -> str:
    """Generate ASCII STL text for a thin box (6 faces × 2 triangles = 12 triangles)."""
    lines: list[str] = [f"solid {name}"]

    def _tri(n: tuple[float, float, float], v1: tuple, v2: tuple, v3: tuple) -> None:
        lines.append(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}")
        lines.append("    outer loop")
        lines.append(f"      vertex {v1[0]:.9e} {v1[1]:.9e} {v1[2]:.9e}")
        lines.append(f"      vertex {v2[0]:.9e} {v2[1]:.9e} {v2[2]:.9e}")
        lines.append(f"      vertex {v3[0]:.9e} {v3[1]:.9e} {v3[2]:.9e}")
        lines.append("    endloop")
        lines.append("  endfacet")

    # 8 corners
    v = [
        (x_min, y_min, z_min),  # 0
        (x_max, y_min, z_min),  # 1
        (x_max, y_max, z_min),  # 2
        (x_min, y_max, z_min),  # 3
        (x_min, y_min, z_max),  # 4
        (x_max, y_min, z_max),  # 5
        (x_max, y_max, z_max),  # 6
        (x_min, y_max, z_max),  # 7
    ]

    # Bottom face (z_min) — normal (0, 0, -1)
    _tri((0, 0, -1), v[0], v[2], v[1])
    _tri((0, 0, -1), v[0], v[3], v[2])
    # Top face (z_max) — normal (0, 0, 1)
    _tri((0, 0, 1), v[4], v[5], v[6])
    _tri((0, 0, 1), v[4], v[6], v[7])
    # Front face (y_min) — normal (0, -1, 0)
    _tri((0, -1, 0), v[0], v[1], v[5])
    _tri((0, -1, 0), v[0], v[5], v[4])
    # Back face (y_max) — normal (0, 1, 0)
    _tri((0, 1, 0), v[2], v[3], v[7])
    _tri((0, 1, 0), v[2], v[7], v[6])
    # Left face (x_min) — normal (-1, 0, 0)
    _tri((-1, 0, 0), v[0], v[4], v[7])
    _tri((-1, 0, 0), v[0], v[7], v[3])
    # Right face (x_max) — normal (1, 0, 0)
    _tri((1, 0, 0), v[1], v[2], v[6])
    _tri((1, 0, 0), v[1], v[6], v[5])

    lines.append(f"endsolid {name}")
    return "\n".join(lines)


# ─── Main belt generation ────────────────────────────────────────────────────

def generate_belt5_stl(
    analysis_result: dict,
    belt5_cfg: "Belt5Config",
    ground_z: float,
    target_names: "object | None" = None,
) -> str:
    """Generate 5-belt ASCII STL content (multi-solid, one per belt).

    Parameters
    ----------
    analysis_result : dict
        Merged analysis result with ``part_info`` and ``vehicle_bbox``.
    belt5_cfg : Belt5Config
        Belt sizing and position configuration from template settings.
    ground_z : float
        Resolved ground Z coordinate (absolute).
    target_names : TargetNames or None
        If provided, uses ``classify_wheels()`` for wheel positions.

    Returns
    -------
    str
        Complete ASCII STL file content with 5 solids.
    """
    from app.services.compute_engine import classify_wheels, compute_wheel_kinematics

    # Classify wheels to get centroids
    part_info: dict = analysis_result.get("part_info", {})
    vbbox: dict = analysis_result.get("vehicle_bbox", {})

    # Build wheel_kin_map (simplified — just need center positions)
    wheel_kin_map: dict[str, dict] = {}
    if target_names is not None:
        wheel_map = classify_wheels(analysis_result, target_names)
        for key, winfo in wheel_map.items():
            # Only need center position, use dummy velocity
            kin = compute_wheel_kinematics(winfo, 1.0)
            wheel_kin_map[key] = kin
    else:
        # Fallback: infer from part_info heuristic
        mid_x = (vbbox.get("x_min", 0) + vbbox.get("x_max", 0)) / 2.0
        mid_y = (vbbox.get("y_min", 0) + vbbox.get("y_max", 0)) / 2.0
        ground_z_val = vbbox.get("z_min", 0)
        wheel_candidates = [
            (name, info) for name, info in part_info.items()
            if ground_z_val < info["centroid"][2] < ground_z_val + 1.2
        ]
        # Group by quadrant
        quadrants: dict[str, list] = {"fr_lh": [], "fr_rh": [], "rr_lh": [], "rr_rh": []}
        for name, info in wheel_candidates:
            cx, cy = info["centroid"][0], info["centroid"][1]
            front = "fr" if cx < mid_x else "rr"
            side = "lh" if cy < mid_y else "rh"
            quadrants[f"{front}_{side}"].append(info)
        for key, infos in quadrants.items():
            if infos:
                avg_x = sum(i["centroid"][0] for i in infos) / len(infos)
                avg_y = sum(i["centroid"][1] for i in infos) / len(infos)
                avg_z = sum(i["centroid"][2] for i in infos) / len(infos)
                wheel_kin_map[key] = {"center": {"x_pos": avg_x, "y_pos": avg_y, "z_pos": avg_z}}

    # Compute belt positions using same logic as _build_belt5_wall_instances
    bsw = belt5_cfg.belt_size_wheel
    bsc = belt5_cfg.belt_size_center

    # Belt Y positions from wheel centroids
    belt_y_positions: dict[str, float] = {}
    for key in ("fr_lh", "fr_rh", "rr_lh", "rr_rh"):
        kin = wheel_kin_map.get(key)
        if kin:
            belt_y_positions[key] = kin["center"]["y_pos"]
        else:
            width = vbbox.get("y_max", 1) - vbbox.get("y_min", -1)
            y_mid = (vbbox.get("y_min", -1) + vbbox.get("y_max", 1)) / 2
            belt_y_positions["fr_lh"] = y_mid - width / 4
            belt_y_positions["fr_rh"] = y_mid + width / 4
            belt_y_positions["rr_lh"] = y_mid - width / 4
            belt_y_positions["rr_rh"] = y_mid + width / 4
            break

    # Narrow car fallback
    if belt5_cfg.narrow_car_fallback.enabled:
        min_gap = belt5_cfg.narrow_car_fallback.min_belt_gap
        for lh_key, rh_key in (("fr_lh", "fr_rh"), ("rr_lh", "rr_rh")):
            gap = belt_y_positions.get(rh_key, 0) - belt_y_positions.get(lh_key, 0)
            if gap < min_gap:
                mid = (belt_y_positions.get(lh_key, 0) + belt_y_positions.get(rh_key, 0)) / 2
                belt_y_positions[lh_key] = mid - min_gap / 2
                belt_y_positions[rh_key] = mid + min_gap / 2

    # Z bounds for thin belts
    z_bot = ground_z - _HALF_THICKNESS
    z_top = ground_z + _HALF_THICKNESS

    solids: list[str] = []

    # 4 wheel belts
    for key, belt_label in (
        ("fr_lh", "Belt_Wheel_FR_LH"),
        ("fr_rh", "Belt_Wheel_FR_RH"),
        ("rr_lh", "Belt_Wheel_RR_LH"),
        ("rr_rh", "Belt_Wheel_RR_RH"),
    ):
        kin = wheel_kin_map.get(key)
        center_x = kin["center"]["x_pos"] if kin else (vbbox.get("x_min", 0) + vbbox.get("x_max", 0)) / 2
        belt_y = belt_y_positions.get(key, 0.0)
        solids.append(_write_box_solid(
            name=belt_label,
            x_min=center_x - bsw.x / 2,
            x_max=center_x + bsw.x / 2,
            y_min=belt_y - bsw.y / 2,
            y_max=belt_y + bsw.y / 2,
            z_min=z_bot,
            z_max=z_top,
        ))

    # Center belt
    # Compute center_xmin using same logic as _compute_belt5_center_xmin
    fr = wheel_kin_map.get("fr_lh") or wheel_kin_map.get("fr_rh")
    rr = wheel_kin_map.get("rr_lh") or wheel_kin_map.get("rr_rh")
    if belt5_cfg.center_belt_position == "user_specified" and belt5_cfg.center_belt_x_pos is not None:
        center_xmin = belt5_cfg.center_belt_x_pos - bsc.x / 2
    elif fr and rr:
        center_x = (fr["center"]["x_pos"] + rr["center"]["x_pos"]) / 2.0
        center_xmin = center_x - bsc.x / 2
    else:
        center_x = (vbbox.get("x_min", 0) + vbbox.get("x_max", 0)) / 2.0
        center_xmin = center_x - bsc.x / 2

    solids.append(_write_box_solid(
        name="Belt_Center",
        x_min=center_xmin,
        x_max=center_xmin + bsc.x,
        y_min=-bsc.y / 2,
        y_max=bsc.y / 2,
        z_min=z_bot,
        z_max=z_top,
    ))

    return "\n".join(solids) + "\n"


# ─── Yaw rotation for belt STL ───────────────────────────────────────────────

def rotate_belt_stl_yaw(
    stl_content: str,
    yaw_angle_deg: float,
    yaw_center_xy: tuple[float, float] = (0.0, 0.0),
) -> str:
    """Apply Z-axis yaw rotation to belt STL content (vertex-level transform).

    Only yaw rotation is applied — no pitch or Z-translation.
    """
    if abs(yaw_angle_deg) < 1e-9:
        return stl_content

    theta = math.radians(yaw_angle_deg)
    c, s = math.cos(theta), math.sin(theta)
    cx, cy = yaw_center_xy

    lines = stl_content.splitlines()
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("vertex ") or stripped.startswith("facet normal "):
            parts = stripped.split()
            if stripped.startswith("vertex "):
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                dx, dy = x - cx, y - cy
                nx = c * dx - s * dy + cx
                ny = s * dx + c * dy + cy
                indent = line[:len(line) - len(line.lstrip())]
                result.append(f"{indent}vertex {nx:.9e} {ny:.9e} {z:.9e}")
            else:  # facet normal
                nx_n, ny_n, nz_n = float(parts[2]), float(parts[3]), float(parts[4])
                nnx = c * nx_n - s * ny_n
                nny = s * nx_n + c * ny_n
                indent = line[:len(line) - len(line.lstrip())]
                result.append(f"{indent}facet normal {nnx:.6e} {nny:.6e} {nz_n:.6e}")
        else:
            result.append(line)
    return "\n".join(result) + "\n"


# ─── Service entry point for Run ──────────────────────────────────────────────

def generate_belt5_for_run(
    db: "Session",
    run: "Run",
) -> dict:
    """Generate 5-belt STL for a Run and save to the run's output directory.

    Returns dict with ``belt_stl_path`` and ``parts``.
    """
    import json as _json
    from sqlalchemy.orm import selectinload, Session  # noqa: F811
    from sqlalchemy import select

    from app.models.configuration import Case, Condition
    from app.models.geometry import GeometryAssembly, Geometry as GeometryModel
    from app.models.template import TemplateVersion
    from app.schemas.template_settings import TemplateSettings
    from app.services.configuration_service import _merge_analysis_results

    case = db.get(Case, run.case_id)
    condition = db.get(Condition, run.condition_id)

    # Load template settings
    active_version = db.scalar(
        select(TemplateVersion).where(
            TemplateVersion.template_id == case.template_id,
            TemplateVersion.is_active == True,  # noqa: E712
        )
    )
    if not active_version:
        raise ValueError("No active template version found")

    template_settings = TemplateSettings.model_validate(
        _json.loads(active_version.settings) if isinstance(active_version.settings, str) else active_version.settings
    )

    gc = template_settings.setup_option.boundary_condition.ground
    if gc.ground_mode != "rotating_belt_5":
        raise ValueError("Belt generation only applicable for rotating_belt_5 ground mode")

    # Load assembly + analysis
    assembly = db.scalar(
        select(GeometryAssembly)
        .options(selectinload(GeometryAssembly.geometries))
        .where(GeometryAssembly.id == case.assembly_id)
    )

    # Use override geometry analysis if available, else merged assembly
    if run.geometry_override_id:
        override_geom = db.get(GeometryModel, run.geometry_override_id)
        if override_geom and override_geom.analysis_result:
            analysis_result = _json.loads(override_geom.analysis_result) if isinstance(override_geom.analysis_result, str) else override_geom.analysis_result
        else:
            analysis_result = _merge_analysis_results(assembly)
    else:
        analysis_result = _merge_analysis_results(assembly)

    # Resolve ground_z
    vbbox = analysis_result.get("vehicle_bbox", {})
    if gc.ground_height_mode == "absolute":
        ground_z = gc.ground_height_absolute
    else:
        ground_z = vbbox.get("z_min", 0.0) + gc.ground_height_offset_from_geom_zMin

    # Generate STL
    belt5_cfg = gc.belt5
    stl_content = generate_belt5_stl(
        analysis_result=analysis_result,
        belt5_cfg=belt5_cfg,
        ground_z=ground_z,
        target_names=template_settings.target_names,
    )

    # Determine output filename
    # Use first geometry's original filename as base
    base_name = "geometry"
    if assembly and assembly.geometries:
        first_geom = assembly.geometries[0]
        base_name = Path(first_geom.original_filename or first_geom.name).stem

    out_dir = settings.runs_dir / run.id
    out_dir.mkdir(parents=True, exist_ok=True)
    belt_filename = f"{base_name}_5belts.stl"
    belt_path = out_dir / belt_filename
    belt_path.write_text(stl_content, encoding="utf-8")

    # Update run
    run.belt_stl_path = str(belt_path)
    db.commit()
    db.refresh(run)

    logger.info("Generated belt STL for run %s: %s", run.id, belt_path)
    return {
        "belt_stl_path": str(belt_path),
        "parts": ["Belt_Wheel_FR_LH", "Belt_Wheel_FR_RH", "Belt_Wheel_RR_LH", "Belt_Wheel_RR_RH", "Belt_Center"],
    }
