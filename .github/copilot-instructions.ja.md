# GitHub Copilot 指示書 — Vehicle Aero Manager (VAM)

## プロジェクト概要

VAM は、自動車エンジニアが車両外部空力（Aero）および車室内騒音（GHN）の CFD シミュレーションセットアップとポスト処理を日常的な車両開発の中で管理するための、Web ブラウザベースのアプリケーションです。

**コアゴール：**
- **一貫性**：20〜30名以上のエンジニアチーム全体でシミュレーション設定を標準化する
- **効率性**：セットアップからポスト処理までの CFD ワークフローを効率化する
- **コラボレーション**：ドメインをまたいだ非同期チームワーク（CAE・デザイン・マネジメント）を実現する

**主要機能：**
- **テンプレートセットアップ**：テンプレートで Ultrafluid 設定を適用。同じ命名規約でジオメトリを差し替え可能
- **設定チェック**：3D 可視化で Ultrafluid 設定を確認。ベース vs 新規の設定差分を表示
- **ケース管理**：シミュレーション関連の全データ（入力 STL・設定・結果・ポスト処理データ）を一元管理
- **自動化**：テンプレート設定後、セットアップからポスト処理まで自動化。ジオメトリ変更（車両サイズ・ホイール軸・多孔質方向等）に自動適応
- **ポスト処理**：詳細解析用 GUI セッション + 画像・動画自動生成の軽量ビューア
- **データ管理**：Pre（CAD/スキャン）→ Solve（XML/結果）→ Post（テーブル/画像/レポート/GSP）のドメイン横断管理

**対象ソルバー**：Ultrafluid — XML 設定ファイルで動作する商用 LBM CFD ソルバー

**開発体制**：1人チーム・Python 重視・インクリメンタルデリバリー。過度な設計はしない。完璧なアーキテクチャより動くソフトウェアを優先する。

---

## 技術スタック

### MVP（Phase 1〜2）— 現行スタック

| レイヤー | 技術 | 備考 |
|---|---|---|
| フロントエンド | React 19 / TypeScript / Vite 8 | |
| UI ライブラリ | Mantine v8 | UI は Mantine コンポーネントを使用 |
| 状態管理（サーバー） | TanStack Query v5 | API コールはすべて React Query 経由 |
| 状態管理（クライアント） | Zustand v5 | `src/stores/` のみ |
| API 型定義 | openapi-typescript v7 | FastAPI OpenAPI スキーマから自動生成 |
| バックエンド | Python 3.12 / FastAPI | |
| バリデーション | Pydantic v2 | 全モデルは `model_config` を使用（`class Config` 禁止） |
| ORM | SQLAlchemy 2.0（mapped_column スタイル） | |
| DB | SQLite（MVP）→ PostgreSQL（スケール時） | |
| ファイルストレージ | ローカル FS（MVP）→ MinIO/S3（スケール時） | StorageBackend 抽象化を使用 |
| 認証 | JWT（MVP）→ Keycloak（スケール時） | AuthBackend 抽象化を使用 |
| タスクキュー | FastAPI BackgroundTasks（MVP）→ Celery（スケール時） | |
| パッケージ管理 | uv | pip を直接使わない |
| デプロイ | Docker Compose | |

### スケールトリガー技術

**Phase 1〜2 では導入しないこと：**
- PostgreSQL、MinIO、Keycloak、Celery、Redis、Kubernetes、Helm

**実装が必要なタイミングで導入可**（Phase 制約なし）：
- Three.js / React Three Fiber — 3D 設定チェック可視化・ポスト処理ビューア用
- VTK / PyVista — サーバーサイドのジオメトリ・結果処理用

---

## 現在の実装状況

### Phase 1：MVP コア（Month 1〜4）

