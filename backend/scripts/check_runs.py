"""Check current status of all runs."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    rows = conn.execute(text("SELECT id, name, status, error_message FROM runs ORDER BY status")).fetchall()
    for r in rows:
        err = r[3][:80] if r[3] else None
        print(f"  {r[1]:30s}  status={r[2]:12s}  err={err}")
