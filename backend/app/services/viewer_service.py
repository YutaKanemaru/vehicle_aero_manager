"""
3D Viewer用のGLBファイル生成・キャッシュサービス。

stl_decimator.STLReader で ASCII/Binary STL を読み込み (trimesh 不使用)、
ProcessPoolExecutor でパーツ並列 QEM デシメーション → GLBExporter で出力する。
外部依存: numpy のみ (fast-simplification / trimesh 不要)。
"""
from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from app.config import settings
from app.models.geometry import Geometry
from app.services.stl_decimator import (
    GLBExporter,
    Solid,
    STLReader,
    _decimate_worker,
)

logger = logging.getLogger(__name__)

# デフォルト保持率 (ratio = fraction to keep, 0.01〜1.0)
DEFAULT_RATIO: float = 0.05


def _get_stl_path(geometry: Geometry) -> Path:
    if geometry.is_linked:
        return Path(geometry.file_path)
    return settings.upload_dir / geometry.file_path


def _get_cache_path(geometry_id: str, ratio: float) -> Path:
    return settings.viewer_cache_dir / f"{geometry_id}_{ratio:.3f}.glb"


def get_cached_glb(geometry_id: str, ratio: float) -> bytes | None:
    """キャッシュされたGLBバイト列を返す。なければ None。"""
    cache_path = _get_cache_path(geometry_id, ratio)
    if cache_path.exists():
        return cache_path.read_bytes()
    return None


def build_viewer_glb(geometry: Geometry, ratio: float = DEFAULT_RATIO) -> bytes:
    """
    STL を読み込み → パーツ並列 QEM デシメーション → GLB 変換・キャッシュ。

    ratio: 保持率 (0.01〜1.0)。例: 0.5 = 元の50%を残す, 0.1 = 10%を残す。
    STLReader が ASCII / Binary 両形式を自動判定する。
    ProcessPoolExecutor で各パーツを独立して decimation する
    (trimesh / fast-simplification 不使用)。
    """
    if not (0.01 <= ratio <= 1.0):
        raise ValueError(f"ratio must be between 0.01 and 1.0, got {ratio}")

    stl_path = _get_stl_path(geometry)

    logger.info(
        "Building GLB for geometry=%s ratio=%.1f%%",
        geometry.id, ratio * 100,
    )

    # STL 読み込み (ASCII + Binary 自動判定)
    solids: list[Solid] = STLReader.read(stl_path)
    logger.info("  Parsed %d solid(s) from %s", len(solids), stl_path.name)

    if not solids:
        raise ValueError(f"No valid solid found in STL: {stl_path}")

    # 並列 QEM デシメーション
    decimated: list[Solid | None] = [None] * len(solids)
    jobs = [(i, s, ratio) for i, s in enumerate(solids)]

    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(_decimate_worker, job): job[0] for job in jobs}
        for future in as_completed(futures):
            try:
                idx, result, elapsed = future.result()
                decimated[idx] = result
                logger.debug(
                    "  Part %d/%d: %d → %d faces [%.1fs]",
                    idx + 1, len(solids),
                    len(solids[idx].faces), len(result.faces), elapsed,
                )
            except Exception as e:
                idx = futures[future]
                logger.error("Decimation failed for part %d (%s): %s", idx, solids[idx].name, e)

    valid: list[Solid] = [s for s in decimated if s is not None and len(s.faces) > 0]
    if not valid:
        raise ValueError(f"No valid mesh after decimation for STL: {stl_path}")

    # GLB 出力 → キャッシュ保存
    cache_path = _get_cache_path(geometry.id, ratio)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    GLBExporter.export(valid, cache_path)

    glb_bytes = cache_path.read_bytes()
    logger.info("GLB cached at %s (%d bytes)", cache_path, len(glb_bytes))
    return glb_bytes


def invalidate_cache(geometry_id: str) -> None:
    """指定ジオメトリの全キャッシュ（全ratio）を削除する。"""
    for cache_file in settings.viewer_cache_dir.glob(f"{geometry_id}_*.glb"):
        cache_file.unlink()
        logger.debug("Removed viewer cache: %s", cache_file)


# ─────────────────────────────────────────────────────────────────────────────
# Axis visualisation helpers
# ─────────────────────────────────────────────────────────────────────────────

import math
import tempfile

import numpy as np


def _rotation_matrix_to_direction(d: "np.ndarray") -> "np.ndarray":
    """3×3 rotation matrix that maps +Z → unit vector *d* (Rodrigues formula)."""
    z = np.array([0.0, 0.0, 1.0])
    d = np.asarray(d, dtype=float)
    norm = np.linalg.norm(d)
    if norm < 1e-9:
        return np.eye(3)
    d = d / norm
    cos_a = float(np.dot(z, d))
    cross = np.cross(z, d)
    sin_a = float(np.linalg.norm(cross))
    if sin_a < 1e-9:
        # Parallel or anti-parallel
        return np.eye(3) if cos_a > 0 else np.diag([1.0, -1.0, -1.0])
    k = cross / sin_a
    K = np.array([
        [0.0,  -k[2],  k[1]],
        [k[2],   0.0, -k[0]],
        [-k[1],  k[0],  0.0],
    ])
    return np.eye(3) + sin_a * K + (1.0 - cos_a) * (K @ K)