| Step | 内容 | 状態 |
|---|---|---|
| Step 1（W1-2） | FastAPI + React + Docker Compose + SQLite + JWT 認証 | ✅ 完了 |
| Step 2（W3-5） | Ultrafluid Pydantic スキーマ — XML ↔ Pydantic ラウンドトリップ | ✅ 完了 |
| Step 3（W6-8） | テンプレート CRUD + バージョン管理（Aero/GHN） | ✅ 完了 |
| Step 4（W9-12） | ジオメトリアップロード + STL 解析 + 計算エンジン + キネマティクス | 🔄 **現在のターゲット** |
| Step 5（W13-16） | XML 生成 + Configuration 管理 + Diff ビュー + 多孔質係数 UI | ⬜ 未着手 |

**コードを生成する際は現在の Step に集中すること。将来の Step の機能は実装しないこと。**

---

## リポジトリ構造

```
vehicle_aero_manager/
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml           # uv 管理の依存関係
│   ├── alembic/                 # DB マイグレーション — 必ず Alembic を使用、create_all() 禁止
│   └── app/
│       ├── main.py              # FastAPI エントリーポイント — アプリ設定のみ、ビジネスロジック禁止
│       ├── config.py            # Pydantic Settings — VAM_ プレフィックスの環境変数
│       ├── database.py          # SQLAlchemy engine, SessionLocal, Base, get_db
│       ├── auth/                # JWT ヘルパー（jwt.py）、FastAPI deps（deps.py）
│       ├── api/v1/              # ルートハンドラーのみ — ビジネスロジック禁止
│       ├── models/              # SQLAlchemy ORM モデルのみ
│       ├── schemas/             # Pydantic リクエスト/レスポンス スキーマのみ
│       ├── services/            # ビジネスロジック — DB 操作はここに書く（ルーターには書かない）
│       ├── storage/             # StorageBackend 抽象化
│       └── ultrafluid/          # XML スキーマ（Pydantic）、パーサー、シリアライザー — 独立モジュール
├── frontend/
│   └── src/
│       ├── api/                 # API クライアント — 生成済み schema.d.ts + 型付きラッパー
│       ├── components/          # UI コンポーネント
│       ├── hooks/               # カスタム React フック
│       ├── stores/              # Zustand ストアのみ
│       └── types/               # 共有 TypeScript 型定義
└── tests/
```

---

## バックエンド コーディング規約

### SQLAlchemy モデル（`app/models/`）

SQLAlchemy 2.0 の mapped スタイルを統一して使用すること：

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
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

ルール：
- 主キーは UUID を `str(36)` で使用 — 整数 PK は使わない
- 必ず `Mapped[T]` + `mapped_column()` を使用 — `Column()` を直接使わない
- モデルにビジネスロジックを書かない

### Pydantic スキーマ（`app/schemas/`）

```python
from pydantic import BaseModel, ConfigDict

class SomeRequest(BaseModel):
    name: str

class SomeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
```

- ORM オブジェクトから読み込む全レスポンススキーマに `ConfigDict(from_attributes=True)` を付ける
- `model_config = ConfigDict(...)` を使う — `class Config` は禁止

### API ルーター（`app/api/v1/`）

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

ルール：
- ルーターはサービスを呼ぶ — ルーターに直接 DB クエリを書かない
- エラーレスポンスは必ず `HTTPException` を使う
- 必ず `response_model` を宣言する

### サービス（`app/services/`）

- ドメインごとに1ファイル（例：`project_service.py`、`template_service.py`）
- 関数の第1引数は `db: Session`
- ORM モデルのインスタンスを返すか、`HTTPException` を raise する

### 環境・設定

- 全設定は `VAM_` プレフィックスの環境変数を使用（`app/config.py` で `pydantic-settings` 経由で定義）
- SQLite DB パス：作業ディレクトリ依存を避けるため、**`__file__` から導出した絶対パス**を使用すること：
  ```python
  # app/config.py
  _BACKEND_DIR = Path(__file__).parent.parent
  database_url: str = f"sqlite:///{_BACKEND_DIR / 'data' / 'vam.db'}"
  ```
