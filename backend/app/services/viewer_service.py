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
from typing import Literal

from app.config import settings
from app.models.geometry import Geometry
from app.services.stl_decimator import (
    GLBExporter,
    QEMDecimator,
    Solid,
    STLReader,
    _decimate_worker,
)

logger = logging.getLogger(__name__)

# 各LODのデシメーションパラメータ
# ratio      : 保持率 (0.0〜1.0) — 元の face 数のうち何割を残すか
# min_faces  : パーツあたりの最低 face 数（削減しすぎを防ぐ下限、QEMDecimator内で適用）
LOD_DECIMATION_PARAMS: dict[str, dict] = {
    "low":    {"ratio": 0.50, "min_faces": 1_000},
    "medium": {"ratio": 0.50, "min_faces": 1_000},
    "high":   {"ratio": 0.50, "min_faces": 1_000},
}


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


def build_viewer_glb(geometry: Geometry, lod: Literal["low", "medium", "high"] = "medium") -> bytes:
    """
    STL を読み込み → パーツ並列 QEM デシメーション → GLB 変換・キャッシュ。

    STLReader が ASCII / Binary 両形式を自動判定する。
    ProcessPoolExecutor で各パーツを独立して decimation する
    (trimesh / fast-simplification 不使用)。
    """
    stl_path = _get_stl_path(geometry)
    params   = LOD_DECIMATION_PARAMS.get(lod, LOD_DECIMATION_PARAMS["medium"])
    ratio    = params["ratio"]

    logger.info(
        "Building GLB for geometry=%s lod=%s ratio=%.0f%%",
        geometry.id, lod, ratio * 100,
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
    cache_path = _get_cache_path(geometry.id, lod)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    GLBExporter.export(valid, cache_path)

    glb_bytes = cache_path.read_bytes()
    logger.info("GLB cached at %s (%d bytes)", cache_path, len(glb_bytes))
    return glb_bytes


def invalidate_cache(geometry_id: str) -> None:
    """指定ジオメトリの全LODキャッシュを削除する。"""
    for lod in LOD_DECIMATION_PARAMS:
        cache_path = _get_cache_path(geometry_id, lod)
        if cache_path.exists():
            cache_path.unlink()
            logger.debug("Removed viewer cache: %s", cache_path)
