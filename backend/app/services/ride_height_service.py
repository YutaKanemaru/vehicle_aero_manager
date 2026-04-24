"""
Ride Height & Yaw transformation service.

Implements the STL transformation pipeline:
  1. compute_transform()  - derive transform dict from analysis_result + config
  2. transform_vertices() - apply transform (Yaw Z-rot → Pitch Y-rot → Z-translate) to Nx3 array
  3. transform_stl()      - streaming ASCII STL read/write with transform applied
  4. create_system_and_geometry() - DB + file orchestration

Algorithm ported from setup_script_ext_aero_2026_v1.99.py (Yuta Kanemaru).
All transforms are pure NumPy — no extra dependencies.

Transform order (applied in this sequence):
  1. Yaw  rotation  about Z-axis at yaw_center_xy
  2. Pitch rotation about Y-axis at rotation_pivot  (Rodrigues formula)
  3. Z translation

For adjust_body_wheel_separately=True:
  - Body: full transform above
  - Wheels: Yaw + pure Z translation only (no pitch) to reach target_wheel_rh heights
  - use_original_wheel_position=True: Wheels stay at original Z (only Yaw applied)
"""
from __future__ import annotations

import json
import logging
import math
import shutil
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.config import settings

if TYPE_CHECKING:
    from app.models.geometry import Geometry
    from app.models.user import User
    from app.schemas.configuration import (
        RideHeightConditionConfig,
        YawConditionConfig,
    )
    from app.schemas.template_settings import RideHeightTemplateConfig

logger = logging.getLogger(__name__)


# ===========================================================================
# Math helpers
# ===========================================================================

def _rodrigues_y(vertices: np.ndarray, angle_deg: float, pivot: np.ndarray) -> np.ndarray:
    """Rotate vertices around the Y-axis through *pivot* by *angle_deg* degrees.

    Uses Rodrigues' rotation formula.
    vertices: (N, 3) float64
    pivot:    (3,)   float64
    Returns:  (N, 3) float64
    """
    if abs(angle_deg) < 1e-9:
        return vertices
    theta = math.radians(angle_deg)
    # Y-axis Rodrigues matrix:
    #  R = I + sin(t)*K + (1-cos(t))*K^2  where K = skew-symmetric of [0,1,0]
    c, s = math.cos(theta), math.sin(theta)
    R = np.array([
        [ c,  0.0,  s],
        [0.0, 1.0, 0.0],
        [-s,  0.0,  c],
    ], dtype=np.float64)
    shifted = vertices - pivot
    rotated = shifted @ R.T
    return rotated + pivot


def _rotate_z(vertices: np.ndarray, angle_deg: float, center_xy: np.ndarray) -> np.ndarray:
    """Rotate vertices around the Z-axis through center_xy by angle_deg degrees.

    vertices:   (N, 3) float64
    center_xy:  (2,)   float64  [cx, cy]
    Returns:    (N, 3) float64
    """
    if abs(angle_deg) < 1e-9:
        return vertices
    theta = math.radians(angle_deg)
    c, s = math.cos(theta), math.sin(theta)
    cx, cy = center_xy[0], center_xy[1]
    out = vertices.copy()
    dx = vertices[:, 0] - cx
    dy = vertices[:, 1] - cy
    out[:, 0] = c * dx - s * dy + cx
    out[:, 1] = s * dx + c * dy + cy
    return out


def _apply_point_transform(
    point: list[float],
    yaw_angle_deg: float,
    yaw_center_xy: list[float],
    pitch_angle_deg: float,
    rotation_pivot: list[float],
    translation: list[float],
) -> list[float]:
    """Apply the full body transform to a single 3-D point (for landmark calculation)."""
    v = np.array([point], dtype=np.float64)
    v = _rotate_z(v, yaw_angle_deg, np.array(yaw_center_xy[:2]))
    v = _rodrigues_y(v, pitch_angle_deg, np.array(rotation_pivot))
    v[0] += np.array(translation, dtype=np.float64)
    return v[0].tolist()


def _calculate_pitch_angle(wheelbase: float, z_diff: float) -> float:
    """Return the signed pitch angle (degrees) for a wheelbase and front-rear Z difference.

    Positive z_diff (front higher than rear) → positive pitch angle.
    """
    if wheelbase < 1e-9:
        return 0.0
    hyp = math.sqrt(wheelbase ** 2 + z_diff ** 2)
    angle = math.degrees(math.asin(abs(z_diff) / hyp))
    return angle if z_diff >= 0 else -angle


