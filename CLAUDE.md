# Vehicle Aero Manager (VAM) — Claude Code Instructions

## Project Overview

VAM is a web browser-based application for automotive engineers to manage vehicle external aerodynamics (Aero) and greenhouse noise (GHN) CFD simulation setup and post-processing.

**Target solver**: Ultrafluid (commercial LBM CFD solver, XML-driven)  
**Team**: 1-person dev, 20–30 engineer users  
**Goals**: Consistency · Efficiency · Collaboration

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 / TypeScript / Vite 8 |
| UI | Mantine v8 (use exclusively) |
| Server state | TanStack Query v5 |
| Client state | Zustand v5 (`src/stores/`) |
| API typing | openapi-typescript v7 (auto-generated) |
| Backend | Python 3.12 / FastAPI |
| Validation | Pydantic v2 (`model_config`, not `class Config`) |
| ORM | SQLAlchemy 2.0 (`mapped_column` style) |
| DB | SQLite (MVP) |
| Package manager | uv (never use pip) |
| Deploy | Docker Compose |

---

## Repository Structure

```
backend/
  app/
    main.py          # FastAPI entry point — setup only, no business logic
    config.py        # Pydantic Settings (VAM_ env prefix)
    database.py      # SQLAlchemy engine, SessionLocal, Base, get_db
    api/v1/          # Route handlers only — no business logic
    models/          # SQLAlchemy ORM models
    schemas/         # Pydantic request/response schemas
    services/        # Business logic (all DB ops belong here)
    storage/         # StorageBackend abstraction
    ultrafluid/      # XML schema, parser, serializer
  alembic/           # DB migrations — never use create_all()
  scripts/           # Test/debug scripts (test_*.py)
frontend/
  src/
    api/             # Generated schema.d.ts + typed wrappers
    components/      # UI components
    hooks/           # Custom React hooks
    stores/          # Zustand stores
docs/specs/          # Feature specifications (reference below)
```

---

## Prohibited Patterns

1. No Celery/Redis/PostgreSQL/MinIO/Keycloak until scale trigger
2. No business logic in API routers — use `services/`
3. No manual API type definitions — use generated `schema.d.ts`
4. No `Base.metadata.create_all()` — use Alembic
5. No `pip install` — use `uv add`
6. No `class Config` in Pydantic — use `model_config = ConfigDict(...)`
7. No Japanese/non-English text in UI
8. No hardcoded numeric defaults in UI components — use `SIM_TYPE_PRESETS` → `templateDefaults.ts` → `FORM_DEFAULTS`

---

## Docs/Specs Map

| Spec | Path |
|---|---|
| Auth | `docs/specs/auth-spec.md` |
| Ultrafluid XML | `docs/specs/ultrafluid-xml-schema.md` |
| Templates | `docs/specs/template-spec.md` |
| Geometry & Assembly | `docs/specs/geometry-spec.md` |
| Case / Run | `docs/specs/case-run-spec.md` |
| 3D Viewer | `docs/specs/viewer-3d-spec.md` |
| Roadmap | `docs/specs/roadmap.md` |

---

## Git Commit Skill

To commit and push recent implementation changes with conventional commit messages, run:

```
最近の実装内容を Conventional Commits 形式で論理的なまとまりに分割してコミットし、push してください。
手順:
1. git status + git diff --stat で変更内容を把握
2. feat/fix/refactor/docs/chore/test に分類
3. まとまりごとに git add <files> → git commit -m "<type>(<scope>): <message>" を実行
4. git push
5. git log --oneline -5 で確認
ルール: 1コミット=1論理変更 / git add . 禁止 / メッセージは英語 / コードは変更しない
```

Or use the VS Code prompt file: `.github/prompts/git-commit.prompt.md`

---

## Update Docs Skill

To update docs/specs and instructions after implementation changes, run:

```
最近の実装内容をもとに、docs/specs と .github/instructions/ を最新の状態にアップデートしてください。
手順:
1. git diff HEAD~1 --name-only で変更ファイルを確認
2. 影響する spec/instruction のみ更新（コードは変更しない）
3. .github/copilot-instructions.md の Implementation Status テーブルも更新
```

Or use the VS Code prompt file: `.github/prompts/update-docs.prompt.md`

---

## Key Implementation Notes

- `transform_run()` calls `db.commit()` internally — DB changes always persisted
- `verification["front_wheel_z_actual"]` = absolute Z (not ride height); RH = `actual_z − vehicle_bbox_z_min`
- Transform-created geometries: `is_linked=False` → hidden from Geometry list UI (intentional)
- `reference_mode="user_input"` bypasses STL parsing (used in unit tests)

---

## Development Commands

```bash
# Start full stack
docker compose up --build

# Backend (from backend/)
uv run uvicorn app.main:app --reload

# Frontend (from frontend/)
npm run dev

# Regenerate API types + defaults
npm run generate-api   # (runs openapi-typescript + extract-defaults.mjs)

# Test scripts
uv run python scripts/test_ride_height.py --unit
uv run python scripts/test_transform_run.py <run_id>
```
