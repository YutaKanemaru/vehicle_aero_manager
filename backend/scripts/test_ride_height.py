"""
Ride Height / Yaw Transform test script.

Usage:
  uv run python scripts/test_ride_height.py
  uv run python scripts/test_ride_height.py <stl_path> [front_rh] [rear_rh] [yaw_deg]

Defaults:
  front_rh = 0.335 m   (front wheel axis height)
  rear_rh  = 0.335 m   (rear wheel axis height)
  yaw_deg  = 0.0 deg

Examples:
  uv run python scripts/test_ride_height.py
  uv run python scripts/test_ride_height.py data/uploads/geometries/abc123/model.stl 0.330 0.340 0.0
  uv run python scripts/test_ride_height.py data/uploads/geometries/abc123/model.stl 0.335 0.335 5.0
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BACKEND_DIR = Path(__file__).parent.parent


def main() -> None:
    from app.services.compute_engine import analyze_stl
    from app.services.ride_height_service import compute_transform
    from app.schemas.configuration import RideHeightConditionConfig, YawConditionConfig

    # ── Resolve arguments ────────────────────────────────────────────────────
    if len(sys.argv) >= 2:
        stl_path = Path(sys.argv[1])
    else:
        upload_dir = BACKEND_DIR / "data" / "uploads" / "geometries"
        stl_files = sorted(upload_dir.rglob("*.stl"))
        if not stl_files:
            print("❌ No STL files found.")
            print("   Usage: uv run python scripts/test_ride_height.py <path/to/file.stl>")
            sys.exit(1)
        stl_path = stl_files[0]
        print(f"📂 Auto-detected: {stl_path}\n")

    front_rh = float(sys.argv[2]) if len(sys.argv) >= 3 else 0.335
    rear_rh  = float(sys.argv[3]) if len(sys.argv) >= 4 else 0.335
    yaw_deg  = float(sys.argv[4]) if len(sys.argv) >= 5 else 0.0

    if not stl_path.exists():
        print(f"❌ File not found: {stl_path}")
        sys.exit(1)

    # ── Analyze STL ──────────────────────────────────────────────────────────
    print(f"🔍 Analyzing STL: {stl_path.name}")
    print("=" * 70)
    try:
        analysis = analyze_stl(stl_path, verbose=False)
    except Exception as e:
        print(f"❌ STL analysis error: {e}")
        raise

    vbbox = analysis["vehicle_bbox"]
    dims  = analysis["vehicle_dimensions"]
    print(f"Vehicle bbox:")
    print(f"  X: {vbbox['x_min']:.4f} ~ {vbbox['x_max']:.4f}  L={dims['length']:.4f} m")
    print(f"  Y: {vbbox['y_min']:.4f} ~ {vbbox['y_max']:.4f}  W={dims['width']:.4f} m")
    print(f"  Z: {vbbox['z_min']:.4f} ~ {vbbox['z_max']:.4f}  H={dims['height']:.4f} m")
    print(f"Parts: {len(analysis['part_info'])}")

    # ── Build ride height config ──────────────────────────────────────────────
    from app.schemas.template_settings import RideHeightTemplateConfig
    rh_cfg = RideHeightConditionConfig(
        enabled=True,
        target_front_wheel_axis_rh=front_rh,
        target_rear_wheel_axis_rh=rear_rh,
    )
    rh_template_cfg = RideHeightTemplateConfig(
        adjust_body_wheel_separately=False,
        use_original_wheel_position=False,
    )
    yaw_cfg = YawConditionConfig(
        center_mode="wheel_center",
        center_x=0.0,
        center_y=0.0,
    )

    # ── Compute transform ─────────────────────────────────────────────────────
    print(f"\n🔧 Computing transform...")
    print(f"   Target front wheel axis RH : {front_rh:.4f} m")
    print(f"   Target rear  wheel axis RH : {rear_rh:.4f} m")
    print(f"   Yaw angle                  : {yaw_deg:.2f} deg")
    print()

    try:
        snapshot = compute_transform(analysis, rh_cfg, yaw_deg, yaw_cfg, rh_template_cfg=rh_template_cfg)
    except Exception as e:
        print(f"❌ compute_transform error: {e}")
        raise

    # ── Print results ─────────────────────────────────────────────────────────
    tr = snapshot.get("transform", {})
    lm = snapshot.get("landmarks", {})
    vr = snapshot.get("verification", {})
    tg = snapshot.get("targets", {})

    print("─" * 70)
    print("Transform summary:")
    print(f"  Yaw angle (deg)    : {tr.get('yaw_angle_deg', 0):.4f}")
    print(f"  Pitch angle (deg)  : {tr.get('pitch_angle_deg', 0):.6f}")
    pivot = tr.get('rotation_pivot', [0, 0, 0])
    print(f"  Rotation pivot     : ({pivot[0]:.4f}, {pivot[1]:.4f}, {pivot[2]:.4f})")
    tz = tr.get('translation', [0, 0, 0])
    print(f"  Z translation      : {tz[2]:.6f} m")

    print("\nLandmarks:")
    for key, val in lm.items():
        if isinstance(val, dict) and "before" in val and "after" in val:
            b = val["before"]
            a = val["after"]
            if isinstance(b, list):
                dz = a[2] - b[2] if len(a) > 2 else a - b
                print(f"  {key:<28}  z: {b[2]:.4f} → {a[2]:.4f}  (Δ={dz:+.4f})")
            else:
                print(f"  {key:<28}  {b:.4f} → {a:.4f}  (Δ={a-b:+.4f})")

    print("\nVerification:")
    front_err = vr.get("front_error_m", 0.0)
    rear_err  = vr.get("rear_error_m", 0.0)
    front_ok = abs(front_err) < 0.001
    rear_ok  = abs(rear_err) < 0.001
    print(f"  Front target  : {tg.get('front_wheel_axis_rh', 0):.4f} m  "
          f"actual: {vr.get('front_wheel_z_actual', 0):.4f} m  "
          f"error: {front_err*1000:+.3f} mm  {'✅' if front_ok else '⚠️'}")
    print(f"  Rear  target  : {tg.get('rear_wheel_axis_rh', 0):.4f} m  "
          f"actual: {vr.get('rear_wheel_z_actual', 0):.4f} m  "
          f"error: {rear_err*1000:+.3f} mm  {'✅' if rear_ok else '⚠️'}")

    # ── Save snapshot ─────────────────────────────────────────────────────────
    out_path = BACKEND_DIR / "test_ride_height_result.json"
    out_path.write_text(json.dumps(snapshot, indent=2))
    print(f"\n💾 Full snapshot saved to: {out_path.name}")

    if snapshot.get("wheel_transforms"):
        print("\nWheel transforms:")
        for corner, wt in snapshot["wheel_transforms"].items():
            t = wt.get("translation", [0, 0, 0])
            print(f"  {corner}: tz={t[2]:+.4f} m")

    overall_ok = front_ok and rear_ok
    print("\n" + ("✅ All targets met (< 1 mm error)" if overall_ok else "⚠️  Some targets exceed 1 mm tolerance"))


if __name__ == "__main__":
    main()