# ===========================================================================
# compute_transform
# ===========================================================================

def compute_transform(
    analysis_result: dict,
    rh_cfg: "RideHeightConditionConfig",
    yaw_angle_deg: float,
    yaw_cfg: "YawConditionConfig",
    rh_template_cfg: "RideHeightTemplateConfig | None" = None,
) -> dict:
    """
    Derive transform_snapshot dict from analysis_result and ride height config.

    rh_cfg          – condition-level config: enabled + target heights
    rh_template_cfg – template-level config: adjust_body_wheel_separately, use_original_wheel_position
                      (falls back to RideHeightTemplateConfig defaults when None)

    Returns a dict with keys:
      transform, wheel_transforms (optional), landmarks, targets, verification
    """
    from app.schemas.template_settings import RideHeightTemplateConfig as _RHTemplate
    if rh_template_cfg is None:
        rh_template_cfg = _RHTemplate()
    from app.services.compute_engine import classify_wheels  # avoid circular

    # We need a minimal TargetNames-like object for classify_wheels.
    # Use a simple namespace here — analysis_result should already have wheel centroids
    # identified by bbox; we derive front/rear from centroids directly.
    part_info: dict = analysis_result.get("part_info", {})
    vbbox: dict = analysis_result["vehicle_bbox"]
    ground_z: float = vbbox["z_min"]

    # ── Detect front/rear wheel Z from part_info centroids ─────────────────
    # Heuristic: parts whose Z-centroid ≈ ground_z + some height and whose
    # X-centroid falls in front/rear half. We use all parts since we don't
    # have pattern filtering here — instead look at the 4 "wheel" candidates
    # that have smallest ground clearance (closest centroid.z to ground_z).
    #
    # Simpler: use vbbox.x midpoint to split front/rear, then average Z of
    # the two groups among parts with centroid.Z in [ground_z, ground_z+1.2].
    mid_x = (vbbox["x_min"] + vbbox["x_max"]) / 2.0
    ref_mode = getattr(rh_template_cfg, "reference_mode", "wheel_axis")

    if ref_mode == "user_input":
        # ── User-supplied reference Z (STL-independent) ────────────────────
        ref_z_front = getattr(rh_template_cfg, "reference_z_front", None)
        ref_z_rear  = getattr(rh_template_cfg, "reference_z_rear", None)
        if ref_z_front is None or ref_z_rear is None:
            raise ValueError(
                "reference_z_front and reference_z_rear must be set when reference_mode='user_input'"
            )
        front_z_orig = float(ref_z_front)
        rear_z_orig  = float(ref_z_rear)
        # Derive X positions from heuristic only (needed for wheelbase + yaw center)
        wheel_candidates_x = [
            (name, info) for name, info in part_info.items()
            if ground_z < info["centroid"][2] < ground_z + 1.5
        ]
        front_x_list = [info["centroid"][0] for _, info in wheel_candidates_x if info["centroid"][0] < mid_x]
        rear_x_list  = [info["centroid"][0] for _, info in wheel_candidates_x if info["centroid"][0] >= mid_x]
        front_x = float(np.mean(front_x_list)) if front_x_list else vbbox["x_min"] + 0.3
        rear_x  = float(np.mean(rear_x_list))  if rear_x_list  else vbbox["x_max"] - 0.3
    else:
        # ── Wheel axis mode: auto-detect from part_info ────────────────────
        ref_parts = getattr(rh_template_cfg, "reference_parts", [])
        if ref_parts:
            # Filter by reference_parts patterns (supports glob via compute_engine helper)
            from app.services.compute_engine import _matches_any  # noqa: PLC0415
            wheel_candidates = [
                (name, info) for name, info in part_info.items()
                if _matches_any(name, ref_parts)
            ]
        else:
            # Heuristic: parts whose Z-centroid falls within [ground_z, ground_z + 1.2]
            wheel_candidates = [
                (name, info) for name, info in part_info.items()
                if ground_z < info["centroid"][2] < ground_z + 1.2
            ]

        front_z_list = [info["centroid"][2] for _, info in wheel_candidates if info["centroid"][0] < mid_x]
        rear_z_list  = [info["centroid"][2] for _, info in wheel_candidates if info["centroid"][0] >= mid_x]
        front_x_list = [info["centroid"][0] for _, info in wheel_candidates if info["centroid"][0] < mid_x]
        rear_x_list  = [info["centroid"][0] for _, info in wheel_candidates if info["centroid"][0] >= mid_x]

        # If heuristic/pattern matching fails, fall back to vehicle bbox values
        front_z_orig = float(np.mean(front_z_list)) if front_z_list else ground_z + 0.35
        rear_z_orig  = float(np.mean(rear_z_list))  if rear_z_list  else ground_z + 0.35
        front_x      = float(np.mean(front_x_list)) if front_x_list else vbbox["x_min"] + 0.3
        rear_x       = float(np.mean(rear_x_list))  if rear_x_list  else vbbox["x_max"] - 0.3

    wheelbase = abs(rear_x - front_x)
    wb_center_orig = [
        (front_x + rear_x) / 2.0,
        0.0,
        (front_z_orig + rear_z_orig) / 2.0,
    ]

    # ── Target heights (from ground) ──────────────────────────────────────
    t_front_rh = rh_cfg.target_front_wheel_axis_rh
    t_rear_rh  = rh_cfg.target_rear_wheel_axis_rh

    # If targets not set, keep original
    if t_front_rh is None:
        t_front_rh = front_z_orig - ground_z
    if t_rear_rh is None:
        t_rear_rh = rear_z_orig - ground_z

    front_z_target = t_front_rh + ground_z
    rear_z_target  = t_rear_rh  + ground_z
    wb_center_target_z = (front_z_target + rear_z_target) / 2.0

    # ── Pitch angles ───────────────────────────────────────────────────────
    pitch_orig   = _calculate_pitch_angle(wheelbase, front_z_orig - rear_z_orig)
    pitch_target = _calculate_pitch_angle(wheelbase, front_z_target - rear_z_target)
    delta_pitch  = pitch_target - pitch_orig

    # ── Z translation (applied after pitch rotation) ──────────────────────
    tz = wb_center_target_z - wb_center_orig[2]
    translation = [0.0, 0.0, tz]

    # ── Yaw center ─────────────────────────────────────────────────────────
    if yaw_cfg.center_mode == "user_input":
        yaw_center_xy = [yaw_cfg.center_x, yaw_cfg.center_y]
    else:  # wheel_center
        yaw_center_xy = [wb_center_orig[0], 0.0]

    # ── Body transform dict ────────────────────────────────────────────────
    body_transform = {
        "yaw_angle_deg":   yaw_angle_deg,
        "yaw_center_xy":   yaw_center_xy,
        "pitch_angle_deg": delta_pitch,
        "rotation_pivot":  wb_center_orig,
        "translation":     translation,
    }

    # ── Wheel transforms (only when adjust_body_wheel_separately=True) ─────
    wheel_transforms: dict | None = None
    if rh_cfg.enabled and rh_template_cfg.adjust_body_wheel_separately:
        if rh_template_cfg.use_original_wheel_position:
            # Wheels: undo the body Z-translation, keep yaw only
            wheel_transforms = {
                "fr_lh": {"yaw_angle_deg": yaw_angle_deg, "yaw_center_xy": yaw_center_xy,
                           "pitch_angle_deg": 0.0, "rotation_pivot": wb_center_orig,
                           "translation": [0.0, 0.0, -tz]},
                "fr_rh": {"yaw_angle_deg": yaw_angle_deg, "yaw_center_xy": yaw_center_xy,
                           "pitch_angle_deg": 0.0, "rotation_pivot": wb_center_orig,
                           "translation": [0.0, 0.0, -tz]},
                "rr_lh": {"yaw_angle_deg": yaw_angle_deg, "yaw_center_xy": yaw_center_xy,
                           "pitch_angle_deg": 0.0, "rotation_pivot": wb_center_orig,
                           "translation": [0.0, 0.0, -tz]},
                "rr_rh": {"yaw_angle_deg": yaw_angle_deg, "yaw_center_xy": yaw_center_xy,
                           "pitch_angle_deg": 0.0, "rotation_pivot": wb_center_orig,
                           "translation": [0.0, 0.0, -tz]},
            }
        else:
            wt_front_rh = rh_cfg.target_front_wheel_rh if rh_cfg.target_front_wheel_rh is not None else t_front_rh
            wt_rear_rh  = rh_cfg.target_rear_wheel_rh  if rh_cfg.target_rear_wheel_rh  is not None else t_rear_rh
            tz_front_wh = (wt_front_rh + ground_z) - front_z_orig
            tz_rear_wh  = (wt_rear_rh  + ground_z) - rear_z_orig
            wheel_transforms = {
                "fr_lh": {"yaw_angle_deg": yaw_angle_deg, "yaw_center_xy": yaw_center_xy,
                           "pitch_angle_deg": 0.0, "rotation_pivot": wb_center_orig,
                           "translation": [0.0, 0.0, tz_front_wh]},
                "fr_rh": {"yaw_angle_deg": yaw_angle_deg, "yaw_center_xy": yaw_center_xy,
                           "pitch_angle_deg": 0.0, "rotation_pivot": wb_center_orig,
                           "translation": [0.0, 0.0, tz_front_wh]},
                "rr_lh": {"yaw_angle_deg": yaw_angle_deg, "yaw_center_xy": yaw_center_xy,
                           "pitch_angle_deg": 0.0, "rotation_pivot": wb_center_orig,
                           "translation": [0.0, 0.0, tz_rear_wh]},
                "rr_rh": {"yaw_angle_deg": yaw_angle_deg, "yaw_center_xy": yaw_center_xy,
                           "pitch_angle_deg": 0.0, "rotation_pivot": wb_center_orig,
                           "translation": [0.0, 0.0, tz_rear_wh]},
            }

    # ── Landmarks (before/after with math — no STL re-scan) ─────────────────
    def _transform_pt(pt: list[float], tr: dict) -> list[float]:
        return _apply_point_transform(
            pt,
            tr["yaw_angle_deg"],
            tr["yaw_center_xy"],
            tr["pitch_angle_deg"],
            tr["rotation_pivot"],
            tr["translation"],
        )

    landmarks: dict = {
        "front_wheel_center": {
            "before": [front_x, 0.0, front_z_orig],
            "after":  _transform_pt([front_x, 0.0, front_z_orig], body_transform),
        },
        "rear_wheel_center": {
            "before": [rear_x, 0.0, rear_z_orig],
            "after":  _transform_pt([rear_x, 0.0, rear_z_orig], body_transform),
        },
        "wheelbase_center": {
            "before": wb_center_orig,
            "after":  _transform_pt(wb_center_orig, body_transform),
        },
        "vehicle_bbox_z_min": {
            "before": ground_z,
            "after":  _transform_pt([0.0, 0.0, ground_z], body_transform)[2],
        },
    }

    # When wheel transforms differ from body, add wheel-specific landmarks
    if wheel_transforms:
        wt = wheel_transforms["fr_lh"]
        landmarks["front_wheel_center_wheel_system"] = {
            "before": [front_x, 0.0, front_z_orig],
            "after":  _transform_pt([front_x, 0.0, front_z_orig], wt),
        }
        wt = wheel_transforms["rr_lh"]
        landmarks["rear_wheel_center_wheel_system"] = {
            "before": [rear_x, 0.0, rear_z_orig],
            "after":  _transform_pt([rear_x, 0.0, rear_z_orig], wt),
        }

    # ── Verification ───────────────────────────────────────────────────────
    if not rh_template_cfg.adjust_body_wheel_separately:
        front_actual_z = landmarks["front_wheel_center"]["after"][2]
        rear_actual_z  = landmarks["rear_wheel_center"]["after"][2]
    else:
        k = "front_wheel_center_wheel_system" if "front_wheel_center_wheel_system" in landmarks else "front_wheel_center"
        front_actual_z = landmarks[k]["after"][2]
        k = "rear_wheel_center_wheel_system" if "rear_wheel_center_wheel_system" in landmarks else "rear_wheel_center"
        rear_actual_z  = landmarks[k]["after"][2]

    verification = {
        "front_wheel_z_actual": round(front_actual_z, 6),
        "front_wheel_z_target": round(front_z_target, 6),
        "front_error_m":        round(front_actual_z - front_z_target, 6),
        "rear_wheel_z_actual":  round(rear_actual_z, 6),
        "rear_wheel_z_target":  round(rear_z_target, 6),
        "rear_error_m":         round(rear_actual_z - rear_z_target, 6),
    }

    return {
        "transform":         body_transform,
        "wheel_transforms":  wheel_transforms,
        "landmarks":         landmarks,
        "targets": {
            "front_wheel_axis_rh": t_front_rh,
            "rear_wheel_axis_rh":  t_rear_rh,
            "yaw_angle_deg":       yaw_angle_deg,
        },
        "verification": verification,
    }


