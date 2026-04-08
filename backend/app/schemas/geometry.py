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
    original_filename: str
    file_size: int
    status: str
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


# ─── GeometryAssembly ────────────────────────────────────────────────────────

class AssemblyCreate(BaseModel):
    name: str
    description: str | None = None
    template_id: str | None = None


class AssemblyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    template_id: str | None = None


class AssemblyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    template_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    geometries: list[GeometryResponse] = []