- `app/database.py` が起動時に `data/` ディレクトリを自動作成する（Docker ボリュームに依存しない）
- アップロードディレクトリ：`/app/data/uploads`
- 結果ディレクトリ：`/app/data/results`
- 新しい設定は `app/config.py` の `Settings` クラスに追加する — 値をハードコードしない

### DB マイグレーション

- スキーマ変更には**必ず Alembic を使用**する
- アプリケーションコードに `Base.metadata.create_all()` を呼ばない（テストセットアップのみ許可）
- マイグレーション生成：`uv run alembic revision --autogenerate -m "description"`
- DB への適用：`uv run alembic upgrade head`

---

## 認証・ユーザー管理

### ロール階層

| ロール | レベル | 権限 |
|---|---|---|
| `superadmin` | 最上位 | 全操作 + ロール割り当て；`create_superadmin.py` で作成 |
| `admin` | 上位 | ユーザー一覧表示、非 superadmin ユーザーの削除 |
| `engineer` | デフォルト | 通常のアプリアクセス、自分自身の削除のみ |
| `viewer` | 最下位 | 読み取り専用アクセス |

- `is_admin` プロパティ：`admin` と `superadmin` の両方で `True` を返す
- `is_superadmin` プロパティ：`superadmin` のみ `True` を返す

### 認証エンドポイント（`app/api/v1/auth.py`）

| メソッド | パス | 必要な権限 | 内容 |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | なし | ユーザー登録 |
| `POST` | `/api/v1/auth/login` | なし | ログイン → JWT 発行 |
| `GET` | `/api/v1/auth/me` | ログイン済み | 自分のプロフィール取得 |
| `DELETE` | `/api/v1/auth/me` | ログイン済み | 自分のアカウント削除 |
| `GET` | `/api/v1/auth/users` | `admin` 以上 | 全ユーザー一覧 |
| `DELETE` | `/api/v1/auth/users/{id}` | `admin` 以上 | ユーザー削除（superadmin は削除不可） |
| `PATCH` | `/api/v1/auth/users/{id}/role` | `superadmin` のみ | ロール変更 |

### 認証 Dependencies（`app/auth/deps.py`）

```python
get_current_user    # 認証済みユーザーなら誰でも
get_admin_user      # admin または superadmin のみ（それ以外は 403）
get_superadmin_user # superadmin のみ（それ以外は 403）
```

### スキーマ（`app/schemas/auth.py`）

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

### 初回 Superadmin の作成

```bash
# backend/ ディレクトリから実行
uv run python create_superadmin.py

# 環境変数でデフォルト値を上書き可能
VAM_SUPERADMIN_EMAIL=my@email.com VAM_SUPERADMIN_PASSWORD=secret uv run python create_superadmin.py
```

デフォルト認証情報：`superadmin` / `changeme123`。スクリプトは冪等 — superadmin が既に存在する場合はスキップされる。

---

## Ultrafluid XML スキーマ（Step 2 — 完了）

### ルート Pydantic モデル

```python
# app/ultrafluid/schema.py
class UfxSolverDeck(BaseModel):
    version: Version
    simulation: Simulation          # general, material, wall_modeling
    geometry: Geometry              # source_file, baffle, domain_bbox, domain_parts
    meshing: Meshing                # general, refinement (box/offset/custom), overset (rotating)
    boundary_conditions: BoundaryConditions  # inlet, outlet, static, wall
    sources: Sources                # porous, mrf, turbulence
    output: Output                  # general, moment_reference_system, aero_coefficients,
                                    # section_cut, probe_file, partial_surface, partial_volume,
                                    # monitoring_surface
```

### 既知の XML 構造（サンプルファイルから取得）

ルート要素は `<uFX_solver_deck>`。主なサブ構造：

