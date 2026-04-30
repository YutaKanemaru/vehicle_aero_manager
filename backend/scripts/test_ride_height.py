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

Outputs:
  backend/test_ride_height_result.json   ← full transform snapshot (JSON)
  backend/{stl_stem}_transformed.stl     ← transformed STL file

Unit test mode (no STL file required):
  uv run python scripts/test_ride_height.py --unit
  Verifies: ref_front=0.4 m, ref_rear=0.4 m → target_front=0.3 m, target_rear=0.35 m

Full pattern suite (no STL file required):
  uv run python scripts/test_ride_height.py --suite
  Runs 12 posture-change patterns covering all combinations of heave / pitch / yaw /
  separate-body-wheel / user-input-reference modes. Exits 1 if any case fails.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BACKEND_DIR = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Shared dummy analysis_result used by --unit and --suite modes
# ---------------------------------------------------------------------------
_REF_Z = 0.4  # reference wheel axis Z (m) for user_input mode

_DUMMY_ANALYSIS: dict = {
    "vehicle_bbox": {
        "x_min": -2.5, "x_max": 2.5,
        "y_min": -1.0, "y_max": 1.0,
        "z_min": 0.0,  "z_max": 1.5,
    },
    "vehicle_dimensions": {"length": 5.0, "width": 2.0, "height": 1.5},
    "part_info": {},
}

# ---------------------------------------------------------------------------
# Test suite case definitions
# ---------------------------------------------------------------------------
# front_delta / rear_delta are offsets from _REF_Z.
# None means target_*_wheel_axis_rh = None (keep original).
_SUITE_CASES: list[dict] = [
    # A — identity (no transform)
    dict(name="identity",             enabled=False, front_d=None,  rear_d=None,  yaw=0.0, yaw_mode="wheel_center", cx=0.0, adj_sep=False, use_orig=False, ref_mode="user_input"),
    # B — heave only (parallel raise)
    dict(name="heave",                enabled=True,  front_d=+0.02, rear_d=+0.02, yaw=0.0, yaw_mode="wheel_center", cx=0.0, adj_sep=False, use_orig=False, ref_mode="user_input"),
    # C — pitch only (front up, rear down — same midpoint)
    dict(name="pitch",                enabled=True,  front_d=+0.02, rear_d=-0.02, yaw=0.0, yaw_mode="wheel_center", cx=0.0, adj_sep=False, use_orig=False, ref_mode="user_input"),
    # D — heave + pitch combined
    dict(name="heave_pitch",          enabled=True,  front_d=+0.03, rear_d=-0.01, yaw=0.0, yaw_mode="wheel_center", cx=0.0, adj_sep=False, use_orig=False, ref_mode="user_input"),
    # E — yaw only
    dict(name="yaw_only",             enabled=False, front_d=None,  rear_d=None,  yaw=5.0, yaw_mode="wheel_center", cx=0.0, adj_sep=False, use_orig=False, ref_mode="user_input"),
    # F — yaw + heave
    dict(name="yaw_heave",            enabled=True,  front_d=+0.02, rear_d=+0.02, yaw=5.0, yaw_mode="wheel_center", cx=0.0, adj_sep=False, use_orig=False, ref_mode="user_input"),
    # G — yaw + pitch + user-defined yaw center
    dict(name="yaw_pitch_custcenter", enabled=True,  front_d=+0.02, rear_d=-0.02, yaw=5.0, yaw_mode="user_input",  cx=0.5, adj_sep=False, use_orig=False, ref_mode="user_input"),
    # H — full 3-axis (yaw + heave + pitch)
    dict(name="full_3axis",           enabled=True,  front_d=+0.02, rear_d=-0.01, yaw=5.0, yaw_mode="wheel_center", cx=0.0, adj_sep=False, use_orig=False, ref_mode="user_input"),
    # I — separate body/wheel, wheel held at original Z
    # skip_rh_check=True: wheel stays at original Z by design → verification error vs. body target is non-zero intentionally
    dict(name="sep_orig_wheel",       enabled=True,  front_d=+0.02, rear_d=-0.01, yaw=5.0, yaw_mode="wheel_center", cx=0.0, adj_sep=True,  use_orig=True,  ref_mode="user_input", skip_rh_check=True),
    # J — separate body/wheel, wheel at independent target
    dict(name="sep_indep_wheel",      enabled=True,  front_d=+0.02, rear_d=-0.01, yaw=5.0, yaw_mode="wheel_center", cx=0.0, adj_sep=True,  use_orig=False, ref_mode="user_input"),
    # K — user_input reference_mode with heave+pitch
    dict(name="userinput_ref",        enabled=True,  front_d=+0.02, rear_d=-0.01, yaw=0.0, yaw_mode="wheel_center", cx=0.0, adj_sep=False, use_orig=False, ref_mode="user_input"),
    # L — rear-only target (asymmetric: front=None)
    dict(name="rear_only",            enabled=True,  front_d=None,  rear_d=+0.02, yaw=0.0, yaw_mode="wheel_center", cx=0.0, adj_sep=False, use_orig=False, ref_mode="user_input"),
]


