import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DocumentORM(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String, nullable=False)
    original_name: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String, nullable=True)
    # Full extracted text
    content: Mapped[str] = mapped_column(Text, nullable=True)
    # JSON array of extracted entity annotations
    entities_json: Mapped[str] = mapped_column(Text, nullable=True)
    # Neo4j node ID of the Document node
    neo4j_node_id: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|processing|done|error
    uploaded_by: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
