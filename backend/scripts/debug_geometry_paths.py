import sys
sys.path.insert(0, ".")
from app.config import settings
from app.database import SessionLocal
from app.models.geometry import Geometry
from pathlib import Path

db = SessionLocal()
geos = db.query(Geometry).all()

print(f"upload_dir = {settings.upload_dir}")
print(f"upload_dir.exists() = {settings.upload_dir.exists()}")
print(f"DB records: {len(geos)}")
print()

for g in geos:
    fp = Path(g.file_path)
    is_abs = fp.is_absolute()
    resolved = fp if is_abs else settings.upload_dir / fp
    sd = resolved.parent
    print(f"id        = {g.id}")
    print(f"file_path = {g.file_path!r}")
    print(f"is_abs    = {is_abs}")
    print(f"resolved  = {resolved}")
    print(f"subdir    = {sd}")
    print(f"exists    = {sd.exists()}")
    print(f"is_root   = {sd == settings.upload_dir}")
    print()

db.close()