def _make_arrow_solid(
    name: str,
    origin: "np.ndarray",
    direction: "np.ndarray",
    length: float,
    shaft_radius: float,
    n_seg: int = 16,
) -> "Solid":
    """Cylinder + cone arrow solid pointing in *direction* from *origin*.

    The arrow is built along +Z then rotated to *direction*.
    """
    tip_ratio = 0.30
    shaft_len = length * (1.0 - tip_ratio)
    tip_len   = length * tip_ratio
    tip_r     = shaft_radius * 2.5

    theta = np.linspace(0.0, 2.0 * math.pi, n_seg, endpoint=False)
    cos_t, sin_t = np.cos(theta), np.sin(theta)

    # ── Cylinder ─────────────────────────────────────────────────
    #   verts: 0..n-1 bottom ring, n..2n-1 top ring, 2n bot centre, 2n+1 top centre
    bot = np.stack([cos_t * shaft_radius, sin_t * shaft_radius, np.zeros(n_seg)], axis=1)
    top = np.stack([cos_t * shaft_radius, sin_t * shaft_radius, np.full(n_seg, shaft_len)], axis=1)
    cyl_verts = np.vstack([bot, top, [[0, 0, 0]], [[0, 0, shaft_len]]])

    cyl_faces: list[list[int]] = []
    bc, tc = 2 * n_seg, 2 * n_seg + 1
    for i in range(n_seg):
        j = (i + 1) % n_seg
        cyl_faces += [[i, j, n_seg + j], [i, n_seg + j, n_seg + i]]   # side
        cyl_faces.append([bc, (i + 1) % n_seg, i])                     # bottom cap
        cyl_faces.append([tc, n_seg + i, n_seg + (i + 1) % n_seg])    # top cap

    # ── Cone ─────────────────────────────────────────────────────
    #   verts: 0..n-1 base ring, n apex, n+1 base centre
    cone_base = np.stack([cos_t * tip_r, sin_t * tip_r, np.full(n_seg, shaft_len)], axis=1)
    cone_verts = np.vstack([cone_base, [[0, 0, shaft_len + tip_len]], [[0, 0, shaft_len]]])
    apex_i, base_c_i = n_seg, n_seg + 1

    cone_faces: list[list[int]] = []
    for i in range(n_seg):
        j = (i + 1) % n_seg
        cone_faces.append([i, j, apex_i])           # lateral
        cone_faces.append([base_c_i, j, i])         # base cap

    v_off = len(cyl_verts)
    all_verts = np.vstack([cyl_verts, cone_verts]).astype(np.float32)
    all_faces = np.vstack([
        np.array(cyl_faces, dtype=np.int32),
        np.array(cone_faces, dtype=np.int32) + v_off,
    ])

    # Rotate +Z → direction, then translate
    R = _rotation_matrix_to_direction(direction)
    all_verts = (R @ all_verts.T).T.astype(np.float32) + np.asarray(origin, dtype=np.float32)

    return Solid(name=name, verts=all_verts, faces=all_faces)


def _make_sphere_solid(
    name: str,
    center: "np.ndarray",
    radius: float,
    lat_div: int = 8,
    lon_div: int = 16,
) -> "Solid":
    """UV sphere solid centred at *center*."""
    verts: list[list[float]] = [[0.0, 0.0, radius]]  # north pole idx=0
    n_rings = lat_div - 1
    for i in range(1, lat_div):
        phi = math.pi * i / lat_div
        z_v, r_v = radius * math.cos(phi), radius * math.sin(phi)
        for j in range(lon_div):
            t = 2.0 * math.pi * j / lon_div
            verts.append([r_v * math.cos(t), r_v * math.sin(t), z_v])
    verts.append([0.0, 0.0, -radius])  # south pole, last index
    s_pole_i = len(verts) - 1
    v_arr = np.array(verts, dtype=np.float32) + np.asarray(center, dtype=np.float32)

    faces: list[list[int]] = []
    # Top cap
    for j in range(lon_div):
        faces.append([0, 1 + j, 1 + (j + 1) % lon_div])
    # Middle bands
    for i in range(n_rings - 1):
        rs, rn = 1 + i * lon_div, 1 + (i + 1) * lon_div
        for j in range(lon_div):
            a, b = rs + j, rs + (j + 1) % lon_div
            c, d = rn + (j + 1) % lon_div, rn + j
            faces += [[a, b, c], [a, c, d]]
    # Bottom cap
    lr = 1 + (n_rings - 1) * lon_div
    for j in range(lon_div):
        faces.append([lr + j, lr + (j + 1) % lon_div, s_pole_i])

    return Solid(name=name, verts=v_arr, faces=np.array(faces, dtype=np.int32))


