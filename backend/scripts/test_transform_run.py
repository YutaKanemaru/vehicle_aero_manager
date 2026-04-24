"""
configuration_service.transform_run() test script.

DBに登録済みの Run に対して transform_run() を直接呼び出し、
変換スナップショットと検証結果を表示します。
BackgroundTasks はインライン実行（同期）します。

Usage:
  uv run python scripts/test_transform_run.py                  # Run一覧を表示
  uv run python scripts/test_transform_run.py <run_id>         # 指定Run を変換
  uv run python scripts/test_transform_run.py --list           # Run一覧のみ表示
  uv run python scripts/test_transform_run.py <run_id> --dry   # スナップショットのみ（DB更新なし）

Examples:
  uv run python scripts/test_transform_run.py
  uv run python scripts/test_transform_run.py abc123def456
  uv run python scripts/test_transform_run.py abc123def456 --dry
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BACKEND_DIR = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Minimal BackgroundTasks stub — runs tasks inline (synchronously)
# ---------------------------------------------------------------------------

class InlineBackgroundTasks:
    """Mimics FastAPI BackgroundTasks but runs tasks immediately and synchronously."""

    def __init__(self, run_inline: bool = True):
        self._tasks: list[tuple] = []
        self.run_inline = run_inline

    def add_task(self, func, *args, **kwargs):
        if self.run_inline:
            print(f"  [BackgroundTask] {func.__name__}() → running inline...")
            try:
                func(*args, **kwargs)
                print(f"  [BackgroundTask] {func.__name__}() ✅ done")
            except Exception as e:
                print(f"  [BackgroundTask] {func.__name__}() ❌ error: {e}")
        else:
            print(f"  [BackgroundTask] {func.__name__}() → skipped (--dry mode)")
            self._tasks.append((func, args, kwargs))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_vec(v) -> str:
    if isinstance(v, (list, tuple)) and len(v) >= 3:
        return f"({v[0]:.4f}, {v[1]:.4f}, {v[2]:.4f})"
    return str(v)


def list_runs(db) -> None:
    from sqlalchemy import select, text
    from app.models.configuration import Run, Case, Condition

    rows = db.execute(
        text("""
            SELECT r.id, r.run_number, r.name, r.status,
                   c.case_number, c.name AS case_name,
                   cond.name AS cond_name, cond.inflow_velocity, cond.yaw_angle,
                   r.geometry_override_id,
                   r.condition_id
            FROM runs r
            JOIN cases c ON c.id = r.case_id
            JOIN conditions cond ON cond.id = r.condition_id
            ORDER BY r.created_at DESC
        """)
    ).fetchall()

    if not rows:
        print("(No runs found in DB)")
        return

    print(f"\n{'Run ID':<36}  {'#':<12}  {'Status':<12}  {'Case':<20}  {'Condition':<20}  {'Vel':>6}  {'Yaw':>6}  {'Override'}")
    print("─" * 130)
    for r in rows:
        run_id, run_num, run_name, status, case_num, case_name, cond_name, vel, yaw, override_id, cond_id = r
        override_flag = "✅" if override_id else "—"
        needs = _needs_transform_from_db(db, cond_id)
        transform_flag = " [NEEDS_TRANSFORM]" if needs else ""
        print(
            f"{run_id:<36}  {(run_num or '—'):<12}  {status:<12}  "
            f"{case_name[:20]:<20}  {cond_name[:20]:<20}  "
            f"{vel:>6.1f}  {yaw:>6.2f}  {override_flag}{transform_flag}"
        )


def _needs_transform_from_db(db, condition_id: str) -> bool:
    from sqlalchemy import text
    row = db.execute(
        text("SELECT yaw_angle, ride_height_json FROM conditions WHERE id = :cid"),
        {"cid": condition_id},
    ).fetchone()
    if not row:
        return False
    yaw_angle, rh_json = row
    if yaw_angle != 0:
        return True
    if rh_json:
        try:
            rh = json.loads(rh_json)
            return bool(rh.get("enabled"))
        except Exception:
            pass
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Test configuration_service.transform_run()")
    parser.add_argument("run_id", nargs="?", help="Run ID to transform")
    parser.add_argument("--list", action="store_true", help="List runs and exit")
    parser.add_argument("--dry", action="store_true", help="Skip background tasks (no GLB generation)")
    parser.add_argument("--no-rollback", action="store_true", help="Commit DB changes (default: rollback)")
    args = parser.parse_args()

    from app.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()

    try:
        # ── List mode ────────────────────────────────────────────────────────
        if args.list or not args.run_id:
            list_runs(db)
            if not args.run_id:
                print("\nUsage: uv run python scripts/test_transform_run.py <run_id>")
            return

        run_id = args.run_id

        # ── Lookup Run ───────────────────────────────────────────────────────
        from app.models.configuration import Run
        run = db.get(Run, run_id)
        if not run:
            print(f"❌ Run not found: {run_id}")
            list_runs(db)
            sys.exit(1)

        print(f"\n{'='*70}")
        print(f"  Run     : {run.run_number}  {run.name}")
        print(f"  Status  : {run.status}")
        print(f"  Case ID : {run.case_id}")
        print(f"{'='*70}\n")

        # ── Find a superadmin / any user for auth ───────────────────────────
        user = db.query(User).filter(User.role == "superadmin").first()
        if not user:
            user = db.query(User).first()
        if not user:
            print("❌ No users found in DB. Create a superadmin first.")
            sys.exit(1)
        print(f"  Running as user: {user.username} ({user.role})\n")

        # ── BackgroundTasks stub ─────────────────────────────────────────────
        bg = InlineBackgroundTasks(run_inline=not args.dry)

        # ── Call transform_run ───────────────────────────────────────────────
        print("🔧 Calling configuration_service.transform_run()...")
        print("─" * 70)

        from app.services import configuration_service
        try:
            result = configuration_service.transform_run(
                db=db,
                case_id=run.case_id,
                run_id=run_id,
                current_user=user,
                background_tasks=bg,
            )
        except Exception as e:
            print(f"\n❌ transform_run() raised: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        # ── Print result ─────────────────────────────────────────────────────
        print(f"\n{'─'*70}")
        print("✅ transform_run() succeeded\n")
        print(f"  system_id      : {result['system_id']}")
        print(f"  geometry_id    : {result['geometry_id']}")
        print(f"  geometry_name  : {result['geometry_name']}")
        print(f"  geometry_status: {result['geometry_status']}")

        snap = result.get("transform_snapshot") or {}
        if snap:
            tr = snap.get("transform", {})
            lm = snap.get("landmarks", {})
            vr = snap.get("verification", {})
            tg = snap.get("targets", {})

            print(f"\n  Transform:")
            print(f"    Yaw angle (deg)  : {tr.get('yaw_angle_deg', 0):.4f}")
            print(f"    Pitch angle (deg): {tr.get('pitch_angle_deg', 0):.6f}")
            pivot = tr.get("rotation_pivot", [0, 0, 0])
            print(f"    Rotation pivot   : {_fmt_vec(pivot)}")
            tz = tr.get("translation", [0, 0, 0])
            print(f"    Z translation    : {tz[2] if isinstance(tz, list) else tz:.6f} m")

            print(f"\n  Landmarks (z before → after):")
            for key, val in lm.items():
                if isinstance(val, dict) and "before" in val and "after" in val:
                    b, a = val["before"], val["after"]
                    if isinstance(b, list):
                        dz = a[2] - b[2]
                        print(f"    {key:<30}  z: {b[2]:.4f} → {a[2]:.4f}  (Δ={dz:+.4f} m)")
                    else:
                        print(f"    {key:<30}  {b:.4f} → {a:.4f}  (Δ={a-b:+.4f} m)")

            print(f"\n  Verification:")
            front_err = vr.get("front_error_m", 0.0)
            rear_err  = vr.get("rear_error_m", 0.0)
            front_ok = abs(front_err) < 0.001
            rear_ok  = abs(rear_err) < 0.001
            print(
                f"    Front  target={tg.get('front_wheel_axis_rh','?'):.4f} m  "
                f"actual={vr.get('front_wheel_z_actual', 0):.4f} m  "
                f"error={front_err*1000:+.3f} mm  {'✅' if front_ok else '⚠️'}"
            )
            print(
                f"    Rear   target={tg.get('rear_wheel_axis_rh','?'):.4f} m  "
                f"actual={vr.get('rear_wheel_z_actual', 0):.4f} m  "
                f"error={rear_err*1000:+.3f} mm  {'✅' if rear_ok else '⚠️'}"
            )

            if snap.get("wheel_transforms"):
                print(f"\n  Wheel transforms (adjust_body_wheel_separately=True):")
                for corner, wt in snap["wheel_transforms"].items():
                    if wt:
                        t = wt.get("translation", [0, 0, 0])
                        print(f"    {corner}: tz={t[2]:+.4f} m")
                    else:
                        print(f"    {corner}: — (not transformed separately)")

        # ── Save snapshot ─────────────────────────────────────────────────────
        out_path = BACKEND_DIR / "test_transform_run_result.json"
        out_path.write_text(json.dumps(result, indent=2, default=str))
        print(f"\n💾 Full result saved to: {out_path.name}")

        # ── DB commit / rollback ─────────────────────────────────────────────
        if args.no_rollback:
            db.commit()
            print(f"\n🟢 DB changes COMMITTED (run.geometry_override_id = {run.geometry_override_id})")
        else:
            db.rollback()
            print(f"\n🟡 DB changes rolled back (use --no-rollback to persist)")

    finally:
        db.close()


if __name__ == "__main__":
    main()