# ---------------------------------------------------------------------------
# Suite runner helpers
# ---------------------------------------------------------------------------

def run_test_case(case: dict) -> dict:
    """Run a single suite test case. Returns result dict with pass/fail and error values."""
    from app.services.ride_height_service import compute_transform
    from app.schemas.configuration import RideHeightConditionConfig, YawConditionConfig
    from app.schemas.template_settings import RideHeightTemplateConfig

    ref_z = _REF_Z
    front_target = (ref_z + case["front_d"]) if case["front_d"] is not None else None
    rear_target  = (ref_z + case["rear_d"])  if case["rear_d"]  is not None else None

    rh_cfg = RideHeightConditionConfig(
        enabled=case["enabled"],
        target_front_wheel_axis_rh=front_target,
        target_rear_wheel_axis_rh=rear_target,
    )
    rh_template_cfg = RideHeightTemplateConfig(
        reference_mode=case["ref_mode"],
        reference_z_front=ref_z,
        reference_z_rear=ref_z,
        adjust_body_wheel_separately=case["adj_sep"],
        use_original_wheel_position=case["use_orig"],
    )
    yaw_cfg = YawConditionConfig(
        center_mode=case["yaw_mode"],
        center_x=case["cx"],
        center_y=0.0,
    )

    try:
        snapshot = compute_transform(
            _DUMMY_ANALYSIS, rh_cfg, case["yaw"], yaw_cfg, rh_template_cfg=rh_template_cfg
        )
    except Exception as e:
        return {"name": case["name"], "passed": False, "front_err_mm": None, "rear_err_mm": None, "error": str(e)}

    vr = snapshot.get("verification", {})
    front_err_m = vr.get("front_error_m", 0.0)
    rear_err_m  = vr.get("rear_error_m",  0.0)
    front_ok = abs(front_err_m) < 0.001
    rear_ok  = abs(rear_err_m)  < 0.001

    # For yaw-only / identity cases: rh disabled + both targets None → no RH error to check
    if not case["enabled"] and front_target is None and rear_target is None:
        front_ok = rear_ok = True
        front_err_m = rear_err_m = 0.0

    # When only one target is set, ignore the None side
    if front_target is None:
        front_ok = True
    if rear_target is None:
        rear_ok = True

    # skip_rh_check: wheel stays at original Z by design (use_original_wheel_position=True)
    if case.get("skip_rh_check"):
        front_ok = rear_ok = True
        front_err_m = rear_err_m = float("nan")

    # Pattern I/J: verify wheel_transforms dict is produced
    extra_ok = True
    extra_note = ""
    if case["adj_sep"] and case["enabled"]:
        if not snapshot.get("wheel_transforms"):
            extra_ok = False
            extra_note = " (wheel_transforms missing)"

    passed = front_ok and rear_ok and extra_ok
    return {
        "name": case["name"],
        "passed": passed,
        "front_err_mm": front_err_m * 1000,
        "rear_err_mm":  rear_err_m  * 1000,
        "note": extra_note,
        "error": None,
    }