```
<uFX_solver_deck>
  <version>
    <gui_version>          # str 例: "2024"
    <solver_version>       # str 例: "2024"
  <simulation>
    <general>
      <num_coarsest_iterations>   # int
      <mach_factor>               # float, デフォルト 1.0
      <num_ramp_up_iterations>    # int, デフォルト 200
      <parameter_preset>          # "default" | "fan_noise"
    <material>
      <name>                      # str 例: "Air"
      <density>                   # float [kg/m³]
      <dynamic_viscosity>         # float [kg/(s·m)]
      <temperature>               # float [K]
      <specific_gas_constant>     # float [J/(kg·K)]
    <wall_modeling>
      <wall_model>                # "GLW" | "GWF" | "WangMoin" | "off", デフォルト "GLW"
      <coupling>                  # "adaptive_two-way" | "two-way" | "one-way" | "off"
      <transitional_bl_detection> # bool（GHN のみ）
  <geometry>
    <source_file>                 # str — STL/ZIP ファイル名
    <baffle_parts>                # <name> のリスト
    <domain_bounding_box>         # x_min/x_max/y_min/y_max/z_min/z_max（Computed）
    <triangle_plinth>             # bool
    <surface_mesh_optimization>
      <triangle_splitting>
        <active>                  # bool
        <max_absolute_edge_length>
        <max_relative_edge_length>
    <domain_part>
      <export_mesh>               # bool
      <domain_part_instance>[]    # name, location ("z_min" 等), bounding_range
  <meshing>
    <general>
      <coarsest_mesh_size>        # float（Computed: finest_resolution × 2^n_levels）
      <mesh_preview>              # bool
      <mesh_export>               # bool
      <refinement_level_transition_layers> # int デフォルト 8
    <refinement>
      <box><box_instance>[]       # name, refinement_level, bounding_box
      <offset><offset_instance>[] # name, normal_distance, refinement_level, [parts]
      <custom><custom_instance>[] # name, refinement_level, parts（GHN のみ）
    <overset>
      <rotating><rotating_instance>[]  # name, rpm, center(x/y/z), axis(x/y/z), parts
                                        # Aero: 4輪（VREV_*）。GHN: 空の <overset/>
  <boundary_conditions>
    <inlet><inlet_instance>[]     # name, parts, fluid_bc_settings (type: velocity)
    <outlet><outlet_instance>[]   # name, parts, fluid_bc_settings (type: non_reflective_pressure)
    <static/>                     # 通常は空
    <wall><wall_instance>[]       # name, parts, [roughness], fluid_bc_settings
                                  # fluid_bc_settings type: static|slip|moving|rotating
  <sources>
    <porous><porous_instance>[]   # name, inertial_resistance, viscous_resistance,
                                  # porous_axis (x/y/z dir), parts
    <mrf/>                        # 通常は空
    <turbulence><turbulence_instance>[]  # name, num_eddies, length_scale,
                                          # turbulence_intensity, point, bounding_box
                                          # Aero のみ；GHN には <turbulence> なし
  <output>
    <general>                     # file_format, output_coarsening, output_variables_full/surface,
                                  # avg_start/window_size/frequency, bounding_box
    <moment_reference_system>     # Type, origin, roll/pitch/yaw axis
    <aero_coefficients>           # reference_area/length, coefficients_along_axis, passive_parts
    <section_cut><section_cut_instance>[]  # GHN 固有 — 高頻度過渡出力
    <probe_file/>                 # 通常は空
    <partial_surface><partial_surface_instance>[]
    <partial_volume><partial_volume_instance>[]
    <monitoring_surface/>
```

### Aero vs GHN の差分

| 要素 | Aero | GHN |
|---|---|---|
| `meshing.refinement.custom` | なし | あり（VREF_RL7 等） |
| `meshing.overset.rotating` | 4輪（VREV_*） | 空の `<overset/>` |
| `boundary_conditions.wall` | ベルト（移動）+ ホイール（回転） | static/slip のみ |
| `sources.turbulence` | あり（tg_ground, tg_body） | なし |
| `output.section_cut` | なし | あり（高頻度過渡） |
| `simulation.wall_modeling.transitional_bl_detection` | なし | あり |

### 既知の Enum 値（公式ドキュメント＆サンプルから）

