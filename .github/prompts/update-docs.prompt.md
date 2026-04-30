---
mode: "agent"
description: "Update docs/specs and .github/instructions based on recent implementation changes"
---

最近の実装内容をもとに、以下のドキュメントを最新の状態にアップデートしてください。

## 対象ファイル

### Specs (`docs/specs/`)
| File | Covers |
|---|---|
| `docs/specs/geometry-spec.md` | Geometry upload, STL analysis, decimation, compute engine, background jobs, ride height service |
| `docs/specs/case-run-spec.md` | Case/Run CRUD, ConditionMap, XML generation, ride height transform (`transform_run`) |
| `docs/specs/template-spec.md` | Template CRUD, versioning, JSON schema, `TemplateSettingsForm`, `SIM_TYPE_PRESETS` |
| `docs/specs/viewer-3d-spec.md` | GLB pipeline, `viewer_service`, `SceneCanvas`, `OverlayObjects`, Template Builder |
| `docs/specs/auth-spec.md` | JWT auth, roles, endpoints, FastAPI deps |
| `docs/specs/ultrafluid-xml-schema.md` | Ultrafluid XML schema, Pydantic models, parser/serializer |
| `docs/specs/roadmap.md` | Phase status, future work |

### Instructions (`.github/instructions/`)
| File | Covers |
|---|---|
| `.github/instructions/backend.instructions.md` | SQLAlchemy, Pydantic, Router/Service rules, Alembic, Auth conventions |
| `.github/instructions/frontend.instructions.md` | API client, State (Zustand/TanStack Query), Mantine, component patterns |

### Core instructions
| File | Covers |
|---|---|
| `.github/copilot-instructions.md` | Project overview, tech stack, implementation status table, repo structure |

---

## 手順

1. **変更内容の把握**
   ```
   git diff HEAD~1 --name-only
   git log --oneline -10
   ```
   変更されたファイルをリストアップし、どの spec/instruction に影響するか判断する。

2. **影響範囲の特定**
   - `backend/app/services/` の変更 → 対応する `docs/specs/*.md` を更新
   - `backend/app/models/` または `schemas/` の変更 → spec の Data Model セクションを更新
   - `backend/app/api/` の変更 → spec の Endpoints セクションを更新
   - `frontend/src/components/` の変更 → spec の UI/Component セクションを更新
   - コーディングパターンの変更 → `.github/instructions/` を更新
   - フェーズ完了・新機能追加 → `copilot-instructions.md` のステータステーブルを更新

3. **更新ルール**
   - コードは一切変更しない — ドキュメントのみ更新する
   - 既存のセクション構成・フォーマット・見出しレベルを維持する
   - 実装されていない内容を spec に追加しない
   - 削除されたコードに対応する記述は spec からも削除する
   - テストスクリプト (`backend/scripts/test_*.py`) の変更は対応する spec の "Test Scripts" セクションに反映する

4. **`copilot-instructions.md` の Implementation Status テーブル**
   - ステップが完了したら `🔲 Planned` → `✅ Complete` に更新する
   - 新しいステップが追加された場合はテーブルに行を追加する

---

## 完了基準

- [ ] 変更されたファイルに対応するすべての spec/instruction が更新されている
- [ ] 存在しない機能が spec に記載されていない
- [ ] `copilot-instructions.md` の Implementation Status が最新である
- [ ] コードファイルは一切変更されていない
