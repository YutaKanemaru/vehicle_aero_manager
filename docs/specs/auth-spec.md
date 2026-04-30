# Auth & User Management

## Role Hierarchy

| Role | Level | Capabilities |
|---|---|---|
| `superadmin` | Highest | All actions + role assignment; created via `create_superadmin.py` |
| `admin` | Elevated | View user list, delete non-superadmin users |
| `engineer` | Default | Normal app access, self-delete only |
| `viewer` | Lowest | Read-only access |

- `is_admin` property returns `True` for both `admin` and `superadmin`
- `is_superadmin` property returns `True` only for `superadmin`

## Auth Endpoints (`app/api/v1/auth.py`)

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | None | User registration |
| `POST` | `/api/v1/auth/login` | None | Login → returns JWT |
| `GET` | `/api/v1/auth/me` | Login | Get own profile |
| `DELETE` | `/api/v1/auth/me` | Login | Delete own account |
| `GET` | `/api/v1/auth/users` | `admin+` | List all users |
| `DELETE` | `/api/v1/auth/users/{id}` | `admin+` | Delete user (cannot delete superadmin) |
| `PATCH` | `/api/v1/auth/users/{id}/role` | `superadmin` | Change user role |

## Auth Dependencies (`app/auth/deps.py`)

```python
get_current_user    # any authenticated user
get_admin_user      # admin or superadmin only (403 otherwise)
get_superadmin_user # superadmin only (403 otherwise)
```

## Schemas (`app/schemas/auth.py`)

```python
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    is_admin: bool
    is_superadmin: bool

class UpdateRoleRequest(BaseModel):
    role: Literal["superadmin", "admin", "engineer", "viewer"]
```

## Creating the First Superadmin

```bash
# Run from the backend/ directory
uv run python create_superadmin.py

# Override defaults via env vars
VAM_SUPERADMIN_EMAIL=my@email.com VAM_SUPERADMIN_PASSWORD=secret uv run python create_superadmin.py
```

Default credentials: `superadmin` / `changeme123`. The script is idempotent — skips if superadmin already exists.