| フィールド | 有効値 | デフォルト |
|---|---|---|
| `parameter_preset` | `"default"`, `"fan_noise"` | `"default"` |
| `wall_model` | `"GLW"`, `"GWF"`, `"WangMoin"`, `"off"` | `"GLW"` |
| `coupling` | `"adaptive_two-way"`, `"two-way"`, `"one-way"`, `"off"` | `"adaptive_two-way"` |
| `pressure_gradient` | `"favorable"`, `"adverse"`, `"full"`, `"off"` | `"adverse"` |
| `domain_part_instance.location` | `"z_min"`, `"x_min"`, `"x_max"`, `"y_min"`, `"y_max"`, `"z_max"` | — |
| `fluid_bc_settings.type` | `"velocity"`, `"non_reflective_pressure"`, `"static"`, `"slip"`, `"moving"`, `"rotating"` | — |

### フィールド分類

| 分類 | 説明 | 例 |
|---|---|---|
| `Fixed` | テンプレートで定義された値、ジオメトリごとに変わらない | `simulation.general.*`, `boundary_conditions.inlet.velocity` |
| `Computed` | STL ジオメトリ解析から導出（trimesh/NumPy） | `geometry.domain_bounding_box`, `meshing.overset.rotating` |
| `UserInput` | エンジニアが UI 経由で明示的に設定する | `sources.porous.resistance` |

### XML 生成パイプライン

```
テンプレート（JSON/Fixed）+ ジオメトリセット（STL/Computed）+ ユーザー入力
    ↓
計算エンジン（trimesh + NumPy）
    ↓
Pydantic モデル組み立て + バリデーション（UfxSolverDeck）
    ↓
lxml.etree シリアライズ
    ↓
Ultrafluid XML ファイル
```

### XML シリアライズルール

- XML 生成には必ず `lxml.etree` を使用 — `xml.etree.ElementTree` は使わない
- `app/ultrafluid/serializer.py` に `to_xml()` メソッドまたはスタンドアロンシリアライザーを実装
- `app/ultrafluid/parser.py` に `from_xml()` パーサーを実装
- ラウンドトリップテスト必須：`parse(serialize(model)) == model`
- XML タグ名は snake_case（例：`<domain_bounding_box>`, `<num_coarsest_iterations>`）
- リストのインスタンスは繰り返し子要素パターン：`<box><box_instance>...</box_instance><box_instance>...</box_instance></box>`
- bool 値は小文字文字列でシリアライズ：`"true"` / `"false"`
- float 値は指数表記を使用可能：例 `1.8194e-05`
- 空のオプションセクションはセルフクロージングタグでシリアライズ：`<mrf/>`, `<static/>`
- サンプルファイル：`docs/samples/aero/AUR_v1.2_EXT_1.99_corrected.xml`（Aero）、`docs/samples/GHN/CX1_v1.2_GHN_cut_plane_volume_corrected.xml`（GHN）

---

## Step 3: テンプレート CRUD — 実装詳細（完了）

### バックエンド

**モデル**（`app/models/template.py`）
- `Template`: `id`, `name`, `description`, `sim_type`（`"aero"`/`"ghn"`）, `created_by`, `created_at`, `updated_at`
- `TemplateVersion`: `id`, `template_id`, `version_number`, `settings`（JSON 文字列）, `is_active`, `comment`, `created_by`, `created_at`
- `Template.versions` → `cascade="all, delete-orphan"`

**スキーマ**（`app/schemas/template.py`、`app/schemas/template_settings.py`）
- `TemplateSettings`: 4セクションの Pydantic モデル（`setup_option`, `simulation_parameter`, `setup`, `target_names`）
- `TemplateCreate`, `TemplateUpdate`, `TemplateVersionCreate`, `TemplateForkRequest`（リクエスト）
- `TemplateResponse`, `TemplateVersionResponse`（レスポンス — `active_version`, `version_count` を含む）
- `@field_validator("settings", mode="before")` で DB の JSON 文字列を自動パース

