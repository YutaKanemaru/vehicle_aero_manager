import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ConditionMapFolder(Base):
    """Organisational folder for grouping ConditionMaps."""
    __tablename__ = "condition_map_folders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    maps: Mapped[list["ConditionMap"]] = relationship("ConditionMap", back_populates="folder")


class CaseFolder(Base):
    """Organisational folder for grouping Cases."""
    __tablename__ = "case_folders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    cases: Mapped[list["Case"]] = relationship("Case", back_populates="folder")


class ConditionMap(Base):
    """Independent entity grouping a set of run conditions (velocity, yaw, etc.)."""
    __tablename__ = "condition_maps"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    folder_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("condition_map_folders.id"), nullable=True, index=True
    )
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    conditions: Mapped[list["Condition"]] = relationship(
        "Condition", back_populates="map", cascade="all, delete-orphan"
    )
    folder: Mapped["ConditionMapFolder | None"] = relationship("ConditionMapFolder", back_populates="maps")


class Condition(Base):
    """A single run condition: inflow velocity + yaw angle. Belongs to a ConditionMap."""
    __tablename__ = "conditions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    map_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("condition_maps.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    inflow_velocity: Mapped[float] = mapped_column(Float)
    yaw_angle: Mapped[float] = mapped_column(Float, default=0.0)
    # JSON strings for ride height and yaw config (nullable for backward compat)
    ride_height_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    yaw_config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    map: Mapped["ConditionMap"] = relationship("ConditionMap", back_populates="conditions")

    @property
    def ride_height(self) -> dict:
        import json as _json
        if self.ride_height_json:
            try:
                return _json.loads(self.ride_height_json)
            except Exception:
                pass
        return {}

    @property
    def yaw_config(self) -> dict:
        import json as _json
        if self.yaw_config_json:
            try:
                return _json.loads(self.yaw_config_json)
            except Exception:
                pass
        return {}


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    case_number: Mapped[str] = mapped_column(String(20), default="")
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_id: Mapped[str] = mapped_column(String(36), ForeignKey("templates.id"))
    assembly_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("geometry_assemblies.id")
    )
    map_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("condition_maps.id"), nullable=True
    )
    folder_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("case_folders.id"), nullable=True, index=True
    )
    parent_case_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    runs: Mapped[list["Run"]] = relationship(
        "Run", back_populates="case", cascade="all, delete-orphan"
    )
    folder: Mapped["CaseFolder | None"] = relationship("CaseFolder", back_populates="cases")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_number: Mapped[str] = mapped_column(String(20), default="")
    name: Mapped[str] = mapped_column(String(255))
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    condition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conditions.id")
    )
    xml_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    stl_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    belt_stl_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    geometry_override_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("geometries.id", ondelete="SET NULL"), nullable=True
    )  # if set, XML generation uses this geometry instead of the assembly's default
    system_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("systems.id", ondelete="SET NULL"), nullable=True
    )  # System record created during transform_run(); used for reliable cleanup
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending / generating / ready / error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduler_job_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # PBS/Slurm job ID (future)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    case: Mapped["Case"] = relationship("Case", back_populates="runs")
    condition: Mapped["Condition"] = relationship("Condition")
