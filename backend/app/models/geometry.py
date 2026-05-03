import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, Text, Float, ForeignKey, Table, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# ─── Assembly ↔ Geometry 多対多リンクテーブル ────────────────────────────────
assembly_geometry_link = Table(
    "assembly_geometry",
    Base.metadata,
    Column("assembly_id", String(36), ForeignKey("geometry_assemblies.id"), primary_key=True),
    Column("geometry_id", String(36), ForeignKey("geometries.id"), primary_key=True),
)


class GeometryFolder(Base):
    """
    Geometry を整理するためのフォルダ階層。
    フォルダ自体はデータを持たず、Geometry を束ねる役割のみ。
    """
    __tablename__ = "geometry_folders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    geometries: Mapped[list["Geometry"]] = relationship(
        "Geometry", back_populates="folder"
    )


class Geometry(Base):
    """
    アップロードされた STL ファイル 1 件を表す。
    status: pending → analyzing → ready | error
    analysis_result: JSON 文字列（パーツ名・bbox・重心等）
    """
    __tablename__ = "geometries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # フォルダ（nullable — フォルダなしで管理可能）
    folder_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("geometry_folders.id"), nullable=True
    )

    # ファイル情報
    file_path: Mapped[str] = mapped_column(String(512))          # アップロード時: upload_dir 相対パス / リンク時: 絶対パス
    original_filename: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer)               # bytes
    is_linked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    # True: ファイルはリンク元に残す（削除時にstlを消さない）; False: アップロード済み（削除時にstlも消す）

    # 解析状態
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # "pending" | "analyzing" | "ready" | "error"
    analysis_result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # GLB decimation ratio used when generating the 3D preview; None = skip GLB generation
    decimation_ratio: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)

    # 所有者
    uploaded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # リレーション
    folder: Mapped["GeometryFolder | None"] = relationship(
        "GeometryFolder", back_populates="geometries"
    )
    assemblies: Mapped[list["GeometryAssembly"]] = relationship(
        "GeometryAssembly",
        secondary=assembly_geometry_link,
        back_populates="geometries",
    )


class AssemblyFolder(Base):
    """
    GeometryAssembly を整理するためのフォルダ階層。
    """
    __tablename__ = "assembly_folders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    assemblies: Mapped[list["GeometryAssembly"]] = relationship(
        "GeometryAssembly", back_populates="folder"
    )


class GeometryAssembly(Base):
    """
    複数の Geometry をまとめた車両構成。Template に紐づける。
    """
    __tablename__ = "geometry_assemblies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # フォルダ（nullable — フォルダなしで管理可能）
    folder_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("assembly_folders.id"), nullable=True
    )

    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow
    )

    folder: Mapped["AssemblyFolder | None"] = relationship(
        "AssemblyFolder", back_populates="assemblies"
    )
    geometries: Mapped[list[Geometry]] = relationship(
        "Geometry",
        secondary=assembly_geometry_link,
        back_populates="assemblies",
    )