**サービス**（`app/services/template_service.py`）
- `list_templates`, `get_template`, `create_template`, `update_template`, `delete_template`
- `list_versions`, `create_version`, `activate_version`
- `fork_template` — アクティブバージョンの設定をコピーして新テンプレートを作成
- 権限チェック: `template.created_by == current_user.id OR current_user.is_admin`
- `create_version` / `activate_version`: 新しいアクティブを設定する前に全バージョンを非アクティブ化

**API エンドポイント**（`app/api/v1/templates.py`）

| メソッド | パス | 内容 |
|---|---|---|
| `GET` | `/api/v1/templates/` | テンプレート一覧 |
| `POST` | `/api/v1/templates/` | 作成（v1 を同時作成） |
| `GET` | `/api/v1/templates/{id}` | アクティブバージョン付きで取得 |
| `PATCH` | `/api/v1/templates/{id}` | 名前/説明更新 |
| `DELETE` | `/api/v1/templates/{id}` | 削除（バージョンもカスケード削除） |
| `GET` | `/api/v1/templates/{id}/versions` | バージョン一覧 |
| `POST` | `/api/v1/templates/{id}/versions` | 新バージョン作成（自動でアクティブに） |
| `PATCH` | `/api/v1/templates/{id}/versions/{vid}/activate` | 指定バージョンをアクティブ化 |
| `POST` | `/api/v1/templates/{id}/fork` | Fork: アクティブバージョンをコピーして新テンプレート作成 |

**マイグレーション**: `alembic/versions/40849f49edd9_add_templates_and_template_versions.py`

### フロントエンド

**API レイヤー**（`src/api/`）
- `client.ts`: `get`, `post`, `put`, `patch`, `delete` ラッパー；204 No Content 対応；`client`（新）と `api`（後方互換エイリアス）の両方を export
- `templates.ts`: 全 9 エンドポイントをラップ；全型は `schema.d.ts` から取得（手動定義禁止）
- `auth.ts` `UserResponse` + `stores/auth.ts` `User`: 両方に `is_admin: boolean` と `is_superadmin: boolean` を含む

**コンポーネント**（`src/components/templates/`）

| ファイル | 内容 |
|---|---|
| `TemplateList.tsx` | テーブル表示。各行に Versions / Fork / Delete アイコン |
| `TemplateCreateModal.tsx` | テンプレート作成用フル設定フォーム |
| `TemplateVersionsDrawer.tsx` | 右サイド Drawer でバージョン履歴表示。New Version ボタン（オーナー/admin のみ）、各バージョンに 👁 / `</>` アイコン |
| `TemplateVersionCreateModal.tsx` | アクティブバージョンの設定を引き継いで新バージョンを作成 |
| `TemplateSettingsViewModal.tsx` | 設定値を無効化フォームで読み取り専用表示 |
| `TemplateForkModal.tsx` | 新活名・説明・コメントを入力してアクティブバージョンをコピーした新テンプレートを作成 |

**権限モデル（フロントエンド）**
- Fork ボタン: 全認証ユーザーに表示
- Delete ボタン: `user.id === template.created_by || user.is_admin` の場合のみ表示
- New Version / Activate ボタン: `user.id === template.created_by || user.is_admin` の場合のみ表示

---

## テンプレート JSON スキーマ（Step 3 参考）

concept_vam のプロトタイプ実装をベースに、テンプレートの `settings` JSON フィールドは以下の4セクション構造に従う：

