"""
Compute Engine — STL ファイルの解析モジュール

trimesh + numpy のみ使用。
numpy-stl / scikit-learn は使用しない。

出力 JSON:
{
  "parts": ["Body", "WheelFL", ...],
  "vehicle_bbox": {"x_min":..., "x_max":..., "y_min":..., "y_max":..., "z_min":..., "z_max":...},
  "vehicle_dimensions": {"length":..., "width":..., "height":...},
  "part_info": {
    "Body": {
      "centroid": [x,y,z],
      "bbox": {x_min,...},
      "vertex_count": N,
      "face_count": N
    }, ...
  }
}
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh


def analyze_stl(file_path: Path) -> dict:
    """
    STL ファイルを解析してパーツ情報・車両 bbox を返す。

    マルチソリッド ASCII STL（1 ファイルに複数 solid）を想定。
    trimesh が Scene として読み込めた場合は各 solid を個別パーツとして扱う。
    """
    loaded = trimesh.load(str(file_path), force="scene")

    if isinstance(loaded, trimesh.Scene):
        meshes: dict[str, trimesh.Trimesh] = dict(loaded.geometry)
    elif isinstance(loaded, trimesh.Trimesh):
        # single solid — original_filename をパーツ名にする
        meshes = {file_path.stem: loaded}
    else:
        raise ValueError(f"Unsupported trimesh type: {type(loaded)}")

    if not meshes:
        raise ValueError("STL file contains no geometry")

    # ─── 車両全体 bbox ──────────────────────────────────────────────────────
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
    part_info: dict[str, dict] = {}
    for name, mesh in meshes.items():
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

    return {
        "parts": list(meshes.keys()),
        "vehicle_bbox": vehicle_bbox,
        "vehicle_dimensions": vehicle_dimensions,
        "part_info": part_info,
    }


def analyze_stl_to_json(file_path: Path) -> str:
    """analyze_stl の結果を JSON 文字列で返す。"""
    return json.dumps(analyze_stl(file_path))
