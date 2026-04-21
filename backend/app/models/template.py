import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, Boolean, Integer, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class TemplateFolder(Base):
    __tablename__ = "template_folders"

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

    templates: Mapped[list["Template"]] = relationship("Template", back_populates="folder")


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sim_type: Mapped[str] = mapped_column(String(10))  # "aero" | "ghn" | "fan_noise"
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    folder_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("template_folders.id"), nullable=True, index=True
    )
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    versions: Mapped[list["TemplateVersion"]] = relationship(
        "TemplateVersion", back_populates="template", cascade="all, delete-orphan"
    )
    folder: Mapped["TemplateFolder | None"] = relationship("TemplateFolder", back_populates="templates")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])


class TemplateVersion(Base):
    __tablename__ = "template_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("templates.id"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    settings: Mapped[str] = mapped_column(Text)  # JSON string
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    template: Mapped["Template"] = relationship("Template", back_populates="versions")
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])