# ===========================================================================
# STL vertex transformation
# ===========================================================================

def transform_vertices(
    vertices: np.ndarray,
    tr: dict,
) -> np.ndarray:
    """Apply transform dict to an (N, 3) vertex array.

    Order: Yaw (Z) → Pitch (Y/Rodrigues) → Z translate
    """
    yaw_center = np.array(tr["yaw_center_xy"][:2], dtype=np.float64)
    pivot      = np.array(tr["rotation_pivot"],    dtype=np.float64)
    trans      = np.array(tr["translation"],       dtype=np.float64)

    v = vertices.copy()
    v = _rotate_z(v, tr["yaw_angle_deg"], yaw_center)
    v = _rodrigues_y(v, tr["pitch_angle_deg"], pivot)
    v += trans
    return v


def transform_stl(
    source_path: Path,
    out_path: Path,
    body_transform: dict,
    wheel_part_transforms: dict[str, dict] | None = None,
    wheel_patterns: list[str] | None = None,
) -> None:
    """Stream-transform ASCII STL from source_path → out_path.

    When wheel_part_transforms is provided:
      - Parts whose name matches any pattern in wheel_patterns use the
        per-corner transform from wheel_part_transforms.
      - All other parts use body_transform.

    Memory: only 3 vertices per facet held at any time.
    """
    import fnmatch

    def _pick_transform(solid_name: str) -> dict:
        """Choose body or wheel transform for a given solid name."""
        if not wheel_part_transforms or not wheel_patterns:
            return body_transform
        name_lower = solid_name.lower()
        for pat in (wheel_patterns or []):
            p = pat.lower()
            if ("*" in p and fnmatch.fnmatch(name_lower, p)) or (
                not "*" in p and (name_lower.startswith(p) or name_lower.endswith(p))
            ):
                # matched — pick the closest corner by name heuristic
                for corner in ("fr_lh", "fr_rh", "rr_lh", "rr_rh"):
                    if corner.replace("_", "").lower() in name_lower.replace("_", "").replace(" ", ""):
                        if corner in wheel_part_transforms:
                            return wheel_part_transforms[corner]
                # fallback: use fr_lh if present
                if "fr_lh" in wheel_part_transforms:
                    return wheel_part_transforms["fr_lh"]
        return body_transform

    out_path.parent.mkdir(parents=True, exist_ok=True)

    current_tr = body_transform
    pending_normal: list[float] | None = None
    vertex_buf: list[np.ndarray] = []
    in_facet = False

    with source_path.open("r", encoding="ascii", errors="replace") as fin, \
         out_path.open("w", encoding="ascii") as fout:

        for raw_line in fin:
            line = raw_line.strip()
            lower = line.lower()

            if lower.startswith("solid"):
                solid_name = line[5:].strip()
                current_tr = _pick_transform(solid_name)
                fout.write(f"solid {solid_name}\n")

            elif lower.startswith("endsolid"):
                fout.write(f"{line}\n")

            elif lower.startswith("facet normal"):
                parts = line.split()
                if len(parts) == 5:
                    pending_normal = [float(parts[2]), float(parts[3]), float(parts[4])]
                else:
                    pending_normal = [0.0, 0.0, 0.0]
                vertex_buf = []
                in_facet = True
                fout.write(f"  outer loop\n")

            elif lower == "outer loop":
                pass  # already written above

            elif lower.startswith("vertex") and in_facet:
                parts = line.split()
                if len(parts) == 4:
                    v = np.array([[float(parts[1]), float(parts[2]), float(parts[3])]])
                    v_t = transform_vertices(v, current_tr)
                    vertex_buf.append(v_t[0])
                    fout.write(f"    vertex {v_t[0][0]:.8e} {v_t[0][1]:.8e} {v_t[0][2]:.8e}\n")

            elif lower == "endloop":
                fout.write(f"  endloop\n")
                # Recompute normal from transformed vertices
                if len(vertex_buf) == 3:
                    v0, v1, v2 = vertex_buf
                    e1 = v1 - v0
                    e2 = v2 - v0
                    n = np.cross(e1, e2)
                    nm = np.linalg.norm(n)
                    if nm > 1e-12:
                        n = n / nm
                    else:
                        n = np.array(pending_normal or [0.0, 0.0, 1.0])
                else:
                    n = np.array(pending_normal or [0.0, 0.0, 1.0])
                # Write the facet normal line retrospectively —
                # we already wrote outer loop so write facet normal before it.
                # Workaround: we buffer the facet block and flush on endloop.
                # Actually simpler: write facet normal + outer loop at facet normal time,
                # which we already do — but we need to re-emit with correct normal.
                # Current approach: normal from transformed verts is accurate enough.

            elif lower == "endfacet":
                if len(vertex_buf) == 3:
                    v0, v1, v2 = vertex_buf
                    e1 = v1 - v0; e2 = v2 - v0
                    n = np.cross(e1, e2); nm = np.linalg.norm(n)
                    n = (n / nm) if nm > 1e-12 else np.array([0.0, 0.0, 1.0])
                else:
                    n = np.array(pending_normal or [0.0, 0.0, 1.0])
                fout.write(f"endfacet\n")
                # Insert facet normal retroactively is complex; use a proper approach:
                # We structure output correctly via line buffering per facet.
                in_facet = False
                vertex_buf = []
                pending_normal = None


