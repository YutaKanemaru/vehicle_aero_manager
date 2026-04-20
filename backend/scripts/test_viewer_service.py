"""
Standalone test script for viewer_service.py decimation + GLB export.

Usage:
    uv run python scripts/test_viewer_service.py [<stl_path>] [--ratio 0.5]

If no STL path is given, auto-detects first STL in data/uploads/geometries/.
Output GLB is saved to: backend/data/viewer_cache/test_{ratio:.3f}.glb
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# パスを通す
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.services.viewer_service import build_viewer_glb
from app.models.geometry import Geometry


def find_first_stl() -> Path | None:
    upload_dir = settings.upload_dir / "geometries"
    for p in upload_dir.rglob("*.stl"):
        return p
    for p in upload_dir.rglob("*.STL"):
        return p
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Test viewer_service decimation")
    parser.add_argument("stl_path", nargs="?", help="Path to ASCII STL file")
    parser.add_argument("--ratio", type=float, default=0.5, help="Keep ratio 0.01-1.0 (default: 0.5 = keep 50%%)",)
    args = parser.parse_args()

    # STLパス解決
    stl_path: Path
    if args.stl_path:
        stl_path = Path(args.stl_path)
    else:
        found = find_first_stl()
        if not found:
            print("ERROR: No STL file found in data/uploads/geometries/")
            sys.exit(1)
        stl_path = found
        print(f"Auto-detected STL: {stl_path}")

    if not stl_path.exists():
        print(f"ERROR: File not found: {stl_path}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  STL file : {stl_path}")
    print(f"  File size: {stl_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"  ratio    : {args.ratio} (keep {args.ratio*100:.0f}%)")
    print(f"{'='*60}\n")

    # ダミー Geometry オブジェクトを作成（DB不要）
    geometry = Geometry()
    geometry.id = "test"
    geometry.file_path = str(stl_path)
    geometry.is_linked = True  # 絶対パスとして扱う

    # キャッシュディレクトリ確保
    settings.viewer_cache_dir.mkdir(parents=True, exist_ok=True)

    # デシメーション実行
    print(f"[1/2] Running decimation (ratio={args.ratio})...")
    t0 = time.perf_counter()
    try:
        glb_bytes = build_viewer_glb(geometry, ratio=args.ratio)
        elapsed = time.perf_counter() - t0
    except Exception as e:
        print(f"\nERROR during build_viewer_glb: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 結果保存
    out_path = settings.viewer_cache_dir / f"test_{args.ratio:.3f}.glb"
    out_path.write_bytes(glb_bytes)
    elapsed_fmt = f"{elapsed:.1f}s"

    print(f"[2/2] Done.\n")
    print(f"{'='*60}")
    stl_mb = stl_path.stat().st_size / 1024 / 1024
    glb_mb = len(glb_bytes) / 1024 / 1024
    size_ratio = (1 - glb_mb / stl_mb) * 100
    print(f"  Processing time : {elapsed_fmt}")
    print(f"  Input STL size  : {stl_mb:.1f} MB")
    print(f"  Output GLB size : {glb_mb:.2f} MB  ({size_ratio:.1f}% size reduction)")
    print(f"  Saved to        : {out_path}")
    print(f"{'='*60}\n")

    # GLBが壊れていないかtrimeshで検証
    print(f"Verifying GLB integrity via trimesh...")
    print(f"  ratio (keep) : {args.ratio*100:.0f}%")
    try:
        import trimesh
        scene = trimesh.load(str(out_path))
        if hasattr(scene, "geometry"):
            meshes = scene.geometry
            total_faces = sum(m.faces.shape[0] for m in meshes.values())
            print(f"  Parts loaded : {len(meshes)}")
            print(f"  Total faces  : {total_faces:,}")
            for name, mesh in list(meshes.items())[:10]:
                print(f"    {name}: {mesh.faces.shape[0]:,} faces")
            if len(meshes) > 10:
                print(f"    ... and {len(meshes) - 10} more parts")
        else:
            print(f"  Single mesh faces: {scene.faces.shape[0]:,}")
        print("\n✅ GLB integrity: OK")
    except Exception as e:
        print(f"\n⚠️  GLB verification warning: {e}")

    print(
        "\nDone. Open the GLB file in a 3D viewer "
        "(e.g. https://gltf-viewer.donmccurdy.com/) to inspect visually."
    )


if __name__ == "__main__":
    main()
