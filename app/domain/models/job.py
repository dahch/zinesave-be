import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    source_url = Column(String, nullable=False)
    base_url = Column(String, nullable=False)

    status = Column(String, default="queued")
    current_step = Column(String, nullable=True)
    progress = Column(Integer, default=0)

    error_code = Column(String, nullable=True)
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, default=func.now())
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # Dictionary { "google_drive": {id, url}, "dropbox": ... }
    external_uploads = Column(JSON, default={})