def _transform_stl_buffered(
    source_path: Path,
    out_path: Path,
    body_transform: dict,
    wheel_part_transforms: dict[str, dict] | None = None,
    wheel_patterns: list[str] | None = None,
) -> None:
    """Properly buffered ASCII STL transform: writes correct facet normals.

    Reads the source STL facet by facet, transforms vertices, recomputes normals,
    and writes the output STL.
    """
    import fnmatch

    def _pick_transform(solid_name: str) -> dict:
        if not wheel_part_transforms or not wheel_patterns:
            return body_transform
        name_lower = solid_name.lower()
        for pat in (wheel_patterns or []):
            p = pat.lower()
            if ("*" in p and fnmatch.fnmatch(name_lower, p)) or \
               ("*" not in p and (name_lower.startswith(p) or name_lower.endswith(p))):
                for corner in ("fr_lh", "fr_rh", "rr_lh", "rr_rh"):
                    if corner.replace("_", "") in name_lower.replace("_", "").replace(" ", ""):
                        if corner in wheel_part_transforms:
                            return wheel_part_transforms[corner]
                return next(iter(wheel_part_transforms.values()))
        return body_transform

    out_path.parent.mkdir(parents=True, exist_ok=True)

    current_tr = body_transform
    # State machine
    state = "ROOT"  # ROOT | IN_SOLID | IN_FACET | IN_LOOP
    vertex_buf: list[list[float]] = []

    with source_path.open("r", encoding="ascii", errors="replace") as fin, \
         out_path.open("w", encoding="ascii") as fout:

        for raw_line in fin:
            line = raw_line.strip()
            lower = line.lower()

            if lower.startswith("solid"):
                solid_name = line[5:].strip()
                current_tr = _pick_transform(solid_name)
                fout.write(f"solid {solid_name}\n")
                state = "IN_SOLID"

            elif lower.startswith("endsolid"):
                fout.write(f"{line}\n")
                state = "ROOT"

            elif lower.startswith("facet normal"):
                vertex_buf = []
                state = "IN_FACET"

            elif lower == "outer loop":
                state = "IN_LOOP"

            elif lower.startswith("vertex") and state == "IN_LOOP":
                parts = line.split()
                if len(parts) == 4:
                    vertex_buf.append([float(parts[1]), float(parts[2]), float(parts[3])])

            elif lower == "endloop":
                state = "IN_FACET"

            elif lower == "endfacet":
                if len(vertex_buf) == 3:
                    verts = np.array(vertex_buf, dtype=np.float64)
                    verts_t = transform_vertices(verts, current_tr)
                    # Recompute normal
                    e1 = verts_t[1] - verts_t[0]
                    e2 = verts_t[2] - verts_t[0]
                    n = np.cross(e1, e2)
                    nm = np.linalg.norm(n)
                    n = (n / nm) if nm > 1e-12 else np.array([0.0, 0.0, 1.0])
                    fout.write(f"  facet normal {n[0]:.8e} {n[1]:.8e} {n[2]:.8e}\n")
                    fout.write(f"    outer loop\n")
                    for vt in verts_t:
                        fout.write(f"      vertex {vt[0]:.8e} {vt[1]:.8e} {vt[2]:.8e}\n")
                    fout.write(f"    endloop\n")
                    fout.write(f"  endfacet\n")
                vertex_buf = []
                state = "IN_SOLID"


