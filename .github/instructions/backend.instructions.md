---
applyTo: "backend/**"
---

# Backend Coding Conventions

## SQLAlchemy Models (`app/models/`)

Use SQLAlchemy 2.0 mapped style consistently:

```python
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SomeModel(Base):
    __tablename__ = "some_table"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow)
```

Rules:
- UUID primary keys as `str(36)` — do not use integer PKs
- Always use `Mapped[T]` + `mapped_column()` — never use `Column()` directly
- Do not put business logic in models
- **CRITICAL**: Always add **both** `default=datetime.utcnow` (Python-side) **and** `server_default=func.now()` (DB-side) to datetime columns. `server_default` only takes effect when Alembic generates the DDL — tables created via raw SQL or `stamp` will have `NULL` datetime values without the Python-side `default`, causing `ResponseValidationError` at runtime.

## Pydantic Schemas (`app/schemas/`)

```python
from pydantic import BaseModel, ConfigDict

class SomeRequest(BaseModel):
    name: str

class SomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
```

- Use `ConfigDict(from_attributes=True)` on all response schemas that read from ORM objects
- Use `model_config = ConfigDict(...)` — **never use `class Config`**

## API Routers (`app/api/v1/`)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.deps import get_current_user

router = APIRouter()

@router.get("/{id}", response_model=SomeResponse)
def get_something(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = some_service.get(db, id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result
```

Rules:
- Routers call services — **never write DB queries directly in routers**
- Use `HTTPException` for all error responses
- Always declare `response_model`
- **Route ordering**: specific paths (e.g. `/folders/`, `/validate-settings`) MUST be declared before parameterized paths (e.g. `/{id}`) to avoid FastAPI routing ambiguity

## Services (`app/services/`)

- One file per domain (e.g., `template_service.py`, `geometry_service.py`)
- Functions take `db: Session` as first argument
- Return ORM model instances or raise `HTTPException`
- Permission check pattern: `resource.created_by == current_user.id OR current_user.is_admin`

## Environment & Configuration

- All settings use `VAM_` prefix in env vars (defined in `app/config.py` via `pydantic-settings`)
- SQLite DB path: always use an **absolute path** derived from `__file__`:
  ```python
  _BACKEND_DIR = Path(__file__).parent.parent
  database_url: str = f"sqlite:///{_BACKEND_DIR / 'data' / 'vam.db'}"
  ```
- Add new settings to `app/config.py` `Settings` class — never hardcode values
- Package management: **always use `uv add`**, never `pip install`

## Database Migrations

- **Always use Alembic** for schema changes — never call `Base.metadata.create_all()` in app code
- Generate: `uv run alembic revision --autogenerate -m "description"`
- Apply: `uv run alembic upgrade head`
- SQLite FK workaround: use `op.batch_alter_table()` when adding FK constraints to existing tables

## Auth Dependencies (`app/auth/deps.py`)

```python
get_current_user    # any authenticated user
get_admin_user      # admin or superadmin only (403 otherwise)
get_superadmin_user # superadmin only (403 otherwise)
```

Roles: `superadmin` > `admin` > `engineer` > `viewer`
- `is_admin` → True for `admin` and `superadmin`
- `is_superadmin` → True only for `superadmin`