def run_suite() -> None:
    """Run all 12 posture-change pattern test cases and print a summary table."""
    print("\n🧪 Test Suite: ride height posture-change patterns (no STL required)")
    print("=" * 72)
    print(f"  {'#':<3}  {'Name':<26}  {'Front err':>10}  {'Rear err':>10}  Status")
    print("  " + "─" * 68)

    results = []
    for i, case in enumerate(_SUITE_CASES, 1):
        result = run_test_case(case)
        results.append(result)

        if result["error"]:
            status = "❌ EXCEPTION"
            front_str = rear_str = "       N/A"
        else:
            status = "✅" if result["passed"] else f"❌{result.get('note', '')}"
            import math
            def _fmt(v: float | None) -> str:
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    return "    skipped"
                return f"{v:>+9.3f}mm"
            front_str = _fmt(result["front_err_mm"])
            rear_str  = _fmt(result["rear_err_mm"])

        print(f"  {i:<3}  {result['name']:<26}  {front_str}  {rear_str}  {status}")
        if result["error"]:
            print(f"       Exception: {result['error']}")

    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    print("  " + "─" * 68)
    print(f"\n  {passed_count}/{total} passed")

    if passed_count < total:
        print("\n❌ Suite FAILED — check ride_height_service.py")
        raise SystemExit(1)
    else:
        print("\n✅ Suite PASSED — all patterns verified")


# ---------------------------------------------------------------------------
# Unit test (single case)
# ---------------------------------------------------------------------------

def run_unit_test() -> None:
    """Pure numeric test: ref front/rear=0.4 m → target front=0.3 m, rear=0.35 m.

    Uses reference_mode='user_input' to bypass STL parsing and name matching.
    No STL file required.
    """
    from app.services.ride_height_service import compute_transform
    from app.schemas.configuration import RideHeightConditionConfig, YawConditionConfig
    from app.schemas.template_settings import RideHeightTemplateConfig

    REF_FRONT = 0.4
    REF_REAR  = 0.4
    TGT_FRONT = 0.3
    TGT_REAR  = 0.35

    print("\n🧪 Unit test: ride height transform (no STL required)")
    print("=" * 70)
    print(f"  Reference  front={REF_FRONT:.3f} m  rear={REF_REAR:.3f} m")
    print(f"  Target     front={TGT_FRONT:.3f} m  rear={TGT_REAR:.3f} m")
    print()

    # Minimal dummy analysis_result — ground_z=0, wheelbase-like X extents
    dummy_analysis: dict = {
        "vehicle_bbox": {
            "x_min": -2.5, "x_max": 2.5,
            "y_min": -1.0, "y_max": 1.0,
            "z_min": 0.0,  "z_max": 1.5,
        },
        "vehicle_dimensions": {"length": 5.0, "width": 2.0, "height": 1.5},
        "part_info": {},
    }

    rh_cfg = RideHeightConditionConfig(
        enabled=True,
        target_front_wheel_axis_rh=TGT_FRONT,
        target_rear_wheel_axis_rh=TGT_REAR,
    )
    rh_template_cfg = RideHeightTemplateConfig(
        reference_mode="user_input",
        reference_z_front=REF_FRONT,
        reference_z_rear=REF_REAR,
        adjust_body_wheel_separately=False,
        use_original_wheel_position=False,
    )
    yaw_cfg = YawConditionConfig(center_mode="wheel_center", center_x=0.0, center_y=0.0)

    snapshot = compute_transform(dummy_analysis, rh_cfg, 0.0, yaw_cfg, rh_template_cfg=rh_template_cfg)

    vr = snapshot.get("verification", {})
    tg = snapshot.get("targets", {})
    tr = snapshot.get("transform", {})
    lm = snapshot.get("landmarks", {})

    print(f"  Pitch angle (deg)  : {tr.get('pitch_angle_deg', 0):.6f}")
    pivot = tr.get("rotation_pivot", [0, 0, 0])
    print(f"  Rotation pivot     : ({pivot[0]:.4f}, {pivot[1]:.4f}, {pivot[2]:.4f})")
    tz = tr.get("translation", [0, 0, 0])
    print(f"  Z translation      : {tz[2]:.6f} m")

    print("\n  Landmarks:")
    for key, val in lm.items():
        if isinstance(val, dict) and "before" in val and "after" in val:
            b, a = val["before"], val["after"]
            if isinstance(b, list):
                print(f"    {key:<28}  z: {b[2]:.4f} → {a[2]:.4f}  (Δ={a[2]-b[2]:+.4f} m)")
            else:
                print(f"    {key:<28}  {b:.4f} → {a:.4f}  (Δ={a-b:+.4f} m)")

    front_actual = vr.get("front_wheel_z_actual", 0.0)
    rear_actual  = vr.get("rear_wheel_z_actual",  0.0)
    front_err    = vr.get("front_error_m", 0.0)
    rear_err     = vr.get("rear_error_m",  0.0)
    front_ok     = abs(front_err) < 0.001
    rear_ok      = abs(rear_err)  < 0.001

    print("\n  Verification:")
    print(f"    Front  ref={REF_FRONT:.3f} m  target={TGT_FRONT:.3f} m  "
          f"actual={front_actual:.4f} m  error={front_err*1000:+.3f} mm  {'✅' if front_ok else '⚠️'}")
    print(f"    Rear   ref={REF_REAR:.3f} m  target={TGT_REAR:.3f} m  "
          f"actual={rear_actual:.4f} m  error={rear_err*1000:+.3f} mm  {'✅' if rear_ok else '⚠️'}")

    overall_ok = front_ok and rear_ok
    print("\n" + ("✅ Unit test PASSED" if overall_ok else "❌ Unit test FAILED — check ride_height_service.py"))
    if not overall_ok:
        raise SystemExit(1)


