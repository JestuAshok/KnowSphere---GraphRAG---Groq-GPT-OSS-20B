import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DataSourceORM(Base):
    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    # "sharepoint" | "confluence" | "google_drive" | "postgres" | "neo4j" | "custom_api" | "file_upload"
    status: Mapped[str] = mapped_column(String, default="not_connected")
    # "connected" | "not_connected" | "error"
    config_json: Mapped[str] = mapped_column(Text, nullable=True)  # JSON config (sanitized, no plain passwords)
    last_sync: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
