"""
Compute Engine テストスクリプト
使い方:
  uv run python test_compute_engine.py
  uv run python test_compute_engine.py <STLファイルパス>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.compute_engine import analyze_stl


def main() -> None:
    # ---- ファイルパス解決 ------------------------------------------------
    if len(sys.argv) >= 2:
        file_path = Path(sys.argv[1])
    else:
        upload_dir = Path(__file__).parent / "data" / "uploads" / "geometries"
        stl_files = sorted(upload_dir.rglob("*.stl"))
        if not stl_files:
            print("❌ STL ファイルが見つかりません")
            print("   usage: uv run python test_compute_engine.py <path/to/file.stl>")
            sys.exit(1)
        file_path = stl_files[0]
        print(f"📂 自動検出: {file_path}\n")

    if not file_path.exists():
        print(f"❌ ファイルが存在しません: {file_path}")
        sys.exit(1)

    print(f"🔍 解析開始: {file_path.name}")
    print("=" * 70)

    # ---- 解析実行 --------------------------------------------------------
    try:
        result = analyze_stl(file_path, verbose=True)
    except Exception as e:
        print(f"❌ 解析エラー: {e}")
        raise

    # ---- 車両全体 bbox --------------------------------------------------
    bbox = result["vehicle_bbox"]
    dims = result["vehicle_dimensions"]
    print("\n【車両全体】")
    print(f"  Length (X): {dims['length']:.4f} m  ({bbox['x_min']:.4f} ~ {bbox['x_max']:.4f})")
    print(f"  Width  (Y): {dims['width']:.4f} m  ({bbox['y_min']:.4f} ~ {bbox['y_max']:.4f})")
    print(f"  Height (Z): {dims['height']:.4f} m  ({bbox['z_min']:.4f} ~ {bbox['z_max']:.4f})")

    # ---- パーツ一覧 -----------------------------------------------------
    part_info = result["part_info"]
    print(f"\n【パーツ一覧】({len(part_info)} parts)")
    print(f"  {'パーツ名':<45} {'頂点':>8} {'面':>8}   重心 (x, y, z)")
    print("  " + "-" * 85)
    for name, info in sorted(part_info.items()):
        cx, cy, cz = info["centroid"]
        print(
            f"  {name:<45} "
            f"{info['vertex_count']:>8,} "
            f"{info['face_count']:>8,}   "
            f"({cx:+.3f}, {cy:+.3f}, {cz:+.3f})"
        )

    # ---- JSON 出力 -------------------------------------------------------
    out_path = Path(__file__).parent / "test_compute_engine_result.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n✅ 完了 — JSON を保存: {out_path}")


if __name__ == "__main__":
    main()
