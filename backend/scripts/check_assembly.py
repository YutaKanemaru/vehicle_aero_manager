"""Check assembly and geometry analysis_result for a given case."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text

conn = engine.connect()

# List tables
rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
print("Tables:", [r[0] for r in rows])

# Find assembly link table
link_tables = [r[0] for r in rows if "assembly" in r[0] and "link" in r[0]]
print("Link tables:", link_tables)

case_id = "985f7041-8d01-4ca4-bbd0-ab3499300617"
case = conn.execute(text("SELECT assembly_id FROM cases WHERE id=:cid"), {"cid": case_id}).fetchone()
if not case:
    print("Case not found")
    conn.close()
    sys.exit(1)

asm_id = case[0]
print(f"\nAssembly ID: {asm_id}")

# Check columns of assembly_geometry
cols = conn.execute(text("PRAGMA table_info(assembly_geometry)")).fetchall()
print("assembly_geometry columns:", [(r[1]) for r in cols])

links = conn.execute(text("SELECT geometry_id FROM assembly_geometry WHERE assembly_id=:aid"), {"aid": asm_id}).fetchall()
print(f"Geometry IDs: {[r[0] for r in links]}")

for (gid,) in links:
    g = conn.execute(text("SELECT name, status, analysis_result FROM geometries WHERE id=:gid"), {"gid": gid}).fetchone()
    name, status, ar = g
    print(f"\n  Geometry: {name}  status={status}")
    if ar:
        data = json.loads(ar)
        vbbox = data.get("vehicle_bbox", {})
        print(f"  vehicle_bbox keys: {list(vbbox.keys())}")
        print(f"  vehicle_bbox: {vbbox}")
        print(f"  parts count: {len(data.get('parts', []))}")
    else:
        print("  analysis_result: NULL")

conn.close()
