"""
Compute Engine — STL ファイルの解析モジュール + XML 組み立てエンジン

trimesh + numpy のみ使用。
numpy-stl / scikit-learn は使用しない。
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import trimesh

if TYPE_CHECKING:
    from app.schemas.template_settings import ComputeOption, TargetNames, TemplateSettings
    from app.ultrafluid.schema import UfxSolverDeck


def analyze_stl(file_path: Path, verbose: bool = False) -> dict:
    """
    STL ファイルを解析してパーツ情報・車両 bbox を返す。

    マルチソリッド ASCII STL（1 ファイルに複数 solid）を想定。
    trimesh が Scene として読み込めた場合は各 solid を個別パーツとして扱う。

    verbose=True にすると各ステップの進捗を print する。
    """
    def log(msg: str) -> None:
        if verbose:
            print(msg)

    log(f"  [1/4] STL 読み込み中: {file_path.name}")
    loaded = trimesh.load(str(file_path), force="scene", process=False)

    if isinstance(loaded, trimesh.Scene):
        meshes: dict[str, trimesh.Trimesh] = dict(loaded.geometry)
    elif isinstance(loaded, trimesh.Trimesh):
        # single solid — original_filename をパーツ名にする
        meshes = {file_path.stem: loaded}
    else:
        raise ValueError(f"Unsupported trimesh type: {type(loaded)}")

    if not meshes:
        raise ValueError("STL file contains no geometry")

    log(f"  [2/4] {len(meshes)} パーツ検出")

    # ─── 車両全体 bbox ──────────────────────────────────────────────────────
    log("  [3/4] 車両全体 bbox 計算中...")
    all_vertices = np.concatenate([m.vertices for m in meshes.values()], axis=0)

    vehicle_bbox = {
        "x_min": float(all_vertices[:, 0].min()),
        "x_max": float(all_vertices[:, 0].max()),
        "y_min": float(all_vertices[:, 1].min()),
        "y_max": float(all_vertices[:, 1].max()),
        "z_min": float(all_vertices[:, 2].min()),
        "z_max": float(all_vertices[:, 2].max()),
    }

    vehicle_dimensions = {
        "length": round(float(vehicle_bbox["x_max"] - vehicle_bbox["x_min"]), 6),
        "width":  round(float(vehicle_bbox["y_max"] - vehicle_bbox["y_min"]), 6),
        "height": round(float(vehicle_bbox["z_max"] - vehicle_bbox["z_min"]), 6),
    }

    # ─── パーツ別情報 ────────────────────────────────────────────────────────
    log(f"  [4/4] パーツ別情報を計算中 ({len(meshes)} parts)...")
    part_info: dict[str, dict] = {}
    for i, (name, mesh) in enumerate(meshes.items(), 1):
        log(f"        [{i}/{len(meshes)}] {name}")
        verts = mesh.vertices
        centroid = verts.mean(axis=0)
        part_info[name] = {
            "centroid": [round(float(v), 6) for v in centroid],
            "bbox": {
                "x_min": float(verts[:, 0].min()),
                "x_max": float(verts[:, 0].max()),
                "y_min": float(verts[:, 1].min()),
                "y_max": float(verts[:, 1].max()),
                "z_min": float(verts[:, 2].min()),
                "z_max": float(verts[:, 2].max()),
            },
            "vertex_count": int(len(verts)),
            "face_count": int(len(mesh.faces)),
        }

    log("  ✅ 解析完了")
    return {
        "parts": list(meshes.keys()),
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

def resolve_compute_flags(
    template_flags: ComputeOption,
) -> ComputeOption:
    """
    Template の ComputeOption に依存関係ルールを適用して返す。

    依存関係ルール:
    - rotate_wheels=False → moving_ground を強制 False
    """
    from app.schemas.template_settings import ComputeOption as CO

    flags = CO(**template_flags.model_dump())

    # 依存関係の強制
    if not flags.rotate_wheels:
        flags.moving_ground = False

    return flags


def compute_domain_bbox(vehicle_bbox: dict, multipliers: list[float]) -> dict:
    """
    車両 bbox に 6 つの相対倍率を掛けて絶対的な計算領域 bbox を返す。

    multipliers: [x_min_mult, x_max_mult, y_min_mult, y_max_mult, z_min_mult, z_max_mult]
    規約: x_min_mult と z_min_mult は車両 COG から前後方向に掛ける
    """
    cx = (vehicle_bbox["x_min"] + vehicle_bbox["x_max"]) / 2
    cy = (vehicle_bbox["y_min"] + vehicle_bbox["y_max"]) / 2
    length = vehicle_bbox["x_max"] - vehicle_bbox["x_min"]
    width  = vehicle_bbox["y_max"] - vehicle_bbox["y_min"]
    height = vehicle_bbox["z_max"] - vehicle_bbox["z_min"]

    x_min_m, x_max_m, y_min_m, y_max_m, z_min_m, z_max_m = multipliers

    return {
        "x_min": cx + x_min_m * length,
        "x_max": cx + x_max_m * length,
        "y_min": cy + y_min_m * width,
        "y_max": cy + y_max_m * width,
        "z_min": vehicle_bbox["z_min"] + z_min_m * height,
        "z_max": vehicle_bbox["z_min"] + z_max_m * height,
    }


def compute_coarsest_mesh_size(finest_res: float, n_levels: int) -> float:
    """finest_resolution_size × 2^n_levels"""
    return finest_res * (2 ** n_levels)


def _matches_any(part_name: str, patterns: list[str]) -> bool:
    """パーツ名がパターンリストのいずれかに部分一致するか判定"""
    return any(p and p.lower() in part_name.lower() for p in patterns)


def classify_wheels(
    analysis_result: dict,
    target_names: TargetNames,
) -> dict[str, dict]:
    """
    analysis_result の part_info からホイール部品を FR-LH/FR-RH/RR-LH/RR-RH に分類する。

    個別 PID (wheel_tire_fr_lh 等) が指定されていればそれを優先。
    ない場合は target_names.wheel パターンにマッチした部品を重心で自動分類。

    Returns: {"fr_lh": part_info, "fr_rh": ..., "rr_lh": ..., "rr_rh": ...}
    """
    part_info: dict[str, dict] = analysis_result.get("part_info", {})

    # 個別 PID が指定されている場合は直接マッピング
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

    # 自動分類: wheel パターンにマッチした部品を重心で振り分け
    wheel_parts = {
        name: info for name, info in part_info.items()
        if _matches_any(name, target_names.wheel)
        and not _matches_any(name, ["VREV_", "Overset"])  # OSM 領域を除外
    }

    if not wheel_parts:
        return {}

    # 車両 COG (x, y)
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
    rim_vertices: np.ndarray | None = None,
) -> dict:
    """
    ホイール情報から overset rotating インスタンスのパラメータを計算する。

    Returns:
        {"center": XYZPos dict, "axis": XYZDir dict, "rpm": float, "radius": float}
    """
    bbox = part_info["bbox"]
    centroid = part_info["centroid"]

    # ホイール半径 = Z 方向の寸法 / 2 (回転軸が Y 方向の場合)
    # または bbox から推定
    radius_y = (bbox["z_max"] - bbox["z_min"]) / 2
    radius_z = (bbox["y_max"] - bbox["y_min"]) / 2
    radius = min(radius_y, radius_z) if radius_y > 0 and radius_z > 0 else max(radius_y, radius_z)

    # rim vertices が与えられていれば PCA で軸を計算
    if rim_vertices is not None and len(rim_vertices) >= 3:
        centered = rim_vertices - rim_vertices.mean(axis=0)
        _, _, vt = np.linalg.svd(centered, full_matrices=False)
        axis = vt[2]  # 最小分散方向 = 回転軸
        if axis[1] < 0:
            axis = -axis  # Y 正方向に揃える
        axis_dir = {"x_dir": float(axis[0]), "y_dir": float(axis[1]), "z_dir": float(axis[2])}
    else:
        # デフォルト: Y 軸方向 (標準的な車両座標系)
        axis_dir = {"x_dir": 0.0, "y_dir": 1.0, "z_dir": 0.0}

    # RPM = (inflow_velocity / circumference) × 60
    circumference = 2 * math.pi * radius
    rpm = (inflow_velocity / circumference) * 60.0 if circumference > 0 else 0.0

    center = {
        "x_pos": centroid[0],
        "y_pos": centroid[1],
        "z_pos": centroid[2],
    }

    return {"center": center, "axis": axis_dir, "rpm": rpm, "radius": radius}


def compute_porous_axis(part_info: dict, vertices: np.ndarray | None = None) -> dict:
    """
    ポーラス部品の主軸方向を PCA で計算する。
    vertices が与えられない場合は bbox から推定。

    Returns: {"x_dir": float, "y_dir": float, "z_dir": float}
    """
    if vertices is not None and len(vertices) >= 3:
        centered = vertices - vertices.mean(axis=0)
        _, _, vt = np.linalg.svd(centered, full_matrices=False)
        axis = vt[0]  # 最大分散方向 = 主軸 (= ポーラス流れ方向)
        if axis[0] < 0:
            axis = -axis  # X 正方向に揃える
        return {"x_dir": float(axis[0]), "y_dir": float(axis[1]), "z_dir": float(axis[2])}

    # bbox から推定: 最も薄い方向が porous 方向
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


def _compute_num_iterations(
    simulation_time: float,
    inflow_velocity: float,
    coarsest_mesh_size: float,
    mach_factor: float,
) -> int:
    """
    コース最粗メッシュでの総イテレーション数を計算する。

    dt_coarsest ≈ coarsest_mesh_size / (inflow_velocity * mach_factor)
    num_iter = ceil(simulation_time / dt_coarsest)
    """
    if inflow_velocity <= 0 or coarsest_mesh_size <= 0:
        return 10000
    dt = coarsest_mesh_size / (inflow_velocity * mach_factor)
    return max(1, math.ceil(simulation_time / dt))


def _compute_avg_iteration(
    avg_start_time: float,
    inflow_velocity: float,
    coarsest_mesh_size: float,
    mach_factor: float,
) -> int:
    return max(0, _compute_num_iterations(
        avg_start_time, inflow_velocity, coarsest_mesh_size, mach_factor
    ))


def assemble_ufx_solver_deck(
    template_settings: TemplateSettings,
    analysis_result: dict,
    inflow_velocity: float,
    yaw_angle: float = 0.0,
    source_file: str = "geometry.stl",
) -> UfxSolverDeck:
    """
    Template (Fixed) + Geometry analysis_result (Computed) + Config (UserInput)
    から UfxSolverDeck を組み立てる。

    1. resolve_compute_flags()
    2. 有効な inflow_velocity / simulation_time を決定 (Config 優先)
    3. compute_domain_bbox()
    4. classify_wheels() + compute_wheel_kinematics()   [rotate_wheels=True のみ]
    5. compute_porous_axis() per porous part            [porous_media=True のみ]
    6. compute_coarsest_mesh_size()
    7. UfxSolverDeck を組み立て
    """
    # 遅延インポート (循環定義を避けるため)
    from app.ultrafluid.schema import (
        AeroCoefficients, BoundaryConditions, BoundingBox,
        CoefficientsAlongAxis, DomainPart, ExportBounds,
        FileFormat, FluidBCMoving, FluidBCNonReflectivePressure,
        FluidBCRotating, FluidBCSlip, FluidBCStatic, FluidBCVelocity,
        Geometry, InletInstance, Material, Meshing, MeshingGeneral,
        MomentReferenceSystem, Overset, Output, OutputCoarsening,
        OutputGeneral, OutputVariablesFull, OutputVariablesSurface,
        AeroCoefficients, BoxInstance, BoundingRange, CustomInstance,
        DomainPartInstance, OffsetInstance, OutletInstance, PorousAxis,
        PorousInstance, Refinement, RotatingInstance, Simulation,
        SimulationGeneral, Sources, SurfaceMeshOptimization,
        TriangleSplitting, TurbulenceBoundingBox, TurbulenceInstance,
        TurbulencePoint, UfxSolverDeck, Version, WallInstance, WallModeling,
        XYZDir, XYZPos,
    )

    sp = template_settings.simulation_parameter
    so = template_settings.setup_option
    setup = template_settings.setup
    tn = template_settings.target_names
    vbbox = analysis_result.get("vehicle_bbox", {})
    part_info: dict = analysis_result.get("part_info", {})

    # ── 1. Compute flags ──────────────────────────────────────────────────
    flags = resolve_compute_flags(so.compute)

    # ── 2. 有効パラメータ ──────────────────────────────────────────────────
    simulation_time = sp.simulation_time
    yaw_angle_deg   = yaw_angle  # degrees
    temperature_k   = (sp.temperature + 273.15) if so.simulation.temperature_degree else sp.temperature

    # ── 3. Computed メッシュパラメータ ─────────────────────────────────────
    coarsest = compute_coarsest_mesh_size(sp.finest_resolution_size, sp.number_of_resolution)

    # ── 4. Domain bounding box ────────────────────────────────────────────
    if vbbox:
        abs_bbox = compute_domain_bbox(vbbox, setup.domain_bounding_box)
    else:
        abs_bbox = {"x_min": -10.0, "x_max": 30.0, "y_min": -15.0, "y_max": 15.0, "z_min": 0.0, "z_max": 8.0}

    domain_bb = BoundingBox(**abs_bbox)

    # ── 5. ホイール運動学 ──────────────────────────────────────────────────
    rotating_instances: list[RotatingInstance] = []
    wheel_wall_instances: list[WallInstance] = []
    if flags.rotate_wheels:
        wheel_map = classify_wheels(analysis_result, tn)
        osm_map = {
            "fr_lh": tn.overset_fr_lh,
            "fr_rh": tn.overset_fr_rh,
            "rr_lh": tn.overset_rr_lh,
            "rr_rh": tn.overset_rr_rh,
        }
        label_map = {
            "fr_lh": "VREV_Front_Left",
            "fr_rh": "VREV_Front_Right",
            "rr_lh": "VREV_Rear_Left",
            "rr_rh": "VREV_Rear_Right",
        }
        for key, winfo in wheel_map.items():
            kin = compute_wheel_kinematics(winfo, inflow_velocity)
            osm_pid = osm_map.get(key, "")
            ri = RotatingInstance(
                name=label_map.get(key, key),
                rpm=kin["rpm"],
                center=XYZPos(**kin["center"]),
                axis=XYZDir(**kin["axis"]),
                parts=[osm_pid] if osm_pid else [],
            )
            rotating_instances.append(ri)
            # rotating wall BC (ホイール表面)
            tire_pid_map = {
                "fr_lh": tn.wheel_tire_fr_lh,
                "fr_rh": tn.wheel_tire_fr_rh,
                "rr_lh": tn.wheel_tire_rr_lh,
                "rr_rh": tn.wheel_tire_rr_rh,
            }
            tire_pid = tire_pid_map.get(key, "")
            if tire_pid:
                wheel_wall_instances.append(WallInstance(
                    name=f"Wheel_{key.upper()}",
                    parts=[tire_pid],
                    fluid_bc_settings=FluidBCRotating(
                        type="rotating",
                        rpm=kin["rpm"],
                        center=XYZPos(**kin["center"]),
                        axis=XYZDir(**kin["axis"]),
                    ),
                ))

    # ── 6. Porous sources ─────────────────────────────────────────────────
    porous_instances: list[PorousInstance] = []
    if flags.porous_media:
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

    # ── 7. Turbulence generators ──────────────────────────────────────────
    turbulence_instances: list[TurbulenceInstance] = []
    if flags.turbulence_generator and so.boundary_condition.turbulence_generator.activate_body_tg:
        # デフォルト: 車体前方の TG
        if vbbox:
            tg_body_x = vbbox["x_min"] - coarsest
            turbulence_instances.append(TurbulenceInstance(
                name="tg_body",
                num_eddies=100,
                length_scale=0.1,
                turbulence_intensity=0.01,
                point=TurbulencePoint(x_pos=tg_body_x),
                bounding_box=TurbulenceBoundingBox(
                    y_min=abs_bbox["y_min"] * 0.8,
                    z_min=abs_bbox["z_min"],
                    y_max=abs_bbox["y_max"] * 0.8,
                    z_max=abs_bbox["z_max"] * 0.5,
                ),
            ))
        if so.boundary_condition.turbulence_generator.activate_ground_tg and flags.moving_ground and vbbox:
            turbulence_instances.append(TurbulenceInstance(
                name="tg_ground",
                num_eddies=100,
                length_scale=0.05,
                turbulence_intensity=0.005,
                point=TurbulencePoint(x_pos=abs_bbox["x_min"] + coarsest),
                bounding_box=TurbulenceBoundingBox(
                    y_min=abs_bbox["y_min"] * 0.5,
                    z_min=abs_bbox["z_min"],
                    y_max=abs_bbox["y_max"] * 0.5,
                    z_max=coarsest * 2,
                ),
            ))

    # ── 8. Inlet velocity vector (yaw angle 対応) ─────────────────────────
    yaw_rad = math.radians(yaw_angle_deg)
    vx = inflow_velocity * math.cos(yaw_rad)
    vy = inflow_velocity * math.sin(yaw_rad)

    # ── 9. Wall BCs (belt + ground) ───────────────────────────────────────
    wall_instances: list[WallInstance] = list(wheel_wall_instances)

    # Belt (moving ground) — center belt
    belt_bc = so.boundary_condition.belt
    if belt_bc.opt_belt_system and flags.moving_ground:
        wall_instances.append(WallInstance(
            name="Belt_Center",
            parts=["Belt_Center"],
            fluid_bc_settings=FluidBCMoving(
                type="moving",
                velocity=XYZDir(x_dir=vx, y_dir=vy, z_dir=0.0),
            ),
        ))
        # Wheel belts
        for wkey in ("fr_lh", "fr_rh", "rr_lh", "rr_rh"):
            wall_instances.append(WallInstance(
                name=f"Belt_Wheel_{wkey.upper()}",
                parts=[f"Belt_Wheel_{wkey.upper()}"],
                fluid_bc_settings=FluidBCMoving(
                    type="moving",
                    velocity=XYZDir(x_dir=vx, y_dir=vy, z_dir=0.0),
                ),
            ))
    else:
        wall_instances.append(WallInstance(
            name="Ground",
            parts=["Ground"],
            fluid_bc_settings=FluidBCSlip(type="slip"),
        ))

    # ── 10. Iteration counts ───────────────────────────────────────────────
    num_iter   = _compute_num_iterations(simulation_time, inflow_velocity, coarsest, sp.mach_factor)
    avg_start  = _compute_avg_iteration(sp.start_averaging_time, inflow_velocity, coarsest, sp.mach_factor)
    avg_window = _compute_avg_iteration(sp.avg_window_size, inflow_velocity, coarsest, sp.mach_factor)
    out_start  = _compute_avg_iteration(
        sp.output_start_time if sp.output_start_time is not None else simulation_time,
        inflow_velocity, coarsest, sp.mach_factor,
    )
    out_freq   = _compute_avg_iteration(
        sp.output_interval_time if sp.output_interval_time is not None else simulation_time,
        inflow_velocity, coarsest, sp.mach_factor,
    )

    # ── 11. Mesh refinement ────────────────────────────────────────────────
    box_instances = [
        BoxInstance(
            name=name,
            refinement_level=br.level,
            bounding_box=BoundingBox(
                x_min=br.box[0], x_max=br.box[1],
                y_min=br.box[2], y_max=br.box[3],
                z_min=br.box[4], z_max=br.box[5],
            ),
        )
        for name, br in setup.meshing.box_refinement.items()
    ]
    box_instances += [
        BoxInstance(
            name=name,
            refinement_level=br.level,
            bounding_box=BoundingBox(
                x_min=br.box[0], x_max=br.box[1],
                y_min=br.box[2], y_max=br.box[3],
                z_min=br.box[4], z_max=br.box[5],
            ),
        )
        for name, br in setup.meshing.part_box_refinement.items()
    ]
    offset_instances = [
        OffsetInstance(
            name=name,
            normal_distance=orf.normal_distance,
            refinement_level=orf.level,
            parts=orf.parts,
        )
        for name, orf in setup.meshing.offset_refinement.items()
    ]
    custom_instances = [
        CustomInstance(name=name, refinement_level=cr.level, parts=cr.parts)
        for name, cr in setup.meshing.custom_refinement.items()
    ]

    # ── 12. Assemble UfxSolverDeck ─────────────────────────────────────────
    deck = UfxSolverDeck(
        version=Version(gui_version="2024", solver_version="2024"),
        simulation=Simulation(
            general=SimulationGeneral(
                num_coarsest_iterations=num_iter,
                mach_factor=sp.mach_factor,
                num_ramp_up_iterations=sp.num_ramp_up_iter,
            ),
            material=Material(
                name="Air",
                density=sp.density,
                dynamic_viscosity=sp.dynamic_viscosity,
                temperature=temperature_k,
                specific_gas_constant=sp.specific_gas_constant,
            ),
            wall_modeling=WallModeling(wall_model="GLW", coupling="adaptive_two-way"),
        ),
        geometry=Geometry(
            source_file=source_file,
            baffle_parts=[
                name for name in part_info
                if _matches_any(name, tn.baffle)
            ],
            domain_bounding_box=domain_bb,
            triangle_plinth=False,
            surface_mesh_optimization=SurfaceMeshOptimization(
                triangle_splitting=TriangleSplitting(
                    active=so.meshing.triangle_splitting,
                    max_absolute_edge_length=0.0,
                    max_relative_edge_length=9.0,
                )
            ),
            domain_part=DomainPart(export_mesh=False, domain_part_instances=[]),
        ),
        meshing=Meshing(
            general=MeshingGeneral(
                coarsest_mesh_size=coarsest,
                mesh_preview=False,
                mesh_export=False,
                refinement_level_transition_layers=8,
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
                file_format=FileFormat(ensight=True, h3d=False),
                output_coarsening=OutputCoarsening(
                    active=True,
                    coarsen_by_num_refinement_levels=1,
                    coarsest_target_refinement_level=4,
                    export_uncoarsened_voxels=False,
                ),
                time_varying_geometry_output=False,
                merge_output_files=True,
                delete_unmerged_output_files=True,
                saved_states=0,
                avg_start_coarsest_iteration=avg_start,
                avg_window_size=avg_window,
                output_frequency=out_freq,
                output_start_iteration=out_start,
                output_variables_full=OutputVariablesFull(
                    time_avg_pressure=True,
                    time_avg_velocity=True,
                    time_avg_wall_shear_stress=True,
                    surface_normal=True,
                    lambda_2=True,
                    q_criterion=True,
                ),
                output_variables_surface=OutputVariablesSurface(
                    time_avg_pressure=True,
                    time_avg_wall_shear_stress=True,
                    surface_normal=True,
                ),
                bounding_box=domain_bb,
            ),
            moment_reference_system=MomentReferenceSystem(
                **{"Type": "SAE"},
                origin=XYZPos(x_pos=0.0, y_pos=0.0, z_pos=0.0),
                roll_axis=XYZDir(x_dir=1.0, y_dir=0.0, z_dir=0.0),
                pitch_axis=XYZDir(x_dir=0.0, y_dir=1.0, z_dir=0.0),
                yaw_axis=XYZDir(x_dir=0.0, y_dir=0.0, z_dir=1.0),
            ),
            aero_coefficients=AeroCoefficients(
                output_start_iteration=avg_start,
                coefficients_parts=False,
                reference_area_auto=True,
                reference_area=1.0,
                reference_length_auto=True,
                reference_length=1.0,
                coefficients_along_axis=CoefficientsAlongAxis(
                    num_sections_x=10,
                    num_sections_y=10,
                    num_sections_z=5,
                    export_bounds=ExportBounds(active=True, exclude_domain_parts=True),
                ),
                passive_parts=list(tn.windtunnel),
            ),
            section_cut=[],
            partial_surface=[],
            partial_volume=[],
        ),
    )

    return deck
