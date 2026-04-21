import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class System(Base):
    """Coordinate system transform: records the STL transformation applied to produce
    a new Geometry. Stores the transform matrix, landmark points before/after, and
    verification results. Used later to re-apply the same transform to Output settings."""

    __tablename__ = "systems"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))

    source_geometry_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("geometries.id"), index=True
    )
    result_geometry_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("geometries.id"), nullable=True
    )
    condition_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("conditions.id"), nullable=True
    )

    # JSON snapshot: {transform, landmarks, targets, verification}
    transform_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now()
    )