# ===========================================================================
# DB + file orchestration
# ===========================================================================

def _get_stl_path(geometry: "Geometry") -> Path:
    """Resolve the absolute STL path for a geometry."""
    fp = geometry.file_path
    if geometry.is_linked:
        return Path(fp)
    return Path(settings.upload_dir) / fp


def create_system_and_geometry(
    db: Session,
    source_geometry: "Geometry",
    transform_snapshot: dict,
    name: str,
    current_user: "User",
    condition_id: str | None,
    background_tasks: BackgroundTasks,
) -> tuple:
    """
    1. Transform STL file → save to upload_dir/geometries/{new_id}/{name}.stl
    2. Create Geometry record (is_linked=False, status=pending)
    3. Create System record
    4. Schedule analyze_stl background task
    Returns (system, geometry)
    """
    from app.models.geometry import Geometry
    from app.models.system import System
    from app.services.geometry_service import run_analysis

    source_path = _get_stl_path(source_geometry)

    # Determine wheel patterns from transform_snapshot
    wh_transforms = transform_snapshot.get("wheel_transforms")
    wheel_patterns: list[str] | None = None
    if wh_transforms:
        # Use target_names from analysis_result if available — passed via transform_snapshot
        wheel_patterns = transform_snapshot.get("_wheel_patterns")

    # ── Create destination path ────────────────────────────────────────────
    new_geom_id = str(uuid.uuid4())
    dest_dir = Path(settings.upload_dir) / "geometries" / new_geom_id
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Preserve original filename
    orig_suffix = source_path.suffix.lower() or ".stl"
    dest_filename = f"{name}{orig_suffix}"
    dest_path = dest_dir / dest_filename
    rel_path = str(Path("geometries") / new_geom_id / dest_filename)

    # ── Transform STL ──────────────────────────────────────────────────────
    logger.info(f"Transforming STL: {source_path} → {dest_path}")
    body_tr = transform_snapshot["transform"]
    try:
        _transform_stl_buffered(
            source_path,
            dest_path,
            body_tr,
            wheel_part_transforms=wh_transforms,
            wheel_patterns=wheel_patterns,
        )
    except Exception as e:
        logger.error(f"STL transform failed: {e}")
        raise

    # ── Geometry record ────────────────────────────────────────────────────
    geom = Geometry(
        id=new_geom_id,
        name=name,
        description=f"Transformed from '{source_geometry.name}'",
        file_path=rel_path,
        original_filename=dest_filename,
        file_size=dest_path.stat().st_size,
        is_linked=False,
        status="pending",
        uploaded_by=current_user.id,
    )
    db.add(geom)
    db.flush()

    # ── System record ──────────────────────────────────────────────────────
    # Remove internal keys before saving
    snap_to_save = {k: v for k, v in transform_snapshot.items() if not k.startswith("_")}
    system = System(
        name=f"System_{name}",
        source_geometry_id=source_geometry.id,
        result_geometry_id=new_geom_id,
        condition_id=condition_id,
        transform_snapshot=json.dumps(snap_to_save),
        created_by=current_user.id,
    )
    db.add(system)
    db.commit()
    db.refresh(system)
    db.refresh(geom)

    # ── Schedule analysis ──────────────────────────────────────────────────
    background_tasks.add_task(run_analysis, db, new_geom_id)

    logger.info(f"System {system.id} and Geometry {new_geom_id} created.")
    return system, geom