```json
{
  "setup_option": {
    "simulation": {
      "temperature_degree": true,         // 温度入力が °C（K に変換される）
      "simulation_time_with_FP": false     // 固定時間ではなくフロー通過時間を使用
    },
    "meshing": {
      "triangle_splitting": true,
      "domain_bounding_box_relative": true, // bbox を車両寸法の相対値で定義
      "box_offset_relative": true,
      "box_refinement_porous": true
    },
    "boundary_condition": {
      "ground": { "moving_ground": true, "no_slip_static_ground_patch": true,
                  "ground_zmin_auto": true, "boundary_layer_suction_position_from_belt_xmin": true },
      "belt": { "opt_belt_system": true, "num_belts": 5,
                "include_wheel_belt_forces": true, "wheel_belt_location_auto": true },
      "turbulence_generator": { "activate_body_tg": true, "activate_ground_tg": true }
    }
  },
  "simulation_parameter": {
    "inflow_velocity": 38.88,             // m/s（Fixed）
    "density": 1.2041,                   // kg/m³（Fixed）
    "dynamic_viscosity": 1.8194e-5,      // kg/(s·m)（Fixed）
    "temperature": 20,                   // °C（Fixed）
    "specific_gas_constant": 287.05,     // J/(kg·K)（Fixed）
    "mach_factor": 2,                    //（Fixed）
    "num_ramp_up_iter": 200,             //（Fixed）
    "finest_resolution_size": 0.0015,    // m — 最粗メッシュサイズを決定（Fixed）
    "number_of_resolution": 7,           // coarsest = finest × 2^N（Fixed）
    "simulation_time": 2,                // 秒（Fixed）
    "simulation_time_FP": 30             // フロー通過数（Fixed、time_with_FP=true の場合）
  },
  "setup": {
    "domain_bounding_box": [-5, 15, -12, 12, 0, 20],  // 相対倍率（Fixed）
    "meshing": {
      "box_refinement": { "Box_RL1": {"level": 1, "box": [...]}, ... },
      "part_box_refinement": { ... },
      "offset_refinement": { ... },
      "custom_refinement": { ... }
    },
    "boundary_condition_input": {
      "belts": { "belt_size_wheel": {"x": 0.4, "y": 0.3}, ... },
      "boundary_layer_suction_xpos": -1.1
    }
  },
  "target_names": {
    "wheel":            ["Wheel_"],          // パーツ名マッチングパターン
    "rim":              ["_Spokes_"],
    "porous":           ["Porous_Media_"],
    "car_bounding_box": [""],
    "baffle":           ["_Baffle_"],
    "triangle_splitting": [""]
  }
}
```

**重要な原則**：`setup_option`（bool フラグ）と `simulation_parameter`（物理値）は Fixed でテンプレートに保存される。`setup` はジオメトリ相対のサイジングルールを含む。`target_names` はソルバーの概念をパーツ命名規則にマッピングする。

---

## 計算エンジンのメモ（Step 4 参考）

計算エンジンは STL ジオメトリから `Computed` フィールドを導出する。主な計算：

| 出力 | 方法 | ライブラリ |
|---|---|---|
| `domain_bounding_box` | 車両 bbox × テンプレートの相対倍率 | `trimesh` または `numpy` |
| `meshing.overset.rotating`（ホイール中心/軸） | リム頂点の PCA → 軸 = 第3主成分 | `trimesh` + `numpy` |
| `sources.porous.porous_axis` | 多孔質メディア頂点の PCA → 面法線方向 | `trimesh` + `numpy` |
| `boundary_conditions.wall`（回転） | ホイール中心/軸/rpm から導出 | 上記から導出 |

**計算エンジンの追加計算（Step 4）：**

| 出力 | 方法 |
|---|---|
| キネマティクス（ライドハイト） | ユーザー指定のライドハイト調整をジオメトリに適用 |
| 座標系変換 | キネマティクス調整後のポスト処理座標系を変換 |
| 多孔質媒体係数 | ユーザー入力の抵抗値をマッチした多孔質パーツに適用 |

**計算エンジンの実装ルール：**
- `trimesh` + `numpy` のみ使用 — `pyproject.toml` に既に含まれている
- `numpy-stl` や `scikit-learn` は使わない（concept_vam プロトタイプで使用されていたがこのスタックでは不使用）
- STL ファイルはマルチソリッド ASCII 形式の場合がある — solid 名でパースする
- ホイールグルーピング：パーツの重心と車両 COG（x, y）を比較して FR-LH / FR-RH / RR-LH / RR-RH に分類
- RPM 計算：`rpm = (inflow_velocity / wheel_circumference) × 60` — bbox からホイール半径が必要

