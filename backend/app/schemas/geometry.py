from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, field_validator
import json


# ─── Analysis result inner types ────────────────────────────────────────────

class PartInfo(BaseModel):
    centroid: list[float]           # [x, y, z]
    bbox: dict[str, float]          # x_min/x_max/y_min/y_max/z_min/z_max
    vertex_count: int
    face_count: int


class AnalysisResult(BaseModel):
    parts: list[str]
    vehicle_bbox: dict[str, float]
    vehicle_dimensions: dict[str, float]  # length / width / height
    part_info: dict[str, PartInfo]


# ─── Geometry ────────────────────────────────────────────────────────────────

class GeometryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    folder_id: str | None
    original_filename: str
    file_size: int
    is_linked: bool = False
    status: str
    decimation_ratio: float = 0.05
    analysis_result: AnalysisResult | None = None
    error_message: str | None
    uploaded_by: str
    created_at: datetime
    updated_at: datetime

    @field_validator("analysis_result", mode="before")
    @classmethod
    def parse_analysis(cls, v: Any) -> Any:
        if isinstance(v, str):
            return AnalysisResult.model_validate(json.loads(v))
        return v


class GeometryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    # folder_id: None は「フォルダから外す」を意味する。model_fields_set で判定。
    folder_id: str | None = None


class GeometryLinkRequest(BaseModel):
    """既存ファイルをコピーせずパスのみ登録する（Link only モード）。"""
    name: str
    description: str | None = None
    file_path: str          # サーバー上の絶対パス（バックエンドから読める必要あり）
    folder_id: str | None = None
    decimation_ratio: float = 0.05  # GLB変換時の保持率 (1.0 以上 = 変換しない)


# ─── GeometryFolder ─────────────────────────────────────────────────────

class GeometryFolderCreate(BaseModel):
    name: str
    description: str | None = None


class GeometryFolderUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GeometryFolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


# ─── GeometryAssembly ────────────────────────────────────────────────────────

class AssemblyCreate(BaseModel):
    name: str
    description: str | None = None
    folder_id: str | None = None


class AssemblyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    folder_id: str | None = None


class AssemblyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    folder_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    geometries: list[GeometryResponse] = []


# ─── AssemblyFolder ─────────────────────────────────────────────────────────────────

class AssemblyFolderCreate(BaseModel):
    name: str
    description: str | None = None


class AssemblyFolderUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class AssemblyFolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
