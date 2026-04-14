"""
Compute Engine — STL ファイルの解析モジュール + XML 組み立てエンジン

trimesh + numpy のみ使用。
numpy-stl / scikit-learn は使用しない。
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import trimesh

if TYPE_CHECKING:
    from app.schemas.template_settings import (
        ComputeOption, GroundConfig, TargetNames, TemplateSettings,
        TurbulenceGeneratorOption, Belt5Config,
    )
    from app.ultrafluid.schema import UfxSolverDeck


def _detect_stl_format(file_path: Path) -> str:
    """
    STL ファイルがアスキー形式かバイナリ形式かを判定する。

    Returns: "ascii" | "binary"

    判定ロジック:
      1. 先頭5バイトが b"solid" でなければ → "binary"
      2. b"solid" で始まる場合: ヘッダー後4バイトを uint32 として読み、
         80 + 4 + n_triangles * 50 == file_size が成立すれば → "binary"
         (バイナリ STL のヘッダーが偶然 "solid" で始まるケースに対応)
      3. 上記を満たさなければ → "ascii"
    """
    file_size = file_path.stat().st_size
    with file_path.open("rb") as f:
        header = f.read(84)

    if len(header) < 5:
        raise ValueError("STL file is too small to be valid.")

    if header[:5] != b"solid":
        return "binary"

    # "solid" で始まる場合 — バイナリの誤検出を排除
    if len(header) >= 84:
        n_triangles = struct.unpack("<I", header[80:84])[0]
        expected_size = 80 + 4 + n_triangles * 50
        if expected_size == file_size:
            return "binary"

    return "ascii"


def _parse_stl_ascii_streaming(
    file_path: Path,
    verbose: bool = False,
) -> dict[str, dict]:
    """
    ASCII STL をストリーミング解析してパーツ情報を返す。

    頂点配列を一切メモリに保持しない。
    各 solid ごとに min/max/sum/count のランニング統計のみ保持する。

    Returns: {part_name: {"centroid", "bbox", "vertex_count", "face_count"}}
    """
    def log(msg: str) -> None:
        if verbose:
            print(msg)

    part_info: dict[str, dict] = {}

    # per-solid running stats
    current_name: str | None = None
    x_min = x_max = y_min = y_max = z_min = z_max = 0.0
    vertex_count = 0
    face_count = 0
    solid_index = 0
    initialized = False  # 最初の vertex が来るまで bbox を初期化するフラグ

    with file_path.open("r", encoding="ascii", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            lower = line.lower()

            if lower.startswith("solid"):
                name_part = line[5:].strip()
                current_name = name_part if name_part else file_path.stem
                # 同名パーツが既にある場合はサフィックスを付与
                base_name = current_name
                suffix = 0
                while current_name in part_info:
                    suffix += 1
                    current_name = f"{base_name}_{suffix}"
                solid_index += 1
                vertex_count = 0
                face_count = 0
                initialized = False
                log(f"        Solid [{solid_index}]: {current_name}")

            elif lower.startswith("facet normal"):
                face_count += 1

            elif lower.startswith("vertex"):
                parts = line.split()
                if len(parts) == 4:
                    try:
                        px, py, pz = float(parts[1]), float(parts[2]), float(parts[3])
                    except ValueError:
                        continue
                    if not initialized:
                        x_min = x_max = px
                        y_min = y_max = py
                        z_min = z_max = pz
                        initialized = True
                    else:
                        if px < x_min: x_min = px
                        if px > x_max: x_max = px
                        if py < y_min: y_min = py
                        if py > y_max: y_max = py
                        if pz < z_min: z_min = pz
                        if pz > z_max: z_max = pz
                    vertex_count += 1

            elif lower.startswith("endsolid") and current_name is not None:
                if vertex_count == 0:
                    # 空の solid はスキップ
                    current_name = None
                    continue
                # バウンディングボックス中心を centroid として使用
                centroid = [
                    round((x_min + x_max) / 2.0, 6),
                    round((y_min + y_max) / 2.0, 6),
                    round((z_min + z_max) / 2.0, 6),
                ]
                part_info[current_name] = {
                    "centroid": centroid,
                    "bbox": {
                        "x_min": float(x_min),
                        "x_max": float(x_max),
                        "y_min": float(y_min),
                        "y_max": float(y_max),
                        "z_min": float(z_min),
                        "z_max": float(z_max),
                    },
                    "vertex_count": vertex_count,
                    "face_count": face_count,
                }
                current_name = None

    if not part_info:
        raise ValueError("No valid solid definitions found in STL file.")

    return part_info


def analyze_stl(file_path: Path, verbose: bool = False) -> dict:
    """
    STL ファイルを解析してパーツ情報・車両 bbox を返す。

    ASCII STL (マルチソリッド対応) のみサポート。
    バイナリ STL が検出された場合は ValueError を発生させる。

    verbose=True にすると各ステップの進捗を print する。
    """
    def log(msg: str) -> None:
        if verbose:
            print(msg)

    log(f"  [1/3] フォーマット検出: {file_path.name}")
    fmt = _detect_stl_format(file_path)
    if fmt == "binary":
        raise ValueError(
            "Binary STL format is not supported. "
            "Please convert the file to ASCII STL before uploading."
        )

    log(f"  [2/3] ASCII STL ストリーミング解析中...")
    part_info = _parse_stl_ascii_streaming(file_path, verbose=verbose)

    log(f"  [3/3] 車両全体 bbox 計算中 ({len(part_info)} parts)...")
    # vehicle bbox: 全パーツの bbox を union — np.concatenate 不使用
    all_bboxes = [p["bbox"] for p in part_info.values()]
    vehicle_bbox = {
        "x_min": min(b["x_min"] for b in all_bboxes),
        "x_max": max(b["x_max"] for b in all_bboxes),
        "y_min": min(b["y_min"] for b in all_bboxes),
        "y_max": max(b["y_max"] for b in all_bboxes),
        "z_min": min(b["z_min"] for b in all_bboxes),
        "z_max": max(b["z_max"] for b in all_bboxes),
    }

    vehicle_dimensions = {
        "length": round(float(vehicle_bbox["x_max"] - vehicle_bbox["x_min"]), 6),
        "width":  round(float(vehicle_bbox["y_max"] - vehicle_bbox["y_min"]), 6),
        "height": round(float(vehicle_bbox["z_max"] - vehicle_bbox["z_min"]), 6),
    }

    log("  ✅ 解析完了")
    return {
        "parts": list(part_info.keys()),
        "vehicle_bbox": vehicle_bbox,
        "vehicle_dimensions": vehicle_dimensions,
        "part_info": part_info,
    }


def analyze_stl_to_json(file_path: Path) -> str:
    """analyze_stl の結果を JSON 文字列で返す。"""
    return json.dumps(analyze_stl(file_path))


# ===========================================================================
# XML 組み立てエンジン (Step 5)
# ===========================================================================

# ---------------------------------------------------------------------------
# Timing / iteration helpers
# ---------------------------------------------------------------------------

def compute_dt(coarsest_mesh_size: float, inflow_velocity: float, mach_factor: float) -> float:
    """
    LBM タイムステップを計算する。

    dt = coarsest_mesh_size / (inflow_velocity × mach_factor × √3)

    √3 は LBM の音速スケーリング定数 (cs = 1/√3 × dx/dt)。
    """
    denom = inflow_velocity * mach_factor * math.sqrt(3.0)
    if denom <= 0:
        return 1e-4
    return coarsest_mesh_size / denom


def time_to_iterations(time_sec: float, dt: float) -> int:
    """秒 → コースメッシュのイテレーション数に変換。"""
    if dt <= 0 or time_sec <= 0:
        return 0
    return max(1, round(time_sec / dt))


def compute_finest_voxel_size(coarsest_voxel_size: float, n_levels: int) -> float:
    """finest = coarsest / 2^n_levels  (UI 表示用)"""
    return coarsest_voxel_size / (2 ** n_levels)


def compute_reference_length(wheel_kinematics_map: dict) -> float:
    """
    フロント軸とリア軸の車軸中心間距離（ホイールベース）を返す。

    wheel_kinematics_map: {"fr_lh": {"center": {...}, ...}, "rr_lh": ..., ...}
    FR と RR のどちらか側の center.x の差を使う。
    """
    fr = wheel_kinematics_map.get("fr_lh") or wheel_kinematics_map.get("fr_rh")
    rr = wheel_kinematics_map.get("rr_lh") or wheel_kinematics_map.get("rr_rh")
    if fr and rr:
        return abs(rr["center"]["x_pos"] - fr["center"]["x_pos"])
    return 1.0  # フォールバック


def compute_moment_reference_origin(wheel_kinematics_map: dict) -> dict:
    """
    FR / RR 車軸中心の X 中点を モーメント基準点として返す。

    Returns: {"x_pos": float, "y_pos": 0.0, "z_pos": float}
    """
    fr = wheel_kinematics_map.get("fr_lh") or wheel_kinematics_map.get("fr_rh")
    rr = wheel_kinematics_map.get("rr_lh") or wheel_kinematics_map.get("rr_rh")
    if fr and rr:
        x = (fr["center"]["x_pos"] + rr["center"]["x_pos"]) / 2.0
        z = (fr["center"]["z_pos"] + rr["center"]["z_pos"]) / 2.0
        return {"x_pos": x, "y_pos": 0.0, "z_pos": z}
    return {"x_pos": 0.0, "y_pos": 0.0, "z_pos": 0.0}


# ---------------------------------------------------------------------------
# Compute domain bbox
# ---------------------------------------------------------------------------

def compute_domain_bbox(
    vehicle_bbox: dict,
    multipliers: list[float],
    ground_z: float | None = None,
) -> dict:
    """
    車両 bbox の各辺を基準に factor * body_dimension だけ拡張して絶対的な bbox を返す。

    multipliers: [x_min_f, x_max_f, y_min_f, y_max_f, z_min_f, z_max_f]
    計算式: result[i] = factor[i] * dimension + bbox_edge[i]
      x_min: vehicle_bbox["x_min"] + x_min_f * x_length   (負値 = 前方拡張)
      x_max: vehicle_bbox["x_max"] + x_max_f * x_length   (正値 = 後方拡張)
      y_min: vehicle_bbox["y_min"] + y_min_f * y_length   (負値 = 側方拡張)
      y_max: vehicle_bbox["y_max"] + y_max_f * y_length
      z_min: ground_z    + z_min_f * z_length   (通常 0)
      z_max: vehicle_bbox["z_max"] + z_max_f * z_length
    ground_z が None の場合は vehicle_bbox["z_min"] を使用。
    """
    gz = ground_z if ground_z is not None else vehicle_bbox["z_min"]
    x_length = vehicle_bbox["x_max"] - vehicle_bbox["x_min"]
    y_length = vehicle_bbox["y_max"] - vehicle_bbox["y_min"]
    z_length = vehicle_bbox["z_max"] - vehicle_bbox["z_min"]

    x_min_f, x_max_f, y_min_f, y_max_f, z_min_f, z_max_f = multipliers

    return {
        "x_min": vehicle_bbox["x_min"] + x_min_f * x_length,
        "x_max": vehicle_bbox["x_max"] + x_max_f * x_length,
        "y_min": vehicle_bbox["y_min"] + y_min_f * y_length,
        "y_max": vehicle_bbox["y_max"] + y_max_f * y_length,
        "z_min": gz + z_min_f * z_length,
        "z_max": vehicle_bbox["z_max"] + z_max_f * z_length,
    }


def _matches_any(part_name: str, patterns: list[str]) -> bool:
    """パーツ名がパターンリストのいずれかに部分一致するか判定"""
    return any(p and p.lower() in part_name.lower() for p in patterns)


# ---------------------------------------------------------------------------
# Wheel classification & kinematics
# ---------------------------------------------------------------------------

def classify_wheels(
    analysis_result: dict,
    target_names: "TargetNames",
) -> dict[str, dict]:
    """
    analysis_result の part_info からホイール部品を FR-LH/FR-RH/RR-LH/RR-RH に分類する。

    個別 PID (wheel_tire_fr_lh 等) が指定されていればそれを優先。
    ない場合は target_names.wheel パターンにマッチした部品を重心で自動分類。

    Returns: {"fr_lh": part_info, "fr_rh": ..., "rr_lh": ..., "rr_rh": ...}
    """
    part_info: dict[str, dict] = analysis_result.get("part_info", {})

    explicit: dict[str, str] = {
        "fr_lh": target_names.wheel_tire_fr_lh,
        "fr_rh": target_names.wheel_tire_fr_rh,
        "rr_lh": target_names.wheel_tire_rr_lh,
        "rr_rh": target_names.wheel_tire_rr_rh,
    }

    result: dict[str, dict | None] = {"fr_lh": None, "fr_rh": None, "rr_lh": None, "rr_rh": None}

    if all(v for v in explicit.values()):
        for key, pid in explicit.items():
            result[key] = part_info.get(pid)
        return {k: v for k, v in result.items() if v is not None}

    # 自動分類: wheel パターンでマッチした部品を重心で振り分け
    wheel_parts = {
        name: info for name, info in part_info.items()
        if _matches_any(name, target_names.wheel)
        and not _matches_any(name, ["VREV_", "Overset"])
    }

    if not wheel_parts:
        return {}

    vbbox = analysis_result["vehicle_bbox"]
    cog_x = (vbbox["x_min"] + vbbox["x_max"]) / 2
    cog_y = (vbbox["y_min"] + vbbox["y_max"]) / 2

    for name, info in wheel_parts.items():
        cx, cy = info["centroid"][0], info["centroid"][1]
        front = "fr" if cx < cog_x else "rr"
        side  = "lh" if cy < cog_y else "rh"
        key = f"{front}_{side}"
        if result[key] is None:
            result[key] = info

    return {k: v for k, v in result.items() if v is not None}


def compute_wheel_kinematics(
    part_info: dict,
    inflow_velocity: float,
    rim_vertices: "np.ndarray | None" = None,
) -> dict:
    """
    ホイール情報から overset rotating インスタンスパラメータを計算する。

    Returns: {"center": XYZPos dict, "axis": XYZDir dict, "rpm": float, "radius": float}
    """
    bbox = part_info["bbox"]
    centroid = part_info["centroid"]

    radius_z = (bbox["z_max"] - bbox["z_min"]) / 2
    radius_y = (bbox["y_max"] - bbox["y_min"]) / 2
    radius = min(radius_z, radius_y) if radius_z > 0 and radius_y > 0 else max(radius_z, radius_y)

    if rim_vertices is not None and len(rim_vertices) >= 3:
        centered = rim_vertices - rim_vertices.mean(axis=0)
        _, _, vt = np.linalg.svd(centered, full_matrices=False)
        axis = vt[2]
        if axis[1] < 0:
            axis = -axis
        axis_dir = {"x_dir": float(axis[0]), "y_dir": float(axis[1]), "z_dir": float(axis[2])}
    else:
        axis_dir = {"x_dir": 0.0, "y_dir": 1.0, "z_dir": 0.0}

    circumference = 2 * math.pi * radius
    rpm = (inflow_velocity / circumference) * 60.0 if circumference > 0 else 0.0

    return {
        "center": {"x_pos": centroid[0], "y_pos": centroid[1], "z_pos": centroid[2]},
        "axis": axis_dir,
        "rpm": rpm,
        "radius": radius,
    }


def compute_porous_axis(part_info: dict, vertices: "np.ndarray | None" = None) -> dict:
    """ポーラス部品の主軸方向を PCA / bbox から返す。"""
    if vertices is not None and len(vertices) >= 3:
        centered = vertices - vertices.mean(axis=0)
        _, _, vt = np.linalg.svd(centered, full_matrices=False)
        axis = vt[0]
        if axis[0] < 0:
            axis = -axis
        return {"x_dir": float(axis[0]), "y_dir": float(axis[1]), "z_dir": float(axis[2])}

    bbox = part_info["bbox"]
    dims = {
        "x": bbox["x_max"] - bbox["x_min"],
        "y": bbox["y_max"] - bbox["y_min"],
        "z": bbox["z_max"] - bbox["z_min"],
    }
    thinnest = min(dims, key=dims.get)
    return {
        "x_dir": 1.0 if thinnest == "x" else 0.0,
        "y_dir": 1.0 if thinnest == "y" else 0.0,
        "z_dir": 1.0 if thinnest == "z" else 0.0,
    }


# ---------------------------------------------------------------------------
# Ground / belt / BL-suction helpers
# ---------------------------------------------------------------------------

def _resolve_no_slip_xmin(
    ground_cfg: "GroundConfig",
    belt5_center_xmin: float | None,
) -> float | None:
    """
    BL suction が有効な場合の no-slip x min 位置を解決する。

    Returns None if bl_suction.apply == False.
    """
    bl = ground_cfg.bl_suction
    if not bl.apply:
        return None  # 全面 no-slip、xmin 位置なし

    # 5-belt: center belt x_min から導出
    if (
        ground_cfg.ground_mode == "rotating_belt_5"
        and bl.no_slip_xmin_from_belt_xmin
        and belt5_center_xmin is not None
    ):
        return belt5_center_xmin + bl.bl_xmin_offset

    # それ以外: ユーザー直接指定
    if bl.no_slip_xmin_pos is not None:
        return bl.no_slip_xmin_pos

    return None


def _static_floor_dims(
    vbbox: dict,
    no_slip_xmin: float | None,
) -> dict:
    """
    static floor の xmin/xmax/ymin/ymax を body 寸法から計算する。

    setup_script_ext_aero_2026_v1.99.py の body-based ロジックに従う:
      xmax = body xMax + body_length × 0.75
      ymin = body yMin - body_width × 0.25
      ymax = body yMax + body_width × 0.25
    """
    body_length = vbbox["x_max"] - vbbox["x_min"]
    body_width  = vbbox["y_max"] - vbbox["y_min"]
    xmin = no_slip_xmin if no_slip_xmin is not None else vbbox["x_min"]
    return {
        "x_min": xmin,
        "x_max": vbbox["x_max"] + body_length * 0.75,
        "y_min": vbbox["y_min"] - body_width  * 0.25,
        "y_max": vbbox["y_max"] + body_width  * 0.25,
    }


def _compute_belt5_center_xmin(
    vbbox: dict,
    wheel_kin_map: dict,
    belt5_cfg: "Belt5Config",
) -> float:
    """
    5ベルトシステムのセンターベルト x_min を計算する。

    center_belt_position == "at_wheelbase_center" の場合:
      center_x = (FR wheel x + RR wheel x) / 2
      center_xmin = center_x - belt_size_center.x / 2
    """
    if belt5_cfg.center_belt_position == "user_specified" and belt5_cfg.center_belt_x_pos is not None:
        return belt5_cfg.center_belt_x_pos - belt5_cfg.belt_size_center.x / 2

    # ホイール運動学から center x を計算
    fr = wheel_kin_map.get("fr_lh") or wheel_kin_map.get("fr_rh")
    rr = wheel_kin_map.get("rr_lh") or wheel_kin_map.get("rr_rh")
    if fr and rr:
        center_x = (fr["center"]["x_pos"] + rr["center"]["x_pos"]) / 2.0
    elif vbbox:
        center_x = (vbbox["x_min"] + vbbox["x_max"]) / 2.0
    else:
        center_x = 0.0

    return center_x - belt5_cfg.belt_size_center.x / 2


def _build_belt5_wall_instances(
    wheel_kin_map: dict,
    belt5_cfg: "Belt5Config",
    vbbox: dict,
    velocity_dir: dict,
    FluidBCMoving: type,
    XYZDir: type,
    WallInstance: type,
) -> tuple[list, float]:
    """
    5ベルト wall BC インスタンスを生成する。

    Returns: (wall_instances, center_belt_xmin)
    """
    bsw = belt5_cfg.belt_size_wheel
    bsc = belt5_cfg.belt_size_center
    vx, vy = velocity_dir["x_dir"], velocity_dir["y_dir"]

    # センターベルト xmin
    center_xmin = _compute_belt5_center_xmin(vbbox, wheel_kin_map, belt5_cfg)

    # ホイールベルトの y 中心位置を tire centroid から決定
    belt_y_positions: dict[str, float] = {}
    for key in ("fr_lh", "fr_rh", "rr_lh", "rr_rh"):
        kin = wheel_kin_map.get(key)
        if kin:
            belt_y_positions[key] = kin["center"]["y_pos"]
        else:
            # フォールバック: 全幅の ±1/4
            width = vbbox["y_max"] - vbbox["y_min"]
            y_mid = (vbbox["y_min"] + vbbox["y_max"]) / 2
            belt_y_positions["fr_lh"] = y_mid - width / 4
            belt_y_positions["fr_rh"] = y_mid + width / 4
            belt_y_positions["rr_lh"] = y_mid - width / 4
            belt_y_positions["rr_rh"] = y_mid + width / 4
            break

    # narrow car fallback: LH-RH 間距離の最小制約
    if belt5_cfg.narrow_car_fallback.enabled:
        min_gap = belt5_cfg.narrow_car_fallback.min_belt_gap
        for axle in (("fr_lh", "fr_rh"), ("rr_lh", "rr_rh")):
            lh_key, rh_key = axle
            gap = belt_y_positions.get(rh_key, 0) - belt_y_positions.get(lh_key, 0)
            if gap < min_gap:
                mid = (belt_y_positions.get(lh_key, 0) + belt_y_positions.get(rh_key, 0)) / 2
                belt_y_positions[lh_key] = mid - min_gap / 2
                belt_y_positions[rh_key] = mid + min_gap / 2

    instances = []

    # ホイールベルト x 位置: ホイール centroid を基準に bsw.x の幅で設置
    for key, belt_label in (
        ("fr_lh", "Belt_Wheel_FR_LH"),
        ("fr_rh", "Belt_Wheel_FR_RH"),
        ("rr_lh", "Belt_Wheel_RR_LH"),
        ("rr_rh", "Belt_Wheel_RR_RH"),
    ):
        kin = wheel_kin_map.get(key)
        center_x = kin["center"]["x_pos"] if kin else (vbbox["x_min"] + vbbox["x_max"]) / 2
        instances.append(WallInstance(
            name=belt_label,
            parts=[belt_label],
            fluid_bc_settings=FluidBCMoving(
                type="moving",
                velocity=XYZDir(x_dir=vx, y_dir=vy, z_dir=0.0),
            ),
        ))

    # センターベルト
    instances.append(WallInstance(
        name="Belt_Center",
        parts=["Belt_Center"],
        fluid_bc_settings=FluidBCMoving(
            type="moving",
            velocity=XYZDir(x_dir=vx, y_dir=vy, z_dir=0.0),
        ),
    ))

    return instances, center_xmin


def _build_ground_box_refinements(
    no_slip_xmin: float,
    coarsest: float,
    ground_height: float,
    floor_dims: dict,
    ground_mode: str,
    belt_active: bool,
    BoundingBox: type,
    BoxInstance: type,
) -> list:
    """
    地面境界層用 box refinement を生成する。

    setup_script_ext_aero_2026_v1.99.py のロジックに従う:
      - box_ground_RL5: 24 layers × coarsest × 0.5^5 の高さ
      - box_ground_RL6:  8 layers × coarsest × 0.5^6 の高さ
      - static ground かつ belt なし: RL1~RL4 の追加 box も生成

    Returns: list[BoxInstance]
    """
    OFFSET_X = -0.01   # no_slip_xmin からのオフセット
    OFFSET_Z = -0.01   # ground_height からのオフセット
    NUM_LAYERS_RL5 = 24
    NUM_LAYERS_RL6 = 8
    INFLATION_FACTORS = [1.4, 1.2, 1.1, 1.05]  # RL1-4 のインフレ係数

    h_rl5 = coarsest * (0.5 ** 5) * NUM_LAYERS_RL5
    h_rl6 = coarsest * (0.5 ** 6) * NUM_LAYERS_RL6

    x_min_box = no_slip_xmin + OFFSET_X
    x_max_box = floor_dims["x_max"]
    y_min_box  = floor_dims["y_min"]
    y_max_box  = floor_dims["y_max"]
    z_min_box  = ground_height + OFFSET_Z

    instances = []

    for rl, thickness in ((5, h_rl5), (6, h_rl6)):
        instances.append(BoxInstance(
            name=f"box_ground_RL{rl}",
            refinement_level=rl,
            bounding_box=BoundingBox(
                x_min=x_min_box,
                x_max=x_max_box,
                y_min=y_min_box,
                y_max=y_max_box,
                z_min=z_min_box,
                z_max=ground_height + thickness,
            ),
        ))

    # static ground かつ belt なし: RL1~RL4 も追加
    if ground_mode == "static" and not belt_active:
        rl5_len = x_max_box - x_min_box
        rl5_wid = y_max_box - y_min_box
        for i, factor in enumerate(INFLATION_FACTORS, 1):
            inflate = (factor - 1) * 0.5
            instances.append(BoxInstance(
                name=f"box_ground_add_RL{i}",
                refinement_level=i,
                bounding_box=BoundingBox(
                    x_min=x_min_box - rl5_len * inflate,
                    x_max=x_max_box + rl5_len * inflate,
                    y_min=y_min_box - rl5_wid * inflate,
                    y_max=y_max_box + rl5_wid * inflate,
                    z_min=z_min_box,
                    z_max=ground_height + h_rl5,
                ),
            ))

    return instances


def _build_tg_instances(
    sim_type: str,
    tg_cfg: "TurbulenceGeneratorOption",
    vbbox: dict,
    coarsest: float,
    no_slip_xmin: float | None,
    floor_dims: dict,
    BoundingBox: type,
    BoxInstance: type,
    TurbulenceInstance: type,
    TurbulencePoint: type,
    TurbulenceBoundingBox: type,
    ground_height: float | None = None,
) -> tuple[list, list]:
    """
    Turbulence generator インスタンスと、body TG 用 box refinement を生成する。

    sim_type == "aero" のときのみ有効。
    setup_script_ext_aero_2026_v1.99.py のロジックに従う。
    ground_height: 解決済み ground 高度 (m)。None の場合は vbbox["z_min"] を使用。

    Returns: (tg_instances, extra_box_instances)
    """
    if sim_type != "aero":
        return [], []

    ground_height = ground_height if ground_height is not None else vbbox["z_min"]
    car_length_x = vbbox["x_max"] - vbbox["x_min"]
    car_length_y = vbbox["y_max"] - vbbox["y_min"]
    car_length_z = vbbox["z_max"] - vbbox["z_min"]
    car_y_center = (vbbox["y_min"] + vbbox["y_max"]) / 2

    h_rl6 = coarsest * (0.5 ** 6) * 8

    tg_instances = []
    box_instances = []
    OFFSET = 0.02  # box refinement パディング

    if tg_cfg.enable_ground_tg and no_slip_xmin is not None:
        tg_instances.append(TurbulenceInstance(
            name="tg_ground",
            num_eddies=tg_cfg.ground_tg_num_eddies,
            length_scale=coarsest * (0.5 ** 6),
            turbulence_intensity=tg_cfg.ground_tg_intensity,
            point=TurbulencePoint(x_pos=no_slip_xmin - 0.01),
            bounding_box=TurbulenceBoundingBox(
                y_min=floor_dims["y_min"],
                y_max=floor_dims["y_max"],
                z_min=ground_height,
                z_max=ground_height + h_rl6,
            ),
        ))

    if tg_cfg.enable_body_tg:
        tg_x = vbbox["x_min"] - car_length_x * 0.05
        tg_y_min = car_y_center - car_length_y * 0.45
        tg_y_max = car_y_center + car_length_y * 0.45
        tg_z_min = vbbox["z_min"] + car_length_z * 0.10
        tg_z_max = vbbox["z_min"] + car_length_z * 0.65

        tg_instances.append(TurbulenceInstance(
            name="tg_body",
            num_eddies=tg_cfg.body_tg_num_eddies,
            length_scale=coarsest * (0.5 ** 6),
            turbulence_intensity=tg_cfg.body_tg_intensity,
            point=TurbulencePoint(x_pos=tg_x),
            bounding_box=TurbulenceBoundingBox(
                y_min=tg_y_min,
                y_max=tg_y_max,
                z_min=tg_z_min,
                z_max=tg_z_max,
            ),
        ))

        # body TG 専用 box refinement RL6
        box_instances.append(BoxInstance(
            name="boxRL_tg_body",
            refinement_level=6,
            bounding_box=BoundingBox(
                x_min=tg_x - OFFSET * 0.5,
                x_max=vbbox["x_min"] + car_length_x * 0.08 + OFFSET,
                y_min=tg_y_min - OFFSET * 0.5,
                y_max=tg_y_max + OFFSET * 0.5,
                z_min=tg_z_min - OFFSET * 0.5,
                z_max=tg_z_max + OFFSET * 0.5,
            ),
        ))

    return tg_instances, box_instances


# ---------------------------------------------------------------------------
# Main assembler
# ---------------------------------------------------------------------------

def assemble_ufx_solver_deck(
    template_settings: "TemplateSettings",
    analysis_result: dict,
    sim_type: str,
    inflow_velocity: float,
    yaw_angle: float = 0.0,
    source_files: list[str] | None = None,
    source_file: str | None = None,
) -> "UfxSolverDeck":
    """
    Template (Fixed) + Geometry analysis_result (Computed) + Config (UserInput)
    から UfxSolverDeck を組み立てる。

    sim_type: "aero" | "ghn" | "fan_noise"
    source_files: Assembly に複数 Geometry がある場合
    source_file:  単一 Geometry の場合
    """
    from app.ultrafluid.schema import (
        AeroCoefficients, BoundaryConditions, BoundingBox,
        CoefficientsAlongAxis, DomainPart, ExportBounds,
        FileFormat, FluidBCMoving, FluidBCNonReflectivePressure,
        FluidBCRotating, FluidBCSlip, FluidBCStatic, FluidBCVelocity,
        Geometry, InletInstance, Material, Meshing, MeshingGeneral,
        MomentReferenceSystem, Overset, Output, OutputCoarsening,
        OutputGeneral, OutputVariablesFull, OutputVariablesSurface,
        BoxInstance, BoundingRange, CustomInstance,
        DomainPartInstance, OffsetInstance, OutletInstance, PorousAxis,
        PartialSurfaceInstance, PartialVolumeInstance,
        PorousInstance, ProbeFileInstance, ProbeOutputVariables, Refinement, RotatingInstance, SectionCutInstance, Simulation,
        SimulationGeneral, Sources, SurfaceMeshOptimization,
        TriangleSplitting, TriangleSplittingInstance, TurbulenceBoundingBox, TurbulenceInstance,
        TurbulencePoint, UfxSolverDeck, Version, WallInstance, WallModeling,
        XYZDir, XYZPos,
    )

    sp   = template_settings.simulation_parameter
    so   = template_settings.setup_option
    setup = template_settings.setup
    tn   = template_settings.target_names
    out_cfg = template_settings.output
    gc   = so.boundary_condition.ground
    tg_cfg = so.boundary_condition.turbulence_generator

    vbbox: dict    = analysis_result.get("vehicle_bbox", {})
    part_info: dict = analysis_result.get("part_info", {})

    # ── 有効パラメータ ────────────────────────────────────────────────────
    temperature_k = (sp.temperature + 273.15) if so.simulation.temperature_degree else sp.temperature
    coarsest      = sp.coarsest_voxel_size                 # ユーザー入力のコースメッシュサイズ
    dt            = compute_dt(coarsest, inflow_velocity, sp.mach_factor)

    # parameter_preset: fan_noise のときのみ "fan_noise"、それ以外 "default"
    parameter_preset = "fan_noise" if sim_type == "fan_noise" else "default"

    # ── Ground height — domain bbox の Z アンカーとして先に解決 ───────────
    # absolute: ユーザー指定の絶対 z 値
    # from_geometry: STL の z_min + オフセット (デフォルト 0.0)
    if gc.ground_height_mode == "absolute":
        ground_height = gc.ground_height_absolute
    else:
        ground_height = vbbox.get("z_min", 0.0) + gc.ground_height_offset_from_geom_zMin

    # ── Domain bounding box ───────────────────────────────────────────────
    if vbbox:
        abs_bbox = compute_domain_bbox(vbbox, setup.domain_bounding_box, ground_z=ground_height)
    else:
        abs_bbox = {"x_min": -10.0, "x_max": 30.0, "y_min": -15.0, "y_max": 15.0, "z_min": 0.0, "z_max": 8.0}
    domain_bb = BoundingBox(**abs_bbox)

    # ── Yaw 방향 ──────────────────────────────────────────────────────────
    yaw_rad = math.radians(yaw_angle)
    vx = inflow_velocity * math.cos(yaw_rad)
    vy = inflow_velocity * math.sin(yaw_rad)
    velocity_dir = {"x_dir": vx, "y_dir": vy}

    # ── Derived flags from ground_mode ─────────────────────────────────────
    # rotate_wheels and moving_ground are fully determined by ground_mode:
    #   static → False / False
    #   full_moving / rotating_belt_* → True / True
    rotate_wheels = gc.ground_mode != "static"
    moving_ground = gc.ground_mode != "static"

    # ── Wheel kinematics ──────────────────────────────────────────────────
    is_aero = sim_type == "aero"
    wheel_kin_map: dict[str, dict] = {}
    rotating_instances: list = []

    if is_aero and rotate_wheels:
        wheel_map = classify_wheels(analysis_result, tn)
        osm_map   = {
            "fr_lh": tn.overset_fr_lh, "fr_rh": tn.overset_fr_rh,
            "rr_lh": tn.overset_rr_lh, "rr_rh": tn.overset_rr_rh,
        }
        label_map = {
            "fr_lh": "VREV_Front_Left", "fr_rh": "VREV_Front_Right",
            "rr_lh": "VREV_Rear_Left",  "rr_rh": "VREV_Rear_Right",
        }
        for key, winfo in wheel_map.items():
            kin = compute_wheel_kinematics(winfo, inflow_velocity)
            wheel_kin_map[key] = kin
            if gc.overset_wheels:
                rotating_instances.append(RotatingInstance(
                    name=label_map[key],
                    rpm=kin["rpm"],
                    center=XYZPos(**kin["center"]),
                    axis=XYZDir(**kin["axis"]),
                    parts=[osm_map[key]] if osm_map.get(key) else [],
                ))

    # ── Belt positioning (5-belt) ─────────────────────────────────────────
    center_belt_xmin: float | None = None
    if is_aero and gc.ground_mode == "rotating_belt_5" and vbbox:
        center_belt_xmin = _compute_belt5_center_xmin(vbbox, wheel_kin_map, gc.belt5)

    # ── BL suction xmin ───────────────────────────────────────────────────
    no_slip_xmin: float | None = None
    if gc.ground_mode != "full_moving":
        no_slip_xmin = _resolve_no_slip_xmin(gc, center_belt_xmin)

    # ── Static floor dimensions (for TG + ground refinement boxes) ───────
    floor_dims: dict = {}
    if vbbox:
        floor_dims = _static_floor_dims(vbbox, no_slip_xmin)

    # ── Ground box refinements ────────────────────────────────────────────
    ground_box_instances: list = []
    need_ground_refinement = (
        is_aero and (
            gc.apply_static_ground_refinement
            or (tg_cfg.enable_ground_tg and no_slip_xmin is not None)
        )
        and vbbox and no_slip_xmin is not None
    )
    if need_ground_refinement:
        belt_active = gc.ground_mode in ("rotating_belt_1", "rotating_belt_5")
        ground_box_instances = _build_ground_box_refinements(
            no_slip_xmin, coarsest, ground_height, floor_dims,
            gc.ground_mode, belt_active,
            BoundingBox, BoxInstance,
        )

    # ── Turbulence generators ─────────────────────────────────────────────
    turbulence_instances: list = []
    tg_extra_boxes: list = []
    if is_aero and vbbox and (tg_cfg.enable_ground_tg or tg_cfg.enable_body_tg):
        turbulence_instances, tg_extra_boxes = _build_tg_instances(
            sim_type, tg_cfg, vbbox, coarsest,
            no_slip_xmin, floor_dims,
            BoundingBox, BoxInstance,
            TurbulenceInstance, TurbulencePoint, TurbulenceBoundingBox,
            ground_height=ground_height,
        )

    # ── Wall BCs ──────────────────────────────────────────────────────────
    wall_instances: list = []

    # ホイール wall BC
    tire_pid_map = {
        "fr_lh": tn.wheel_tire_fr_lh, "fr_rh": tn.wheel_tire_fr_rh,
        "rr_lh": tn.wheel_tire_rr_lh, "rr_rh": tn.wheel_tire_rr_rh,
    }
    if is_aero and rotate_wheels:
        for key, kin in wheel_kin_map.items():
            tire_pid = tire_pid_map.get(key, "")
            if tire_pid:
                roughness = tn.tire_roughness if tn.tire_roughness > 0 else None
                wall_instances.append(WallInstance(
                    name=f"Wheel_{key.upper()}",
                    parts=[tire_pid],
                    roughness=roughness,
                    fluid_bc_settings=FluidBCRotating(
                        type="rotating",
                        rpm=kin["rpm"],
                        center=XYZPos(**kin["center"]),
                        axis=XYZDir(**kin["axis"]),
                    ),
                ))
    else:
        # ghn / fan_noise / aero static: wheel = static BC
        wheel_parts_all = [
            name for name in part_info
            if _matches_any(name, tn.wheel)
        ]
        if wheel_parts_all:
            wall_instances.append(WallInstance(
                name="Wheels",
                parts=wheel_parts_all,
                fluid_bc_settings=FluidBCStatic(type="static"),
            ))

    # ベルト wall BC
    if is_aero and gc.ground_mode == "rotating_belt_5" and moving_ground and vbbox:
        belt_wis, _ = _build_belt5_wall_instances(
            wheel_kin_map, gc.belt5, vbbox, velocity_dir,
            FluidBCMoving, XYZDir, WallInstance,
        )
        wall_instances.extend(belt_wis)

    elif is_aero and gc.ground_mode == "rotating_belt_1" and moving_ground:
        wall_instances.append(WallInstance(
            name="Belt",
            parts=["Belt"],
            fluid_bc_settings=FluidBCMoving(
                type="moving",
                velocity=XYZDir(x_dir=vx, y_dir=vy, z_dir=0.0),
            ),
        ))

    # 地面 wall BC
    if is_aero and gc.ground_mode == "full_moving":
        wall_instances.append(WallInstance(
            name="Ground",
            parts=["Ground"],
            fluid_bc_settings=FluidBCMoving(
                type="moving",
                velocity=XYZDir(x_dir=vx, y_dir=vy, z_dir=0.0),
            ),
        ))
    else:
        # static ground BC ("uFX_ground")
        ground_parts = ["uFX_ground"]
        if gc.ground_patch_active and floor_dims:
            pass  # 実際のパーツ名は STL 由来のため、ここでは標準名を使用
        wall_instances.append(WallInstance(
            name="uFX_ground",
            parts=ground_parts,
            fluid_bc_settings=FluidBCStatic(type="static"),
        ))

    # ── Porous sources ────────────────────────────────────────────────────
    porous_instances: list = []
    if template_settings.porous_coefficients:
        porous_coeff_map = {p.part_name: p for p in template_settings.porous_coefficients}
        for pname, pinfo in part_info.items():
            if not _matches_any(pname, tn.porous):
                continue
            coeff = porous_coeff_map.get(pname)
            if coeff is None:
                continue
            p_axis = compute_porous_axis(pinfo)
            porous_instances.append(PorousInstance(
                name=pname,
                inertial_resistance=coeff.inertial_resistance,
                viscous_resistance=coeff.viscous_resistance,
                porous_axis=PorousAxis(**p_axis),
                parts=[pname],
            ))

    # ── Iteration counts ──────────────────────────────────────────────────
    num_iter   = time_to_iterations(sp.simulation_time, dt)
    avg_start  = time_to_iterations(sp.start_averaging_time, dt)
    avg_window = time_to_iterations(sp.avg_window_size, dt)

    fd = out_cfg.full_data
    out_start = time_to_iterations(
        fd.output_start_time if fd.output_start_time is not None else sp.simulation_time, dt
    )
    out_freq = time_to_iterations(
        fd.output_interval if fd.output_interval is not None else sp.simulation_time, dt
    )

    # ── Section cut instances ─────────────────────────────────────────────
    sc_instances: list = []
    for sc in out_cfg.section_cuts:
        sc_start = time_to_iterations(
            sc.output_start_time if sc.output_start_time is not None
            else (fd.output_start_time if fd.output_start_time is not None else sp.simulation_time),
            dt,
        )
        sc_freq = time_to_iterations(
            sc.output_interval if sc.output_interval is not None
            else (fd.output_interval if fd.output_interval is not None else sp.simulation_time),
            dt,
        )
        if len(sc.bbox) == 6:
            sc_bbox = BoundingBox(
                x_min=sc.bbox[0], x_max=sc.bbox[1],
                y_min=sc.bbox[2], y_max=sc.bbox[3],
                z_min=sc.bbox[4], z_max=sc.bbox[5],
            )
        else:
            sc_bbox = BoundingBox(**abs_bbox)
        sc_instances.append(SectionCutInstance(
            name=sc.name,
            merge_output_files=sc.merge_output,
            delete_unmerged_output_files=sc.delete_unmerged,
            triangulation=sc.triangulation,
            file_format=FileFormat(ensight=sc.file_format_ensight, h3d=sc.file_format_h3d),
            axis=XYZDir(x_dir=sc.axis_x, y_dir=sc.axis_y, z_dir=sc.axis_z),
            point=XYZPos(x_pos=sc.point_x, y_pos=sc.point_y, z_pos=sc.point_z),
            bounding_box=sc_bbox,
            output_frequency=sc_freq,
            output_start_iteration=sc_start,
            output_variables=sc.output_variables,
        ))

    # ── Probe file instances ──────────────────────────────────────────────
    probe_instances: list = []
    for pf_cfg in out_cfg.probe_files:
        pf_freq = time_to_iterations(
            pf_cfg.output_frequency if pf_cfg.output_frequency > 0 else sp.simulation_time,
            dt,
        )
        ov = pf_cfg.output_variables
        probe_ov = ProbeOutputVariables(
            pressure=ov.pressure,
            time_avg_pressure=ov.time_avg_pressure,
            window_avg_pressure=ov.window_avg_pressure,
            cp=ov.cp,
            velocity=ov.velocity,
            time_avg_velocity=ov.time_avg_velocity,
            window_avg_velocity=ov.window_avg_velocity,
            velocity_magnitude=ov.velocity_magnitude,
            time_avg_velocity_magnitude=ov.time_avg_velocity_magnitude,
            window_avg_velocity_magnitude=ov.window_avg_velocity_magnitude,
            wall_shear_stress=ov.wall_shear_stress,
            time_avg_wall_shear_stress=ov.time_avg_wall_shear_stress,
            window_avg_wall_shear_stress=ov.window_avg_wall_shear_stress,
            density=ov.density,
            time_avg_density=ov.time_avg_density,
            window_avg_density=ov.window_avg_density,
            pressure_std=ov.pressure_std,
            pressure_var=ov.pressure_var,
        )
        probe_instances.append(ProbeFileInstance(
            name=pf_cfg.name,
            source_file=f"{pf_cfg.name}.csv",  # relative path beside output.xml
            probe_type=pf_cfg.probe_type,
            radius=pf_cfg.radius,
            output_frequency=pf_freq,
            scientific_notation=pf_cfg.scientific_notation,
            output_precision=pf_cfg.output_precision,
            output_start_iteration=pf_cfg.output_start_iteration,
            output_variables=probe_ov,
        ))

    # ── Partial surface instances ─────────────────────────────────────────
    all_part_names = list(part_info.keys())
    baffle_patterns = tn.baffle
    ps_instances: list = []
    for ps_cfg in out_cfg.partial_surfaces:
        ps_start = time_to_iterations(
            ps_cfg.output_start_time if ps_cfg.output_start_time is not None
            else (fd.output_start_time if fd.output_start_time is not None else sp.simulation_time),
            dt,
        )
        ps_freq = time_to_iterations(
            ps_cfg.output_interval if ps_cfg.output_interval is not None
            else (fd.output_interval if fd.output_interval is not None else sp.simulation_time),
            dt,
        )
        # include_parts: empty = all parts; non-empty = filter by substring match
        if ps_cfg.include_parts:
            parts_list = [p for p in all_part_names if any(pat in p for pat in ps_cfg.include_parts)]
        else:
            parts_list = list(all_part_names)
        # exclude_parts: remove matching
        if ps_cfg.exclude_parts:
            parts_list = [p for p in parts_list if not any(pat in p for pat in ps_cfg.exclude_parts)]
        # baffle_export_option: auto-exclude baffle parts when set
        if ps_cfg.baffle_export_option is not None and baffle_patterns:
            parts_list = [p for p in parts_list if not _matches_any(p, baffle_patterns)]
        ps_instances.append(PartialSurfaceInstance(
            name=ps_cfg.name,
            parts=parts_list,
            merge_output_files=ps_cfg.merge_output,
            delete_unmerged_output_files=ps_cfg.delete_unmerged,
            file_format=FileFormat(ensight=ps_cfg.file_format_ensight, h3d=ps_cfg.file_format_h3d),
            output_frequency=ps_freq,
            output_start_iteration=ps_start,
            output_variables=ps_cfg.output_variables,
        ))

    # ── Partial volume instances ──────────────────────────────────────────
    pv_instances: list = []
    for pv_cfg in out_cfg.partial_volumes:
        pv_start = time_to_iterations(
            pv_cfg.output_start_time if pv_cfg.output_start_time is not None
            else (fd.output_start_time if fd.output_start_time is not None else sp.simulation_time),
            dt,
        )
        pv_freq = time_to_iterations(
            pv_cfg.output_interval if pv_cfg.output_interval is not None
            else (fd.output_interval if fd.output_interval is not None else sp.simulation_time),
            dt,
        )
        # Resolve bounding box based on bbox_mode
        if pv_cfg.bbox_mode == "from_meshing_box" and pv_cfg.bbox_source_box_name:
            _box = (
                setup.meshing.box_refinement.get(pv_cfg.bbox_source_box_name)
                or setup.meshing.part_box_refinement.get(pv_cfg.bbox_source_box_name)
            )
            if _box:
                pv_bb = BoundingBox(
                    x_min=_box.box[0], x_max=_box.box[1],
                    y_min=_box.box[2], y_max=_box.box[3],
                    z_min=_box.box[4], z_max=_box.box[5],
                )
            else:
                pv_bb = BoundingBox(**abs_bbox)
        elif pv_cfg.bbox_mode == "around_parts" and pv_cfg.bbox_source_parts and part_info:
            matched = [
                p for n, p in part_info.items()
                if any(pat in n for pat in pv_cfg.bbox_source_parts)
            ]
            if matched:
                pv_bb = BoundingBox(
                    x_min=min(p["bbox"]["x_min"] for p in matched),
                    x_max=max(p["bbox"]["x_max"] for p in matched),
                    y_min=min(p["bbox"]["y_min"] for p in matched),
                    y_max=max(p["bbox"]["y_max"] for p in matched),
                    z_min=min(p["bbox"]["z_min"] for p in matched),
                    z_max=max(p["bbox"]["z_max"] for p in matched),
                )
            else:
                pv_bb = BoundingBox(**abs_bbox)
        elif pv_cfg.bbox_mode == "user_defined" and pv_cfg.bbox and len(pv_cfg.bbox) == 6:
            b = pv_cfg.bbox
            pv_bb = BoundingBox(
                x_min=b[0], x_max=b[1], y_min=b[2], y_max=b[3], z_min=b[4], z_max=b[5]
            )
        else:
            pv_bb = BoundingBox(**abs_bbox)
        pv_coarsening = (
            OutputCoarsening(
                active=True,
                coarsest_target_refinement_level=pv_cfg.coarsest_target_refinement_level,
                coarsen_by_num_refinement_levels=pv_cfg.coarsen_by_num_refinement_levels,
                export_uncoarsened_voxels=False,
            )
            if pv_cfg.output_coarsening_active else None
        )
        pv_instances.append(PartialVolumeInstance(
            name=pv_cfg.name,
            merge_output_files=pv_cfg.merge_output,
            delete_unmerged_output_files=pv_cfg.delete_unmerged,
            file_format=FileFormat(ensight=pv_cfg.file_format_ensight, h3d=pv_cfg.file_format_h3d),
            output_frequency=pv_freq,
            output_start_iteration=pv_start,
            bounding_box=pv_bb,
            output_variables=pv_cfg.output_variables,
            output_coarsening=pv_coarsening,
        ))

    # ── Mesh refinement ───────────────────────────────────────────────────
    # box_refinement: 相対乗数 → 車両 bbox を基準に絶対座標に変換
    box_instances = []
    for name, br in {**setup.meshing.box_refinement, **setup.meshing.part_box_refinement}.items():
        if vbbox:
            abs_box = compute_domain_bbox(vbbox, br.box, ground_z=ground_height)
        else:
            abs_box = {
                "x_min": br.box[0], "x_max": br.box[1],
                "y_min": br.box[2], "y_max": br.box[3],
                "z_min": br.box[4], "z_max": br.box[5],
            }
        box_instances.append(BoxInstance(
            name=name,
            refinement_level=br.level,
            bounding_box=BoundingBox(**abs_box),
        ))

    # part_based_box_refinement: パーツ bbox の union + オフセット → 絶対座標
    for name, pbr in setup.meshing.part_based_box_refinement.items():
        matched = [pname for pname in part_info if _matches_any(pname, pbr.parts)]
        if not matched:
            continue  # パターンにマッチするパーツがない場合はスキップ
        px_min = min(part_info[p]["bbox"]["x_min"] for p in matched) - pbr.offset_xmin
        px_max = max(part_info[p]["bbox"]["x_max"] for p in matched) + pbr.offset_xmax
        py_min = min(part_info[p]["bbox"]["y_min"] for p in matched) - pbr.offset_ymin
        py_max = max(part_info[p]["bbox"]["y_max"] for p in matched) + pbr.offset_ymax
        pz_min = min(part_info[p]["bbox"]["z_min"] for p in matched) - pbr.offset_zmin
        pz_max = max(part_info[p]["bbox"]["z_max"] for p in matched) + pbr.offset_zmax
        box_instances.append(BoxInstance(
            name=name,
            refinement_level=pbr.level,
            bounding_box=BoundingBox(
                x_min=px_min, x_max=px_max,
                y_min=py_min, y_max=py_max,
                z_min=pz_min, z_max=pz_max,
            ),
        ))

    box_instances += ground_box_instances + tg_extra_boxes

    offset_instances = [
        OffsetInstance(
            name=name,
            normal_distance=orf.normal_distance,
            refinement_level=orf.level,
            parts=[
                p for p in orf.parts
                if not _matches_any(p, tn.windtunnel)
            ] if orf.parts else [],
        )
        for name, orf in setup.meshing.offset_refinement.items()
    ]
    custom_instances = [
        CustomInstance(name=name, refinement_level=cr.level, parts=cr.parts)
        for name, cr in setup.meshing.custom_refinement.items()
    ]

    # ── Baffle parts ──────────────────────────────────────────────────────
    baffle_parts = [name for name in part_info if _matches_any(name, tn.baffle)]

    # ── triangle splitting ────────────────────────────────────────────────
    ts_active = so.meshing.triangle_splitting
    ts_instances = [
        TriangleSplittingInstance(
            name=inst.name,
            active=inst.active,
            max_absolute_edge_length=inst.max_absolute_edge_length,
            max_relative_edge_length=inst.max_relative_edge_length,
            parts=inst.parts,
        )
        for inst in so.meshing.triangle_splitting_instances
    ]

    # ── Moment reference system ───────────────────────────────────────────
    if wheel_kin_map:
        moment_origin = compute_moment_reference_origin(wheel_kin_map)
    else:
        # フォールバック: vehicle bbox の中心
        if vbbox:
            cx = (vbbox["x_min"] + vbbox["x_max"]) / 2
            moment_origin = {"x_pos": cx, "y_pos": 0.0, "z_pos": ground_height}
        else:
            moment_origin = {"x_pos": 0.0, "y_pos": 0.0, "z_pos": 0.0}

    # ── Reference length / area for aero coefficients ─────────────────────
    aero_cfg = out_cfg.aero_coefficients
    ref_length = 1.0
    if not aero_cfg.reference_length_auto:
        ref_length = aero_cfg.reference_length or 1.0
    elif wheel_kin_map:
        ref_length = compute_reference_length(wheel_kin_map)

    ref_area = aero_cfg.reference_area or 1.0

    # ── Output bounding box ───────────────────────────────────────────────
    if fd.bbox is not None and len(fd.bbox) == 6:
        out_bb = BoundingBox(
            x_min=fd.bbox[0], x_max=fd.bbox[1],
            y_min=fd.bbox[2], y_max=fd.bbox[3],
            z_min=fd.bbox[4], z_max=fd.bbox[5],
        )
    elif fd.bbox_mode == "from_meshing_box" and fd.bbox_source_box_name and fd.bbox_source_box_name in setup.meshing.box_refinement:
        br = setup.meshing.box_refinement[fd.bbox_source_box_name]
        out_bb = BoundingBox(
            x_min=br.box[0], x_max=br.box[1],
            y_min=br.box[2], y_max=br.box[3],
            z_min=br.box[4], z_max=br.box[5],
        )
    else:
        out_bb = domain_bb

    # ── passive parts (windtunnel → passive) ──────────────────────────────
    passive_parts = [
        p for p in part_info
        if _matches_any(p, tn.windtunnel)
    ]
    # include_wheel_belt_forces=False → wheel belt parts も passive に追加
    if is_aero and gc.ground_mode == "rotating_belt_5" and not gc.belt5.include_wheel_belt_forces:
        passive_parts += [
            f"Belt_Wheel_{k.upper()}"
            for k in ("fr_lh", "fr_rh", "rr_lh", "rr_rh")
        ]

    # ── Assemble UfxSolverDeck ────────────────────────────────────────────
    deck = UfxSolverDeck(
        version=Version(gui_version="2024", solver_version="2024"),
        simulation=Simulation(
            general=SimulationGeneral(
                num_coarsest_iterations=num_iter,
                mach_factor=sp.mach_factor,
                num_ramp_up_iterations=sp.num_ramp_up_iter,
                parameter_preset=parameter_preset,
            ),
            material=Material(
                name="Air",
                density=sp.density,
                dynamic_viscosity=sp.dynamic_viscosity,
                temperature=temperature_k,
                specific_gas_constant=sp.specific_gas_constant,
            ),
            wall_modeling=WallModeling(
                wall_model="GLW",
                coupling="adaptive_two-way",
                transitional_bl_detection=(True if sim_type == "ghn" else None),
            ),
        ),
        geometry=Geometry(
            source_file=source_file,
            source_files=source_files or [],
            baffle_parts=baffle_parts,
            domain_bounding_box=domain_bb,
            triangle_plinth=False,
            surface_mesh_optimization=SurfaceMeshOptimization(
                triangle_splitting=TriangleSplitting(
                    active=ts_active,
                    max_absolute_edge_length=so.meshing.max_absolute_edge_length,
                    max_relative_edge_length=so.meshing.max_relative_edge_length,
                    triangle_splitting_instances=ts_instances,
                )
            ),
            domain_part=DomainPart(export_mesh=False, domain_part_instances=[]),
        ),
        meshing=Meshing(
            general=MeshingGeneral(
                coarsest_mesh_size=coarsest,
                mesh_preview=False,
                mesh_export=False,
                refinement_level_transition_layers=so.meshing.refinement_level_transition_layers,
            ),
            refinement=Refinement(
                box=box_instances,
                offset=offset_instances,
                custom=custom_instances,
            ),
            overset=Overset(rotating=rotating_instances),
        ),
        boundary_conditions=BoundaryConditions(
            inlet=[InletInstance(
                name="Inlet",
                parts=["Inlet"],
                fluid_bc_settings=FluidBCVelocity(
                    type="velocity",
                    velocity=XYZDir(x_dir=vx, y_dir=vy, z_dir=0.0),
                ),
            )],
            outlet=[OutletInstance(
                name="Outlet",
                parts=["Outlet"],
                fluid_bc_settings=FluidBCNonReflectivePressure(type="non_reflective_pressure"),
            )],
            wall=wall_instances,
        ),
        sources=Sources(
            porous=porous_instances,
            turbulence=turbulence_instances,
        ),
        output=Output(
            general=OutputGeneral(
                file_format=FileFormat(
                    ensight=fd.file_format_ensight,
                    h3d=fd.file_format_h3d,
                ),
                output_coarsening=OutputCoarsening(
                    active=fd.output_coarsening_active,
                    coarsen_by_num_refinement_levels=fd.coarsen_by_num_refinement_levels,
                    coarsest_target_refinement_level=fd.coarsest_target_refinement_level,
                    export_uncoarsened_voxels=False,
                ),
                time_varying_geometry_output=False,
                merge_output_files=fd.merge_output,
                delete_unmerged_output_files=fd.delete_unmerged,
                saved_states=0,
                avg_start_coarsest_iteration=avg_start,
                avg_window_size=avg_window,
                output_frequency=out_freq,
                output_start_iteration=out_start,
                output_variables_full=fd.output_variables_full,
                output_variables_surface=fd.output_variables_surface,
                bounding_box=out_bb,
            ),
            moment_reference_system=MomentReferenceSystem(
                **{"Type": "SAE"},
                origin=XYZPos(**moment_origin),
                roll_axis=XYZDir(x_dir=1.0, y_dir=0.0, z_dir=0.0),
                pitch_axis=XYZDir(x_dir=0.0, y_dir=1.0, z_dir=0.0),
                yaw_axis=XYZDir(x_dir=0.0, y_dir=0.0, z_dir=1.0),
            ),
            aero_coefficients=AeroCoefficients(
                output_start_iteration=avg_start,
                coefficients_parts=True,
                reference_area_auto=aero_cfg.reference_area_auto,
                reference_area=ref_area,
                reference_length_auto=aero_cfg.reference_length_auto,
                reference_length=ref_length,
                coefficients_along_axis=CoefficientsAlongAxis(
                    num_sections_x=aero_cfg.num_sections_x if aero_cfg.coefficients_along_axis_active else 0,
                    num_sections_y=aero_cfg.num_sections_y if aero_cfg.coefficients_along_axis_active else 0,
                    num_sections_z=aero_cfg.num_sections_z if aero_cfg.coefficients_along_axis_active else 0,
                    export_bounds=ExportBounds(
                        active=aero_cfg.export_bounds_active,
                        exclude_domain_parts=aero_cfg.export_bounds_exclude_domain_parts,
                    ),
                ),
                passive_parts=passive_parts,
            ),
            section_cut=sc_instances,
            probe_file=probe_instances,
            partial_surface=ps_instances,
            partial_volume=pv_instances,
        ),
    )

    return deck


# ---------------------------------------------------------------------------
# Probe CSV helpers
# ---------------------------------------------------------------------------

def build_probe_csv_files(template_settings: "TemplateSettings") -> dict[str, bytes]:
    """
    Generate probe location CSV file contents from template probe_files config.

    Returns a dict of {filename: csv_bytes} for each configured probe_file_instance.
    The CSV format is `x_pos;y_pos;z_pos;description` (no header), matching the
    Ultrafluid <source_file> expected format.

    The caller (configuration_service) is responsible for writing these files
    to the run output directory alongside output.xml.
    """
    result: dict[str, bytes] = {}
    for pf_cfg in template_settings.output.probe_files:
        lines: list[str] = []
        for pt in pf_cfg.points:
            desc = pt.description.replace(";", "_")  # escape semicolons in description
            lines.append(f"{pt.x_pos};{pt.y_pos};{pt.z_pos};{desc}")
        csv_content = "\n".join(lines)
        filename = f"{pf_cfg.name}.csv"
        result[filename] = csv_content.encode("utf-8")
    return result