---

## Docker・ローカル開発

### フルスタックの起動

```bash
docker compose up --build
```

- バックエンド：http://localhost:8000
- フロントエンド：http://localhost:5173
- API ドキュメント：http://localhost:8000/docs

### バックエンドのホットリロード

バックエンドソース（`backend/app/`）はコンテナにボリュームマウントされている — リビルドなしで変更が即座に反映される。

### Python パッケージのインストール

```bash
# 必ず uv を使うこと、pip は禁止
uv add <package-name>
```

---

## 禁止パターン

1. **スケールトリガーのバックエンド技術を導入しない**（Celery、Redis、PostgreSQL、MinIO、Keycloak）— スケールトリガーに達するまで禁止。
2. **API ルーターにビジネスロジックを書かない** — 全ロジックは `app/services/` に書く。
3. **`schema.d.ts` を迂回しない** — フロントエンドで手動の API 型定義を書かない。
4. **アプリケーションコードに `Base.metadata.create_all()` を使わない** — 必ず Alembic を使う。
5. **SQLite 固有の SQL を書かない**（`check_same_thread` 設定以外）— PostgreSQL への移行時に壊れる。
6. **`pip install` を使わない** — 必ず `uv add` を使う。
7. **将来の Step に飛ばない** — 実装フェーズで定義された順番で機能を実装する。
8. **Pydantic モデルに `class Config` を使わない** — `model_config = ConfigDict(...)` を使う。

---

## Phase 2+ ロードマップ

以下の機能は将来のフェーズで計画されている。コンテキストとして文書化するが、**Phase 1 では実装しないこと**。

### ケース管理

シミュレーションケースに関連する全データをアプリケーションで管理する：入力 STL、シミュレーション設定、チェック結果、ソルバー結果、ポスト処理データ。これにより：
- ケース間の比較やテーブルデータ抽出が容易になる
- ジョブスケジューラ（PBS、Slurm）との連携で計算ノードへの自動ファイル転送が可能
- 手動ファイル転送もフォールバックとしてサポート

### ポスト処理

**2つのモードを計画：**

1. **GUI ポスト処理**（Three.js / React Three Fiber）
   - 3D 結果データを GUI セッションにロードして詳細解析
   - データ粗化で複数のフルデータセットを効率的に処理
   - 堅牢な複数データセット比較
   - Ultrafluid ログファイルからのシミュレーション情報継承
   - フォトリアリスティックレンダリング（低優先）

2. **軽量ポスト処理（ビューア）**
   - ポスト処理設定（値・位置・ビュー・凡例・GSP 設定）を事前定義
   - Ultrafluid 出力から画像・動画を自動生成
   - ビュー/位置同期・オーバーレイモードによるケース間比較の画像ビューア
   - GSP データセットビューア（プローブ結果、面積加重パワースペクトル）— Excel 不要

**注記**：軽量ポスト処理ビューアのプロトタイプは既存。必要時に提供可能。

### ポスト処理テンプレート

シミュレーションテンプレートとは別に、ポスト処理設定（可視化パラメータ、断面位置、凡例範囲、ビュー角度等）を定義する。

### データ管理システム

CFD プロセス全体のドメイン横断データライフサイクル管理：
- **Pre**：構造部門からの CAD データ、デザインチームからのスキャンデータ
- **Solve**：Ultrafluid 設定ファイル、Ultrafluid 結果（.case/h3d）
- **Post**：結果テーブル、ビューア経由の画像/動画、レポート生成、GSP データ

### ジョブスケジューラ連携

HPC ジョブスケジューラ（PBS、Slurm）との統合：
- アプリケーションからソルバージョブを投入
- ローカルストレージと計算ノード間のファイル転送を自動化
- ジョブステータス追跡と結果取得
