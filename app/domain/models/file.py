import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class File(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)

    type = Column(String, nullable=False)  # epud
    path = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=True)

    checksum = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