def main() -> None:
    if "--suite" in sys.argv:
        run_suite()
        return
    if "--unit" in sys.argv:
        run_unit_test()
        return

    from app.services.compute_engine import analyze_stl
    from app.services.ride_height_service import compute_transform, transform_stl
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
        reference_parts=["Wheel_"],  # parts whose name starts with "Wheel_" are used as wheel axis reference
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
    ground_z = vbbox["z_min"]
    front_actual_z  = vr.get('front_wheel_z_actual', 0)
    rear_actual_z   = vr.get('rear_wheel_z_actual',  0)
    front_actual_rh = front_actual_z - ground_z
    rear_actual_rh  = rear_actual_z  - ground_z
    print(f"  Front  target={tg.get('front_wheel_axis_rh', 0):.4f} m (RH)  "
          f"actual_rh={front_actual_rh:.4f} m  actual_z={front_actual_z:.4f} m  "
          f"error={front_err*1000:+.3f} mm  {'✅' if front_ok else '⚠️'}")
    print(f"  Rear   target={tg.get('rear_wheel_axis_rh',  0):.4f} m (RH)  "
          f"actual_rh={rear_actual_rh:.4f} m  actual_z={rear_actual_z:.4f} m  "
          f"error={rear_err*1000:+.3f} mm  {'✅' if rear_ok else '⚠️'}")
    print(f"  ground_z (vehicle_bbox_z_min before transform) = {ground_z:.4f} m")

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

    # ── Write transformed STL ─────────────────────────────────────────────────
    stl_out_path = BACKEND_DIR / f"{stl_path.stem}_transformed.stl"
    print(f"\n✍️  Writing transformed STL...")
    try:
        transform_stl(
            source_path=stl_path,
            out_path=stl_out_path,
            body_transform=snapshot["transform"],
            wheel_part_transforms=snapshot.get("wheel_transforms"),
            wheel_patterns=None,
        )
        print(f"💾 Transformed STL saved to: {stl_out_path.name}")
    except Exception as e:
        print(f"❌ transform_stl() error: {e}")
        raise


if __name__ == "__main__":
    main()