def build_axes_glb(
    template_settings: "object",  # TemplateSettings
    analysis_result: dict,
    stl_paths: "list[Path]",
    inflow_velocity: float,
) -> bytes:
    """Generate a GLB containing wheel-rotation-axis arrows + wheel-centre spheres
    + porous-flow-direction arrows for the given template / geometry combo.

    Returns raw GLB bytes (no caching — the payload is small).
    """
    from app.services.compute_engine import (
        _find_rim_vertices_for_wheel,
        _matches_any,
        classify_wheels,
        compute_porous_axis,
        compute_wheel_kinematics,
        extract_pca_axes,
    )

    part_info: dict = analysis_result.get("part_info", {})
    tn = template_settings.target_names  # type: ignore[attr-defined]

    porous_patterns = [pc.part_name for pc in template_settings.porous_coefficients]  # type: ignore[attr-defined]
    rim_patterns    = list(tn.rim)

    pca_axes       = extract_pca_axes(stl_paths, porous_patterns, rim_patterns)
    porous_verts_m = pca_axes.get("porous", {})
    rim_verts_m    = pca_axes.get("rim",    {})

    wheel_map = classify_wheels(analysis_result, tn)

    solids: list[Solid]                          = []
    colors: list[tuple[float, float, float, float]] = []

    CORNER_COLORS: dict[str, tuple[float, float, float, float]] = {
        "fr_lh": (1.00, 0.25, 0.25, 1.0),   # red
        "fr_rh": (0.25, 0.45, 1.00, 1.0),   # blue
        "rr_lh": (1.00, 0.60, 0.00, 1.0),   # orange
        "rr_rh": (0.10, 0.85, 0.10, 1.0),   # green
    }
    POROUS_COLOR: tuple[float, float, float, float] = (0.65, 0.00, 0.90, 1.0)  # purple

    for key, pi in wheel_map.items():
        rim_v = _find_rim_vertices_for_wheel(pi, rim_verts_m)
        kin   = compute_wheel_kinematics(pi, inflow_velocity, rim_v)

        origin = np.array([kin["center"]["x_pos"], kin["center"]["y_pos"], kin["center"]["z_pos"]])
        axis   = np.array([kin["axis"]["x_dir"],   kin["axis"]["y_dir"],   kin["axis"]["z_dir"]])
        radius = float(kin["radius"])
        color  = CORNER_COLORS.get(key, (0.8, 0.8, 0.8, 1.0))

        arrow_len  = radius * 0.80
        shaft_r    = arrow_len * 0.06

        solids.append(_make_arrow_solid(f"WheelAxis_{key.upper()}", origin, axis, arrow_len, shaft_r))
        colors.append(color)
        solids.append(_make_sphere_solid(f"WheelCenter_{key.upper()}", origin, radius * 0.06))
        colors.append(color)

    for pc in template_settings.porous_coefficients:  # type: ignore[attr-defined]
        # Merge all PCA vertices whose solid name matches the pattern
        matched_verts = [v for k, v in porous_verts_m.items() if _matches_any(k, [pc.part_name])]
        merged_verts  = np.vstack(matched_verts) if matched_verts else None

        # Find representative part_info entry
        centroid_pi: dict | None = None
        for name, pi in part_info.items():
            if _matches_any(name, [pc.part_name]):
                centroid_pi = pi
                break
        if centroid_pi is None:
            continue

        paxis    = compute_porous_axis(centroid_pi, merged_verts)
        centroid = np.array(centroid_pi["centroid"])
        bbox     = centroid_pi["bbox"]
        dims     = [
            bbox["x_max"] - bbox["x_min"],
            bbox["y_max"] - bbox["y_min"],
            bbox["z_max"] - bbox["z_min"],
        ]
        arrow_len = max(dims) * 0.6
        shaft_r   = min(dims) * 0.04
        axis_vec  = np.array([paxis["x_dir"], paxis["y_dir"], paxis["z_dir"]])

        solids.append(_make_arrow_solid(f"PorousAxis_{pc.part_name}", centroid, axis_vec, arrow_len, shaft_r))
        colors.append(POROUS_COLOR)

    if not solids:
        raise ValueError("No wheel or porous geometry found — cannot build axes GLB")

    with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
        tmp_path = Path(f.name)
    try:
        GLBExporter.export(solids, tmp_path, colors=colors)
        return tmp_path.read_bytes()
    finally:
        tmp_path.unlink(missing_ok=True)
