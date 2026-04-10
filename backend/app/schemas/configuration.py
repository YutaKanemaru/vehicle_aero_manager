from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# ConditionMap
# ---------------------------------------------------------------------------

class ConditionMapCreate(BaseModel):
    name: str
    description: str | None = None


class ConditionMapUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class ConditionMapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    condition_count: int = 0


# ---------------------------------------------------------------------------
# Condition
# ---------------------------------------------------------------------------

class ConditionCreate(BaseModel):
    name: str
    inflow_velocity: float
    yaw_angle: float = 0.0


class ConditionUpdate(BaseModel):
    name: str | None = None
    inflow_velocity: float | None = None
    yaw_angle: float | None = None


class ConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    map_id: str
    name: str
    inflow_velocity: float
    yaw_angle: float
    created_by: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Case
# ---------------------------------------------------------------------------

class CaseCreate(BaseModel):
    name: str
    description: str | None = None
    template_id: str
    assembly_id: str
    map_id: str | None = None


class CaseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    map_id: str | None = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str | None
    template_id: str
    assembly_id: str
    map_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    run_count: int = 0


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

class RunCreate(BaseModel):
    name: str
    condition_id: str


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    case_id: str
    condition_id: str
    xml_path: str | None
    status: Literal["pending", "generating", "ready", "error"]
    error_message: str | None
    scheduler_job_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

class DiffField(BaseModel):
    field: str
    run_a_value: str | None
    run_b_value: str | None


class DiffResult(BaseModel):
    run_a_id: str
    run_b_id: str
    changed_fields: list[DiffField]
