"""
3D Viewer用のGLBファイル生成・キャッシュサービス。

trimesh.load() を使わずカスタムストリーミングパーサーで STL を読み込み、
ThreadPoolExecutor でパーツ並列デシメーション → GLB に変換してキャッシュする。
compute_engine._parse_stl_ascii_streaming と同じトークン解析ロジックを使用するが、
こちらは頂点配列 (vertices_buf / faces_buf) を保持してメッシュを構築する点が異なる。
"""
from __future__ import annotations

import concurrent.futures
import logging
from pathlib import Path
from typing import Literal

import numpy as np

from app.config import settings
from app.models.geometry import Geometry
from app.services.compute_engine import _detect_stl_format

logger = logging.getLogger(__name__)

# 各LODのデシメーションパラメータ
# target_reduction : 削減率 (0.0〜1.0) — 元の face 数に対して何割削減するか
# agg              : fast-simplification aggressiveness (1〜10)
#                    高いほど平面を優先削減・曲面を保持する挙動が強くなる
#                    5=デフォルト(バランス), 7=平面優先, 9=積極的（形状崩れリスク有）
# min_faces        : パーツあたりの最低 face 数（削減しすぎを防ぐ下限）
LOD_DECIMATION_PARAMS: dict[str, dict] = {
    "low":    {"target_reduction": 0.50, "agg": 7,   "min_faces": 1_000},
    "medium": {"target_reduction": 0.50, "agg": 5,   "min_faces": 1_000},
    "high":   {"target_reduction": 0.50, "agg": 3,   "min_faces": 1_000},
}

# 後方互換用エイリアス
LOD_TARGET_REDUCTION: dict[str, float] = {k: v["target_reduction"] for k, v in LOD_DECIMATION_PARAMS.items()}
LOD_MIN_FACES_PER_PART: dict[str, int] = {k: v["min_faces"] for k, v in LOD_DECIMATION_PARAMS.items()}


def _get_stl_path(geometry: Geometry) -> Path:
    if geometry.is_linked:
        return Path(geometry.file_path)
    return settings.upload_dir / geometry.file_path


def _get_cache_path(geometry_id: str, lod: str) -> Path:
    return settings.viewer_cache_dir / f"{geometry_id}_{lod}.glb"


def get_cached_glb(geometry_id: str, lod: str) -> bytes | None:
    """キャッシュされたGLBバイト列を返す。なければ None。"""
    cache_path = _get_cache_path(geometry_id, lod)
    if cache_path.exists():
        return cache_path.read_bytes()
    return None


def _parse_solids_for_decimation(
    stl_path: Path,
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """
    ASCII STL をストリーミング解析し、各 solid の頂点・面配列を返す。

    compute_engine._parse_stl_ascii_streaming と同じトークン解析ロジックだが、
    デシメーション用に頂点配列を保持する。
    ピークメモリは最大 solid 1 つ分の頂点数に比例 (ファイル全体ではない)。

    Returns: [(name, vertices_np float32, faces_np int32), ...]
    """
    result: list[tuple[str, np.ndarray, np.ndarray]] = []
    seen_names: set[str] = set()

    current_name: str | None = None
    vertices_buf: list[list[float]] = []
    faces_buf: list[list[int]] = []
    # 1 facet につき 3 頂点 → face = [v_base, v_base+1, v_base+2]
    _v_base = 0

    with stl_path.open("r", encoding="ascii", errors="replace") as f:
        for raw_line in f:
            line = raw_line.strip()
            lower = line.lower()

            if lower.startswith("solid"):
                name_part = line[5:].strip()
                base_name = name_part if name_part else stl_path.stem
                candidate = base_name
                suffix = 0
                while candidate in seen_names:
                    suffix += 1
                    candidate = f"{base_name}_{suffix}"
                current_name = candidate
                seen_names.add(current_name)
                vertices_buf = []
                faces_buf = []
                _v_base = 0

            elif lower.startswith("vertex"):
                parts = line.split()
                if len(parts) == 4:
                    try:
                        vertices_buf.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    except ValueError:
                        pass

            elif lower.startswith("endfacet"):
                # endfacet の直前に 3 頂点が積まれているはず
                n = len(vertices_buf)
                # 今回の facet の頂点インデックスを 3 つ取得
                if n - _v_base == 3:
                    faces_buf.append([_v_base, _v_base + 1, _v_base + 2])
                _v_base = len(vertices_buf)

            elif lower.startswith("endsolid") and current_name is not None:
                if vertices_buf and faces_buf:
                    v_arr = np.array(vertices_buf, dtype=np.float32)
                    f_arr = np.array(faces_buf, dtype=np.int32)
                    result.append((current_name, v_arr, f_arr))
                current_name = None
                vertices_buf = []
                faces_buf = []
                _v_base = 0

    if not result:
        raise ValueError("No valid solid definitions found in STL file.")

    return result


def _decimate_solid(
    name: str,
    vertices: np.ndarray,
    faces: np.ndarray,
    target_reduction: float,
    min_faces: int,
) -> tuple[str, "trimesh.Trimesh"]:
    """
    1 パーツのデシメーションを実行する (ThreadPoolExecutor から呼ばれる)。

    target_reduction: 削減率 (0.0〜1.0)。0.75 なら元の 75% を削減し 25% を残す。
    min_faces: このパーツの最低 face 数 (下限ガード)。

    trimesh.Trimesh を直接構築 (trimesh.load() 不使用)。
    QEM デシメーション失敗時は numpy 均等サブサンプリングにフォールバック。
    """
    import trimesh  # ワーカースレッドでインポート

    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    current_faces = len(mesh.faces)

    # 削減後の目標 face 数を計算（下限保護）
    target_faces = max(min_faces, int(current_faces * (1.0 - target_reduction)))

    if current_faces <= target_faces:
        return name, mesh

    # QEM デシメーション
    try:
        decimated = mesh.simplify_quadric_decimation(face_count=target_faces)
        if len(decimated.faces) > 0:
            actual_reduction = (1.0 - len(decimated.faces) / current_faces) * 100
            logger.debug("  Part %s: %d → %d faces (QEM, %.1f%% reduced)", name, current_faces, len(decimated.faces), actual_reduction)
            return name, decimated
    except Exception as e:
        logger.warning("QEM failed for part %s: %s — falling back to subsampling.", name, e)

    # フォールバック: numpy 均等サブサンプリング
    step = max(1, current_faces // target_faces)
    sampled_faces = faces[::step]
    used_indices = np.unique(sampled_faces)
    index_map = np.zeros(len(vertices), dtype=np.int64)
    index_map[used_indices] = np.arange(len(used_indices))
    new_vertices = vertices[used_indices]
    new_faces = index_map[sampled_faces]
    fallback = trimesh.Trimesh(vertices=new_vertices, faces=new_faces, process=False)
    actual_reduction = (1.0 - len(fallback.faces) / current_faces) * 100
    logger.debug("  Part %s: %d → %d faces (subsampling, %.1f%% reduced)", name, current_faces, len(fallback.faces), actual_reduction)
    return name, fallback


def build_viewer_glb(geometry: Geometry, lod: Literal["low", "medium", "high"] = "medium") -> bytes:
    """
    STL をストリーミング解析 → パーツ並列デシメーション → GLB 変換・キャッシュ。

    trimesh.load() を使用しない。
    _parse_solids_for_decimation() でパーツ別頂点配列を取得し、
    ThreadPoolExecutor で _decimate_solid() を並列実行する。
    """
    import trimesh

    stl_path = _get_stl_path(geometry)
    target_reduction = LOD_TARGET_REDUCTION.get(lod, LOD_TARGET_REDUCTION["medium"])
    min_faces = LOD_MIN_FACES_PER_PART.get(lod, LOD_MIN_FACES_PER_PART["medium"])

    logger.info(
        "Building GLB for geometry=%s lod=%s target_reduction=%.0f%% min_faces=%d",
        geometry.id, lod, target_reduction * 100, min_faces,
    )

    # バイナリ STL は非対応
    fmt = _detect_stl_format(stl_path)
    if fmt == "binary":
        raise ValueError(
            "Binary STL format is not supported. Please convert to ASCII STL before uploading."
        )

    # ストリーミング解析
    solids = _parse_solids_for_decimation(stl_path)
    logger.info("  Parsed %d solid(s) from %s", len(solids), stl_path.name)

    # 並列デシメーション（各パーツが独立して同じ削減率を適用）
    meshes: dict[str, trimesh.Trimesh] = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(_decimate_solid, name, verts, faces, target_reduction, min_faces): name
            for name, verts, faces in solids
        }
        for future in concurrent.futures.as_completed(futures):
            part_name = futures[future]
            try:
                result_name, mesh = future.result()
                if len(mesh.faces) > 0:
                    meshes[result_name] = mesh
            except Exception as e:
                logger.error("Decimation failed for part %s: %s", part_name, e)

    if not meshes:
        raise ValueError(f"No valid mesh found in STL: {stl_path}")

    # パーツ名付き Scene を構築して GLB 出力
    out_scene = trimesh.scene.scene.Scene()
    for name, mesh in meshes.items():
        out_scene.add_geometry(mesh, node_name=name, geom_name=name)

    glb_bytes: bytes = out_scene.export(file_type="glb")

    # キャッシュに保存
    cache_path = _get_cache_path(geometry.id, lod)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(glb_bytes)
    logger.info("GLB cached at %s (%d bytes)", cache_path, len(glb_bytes))

    return glb_bytes


def invalidate_cache(geometry_id: str) -> None:
    """指定ジオメトリの全LODキャッシュを削除する。"""
    for lod in LOD_TARGET_REDUCTION:
        cache_path = _get_cache_path(geometry_id, lod)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug("Removed viewer cache: %s", cache_path)
