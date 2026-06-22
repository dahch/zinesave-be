import uuid

from sqlalchemy import JSON, Column, DateTime, String
from sqlalchemy.sql import func

from app.core.database import Base


class CloudConnection(Base):
    __tablename__ = "cloud_connections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)

    provider = Column(String, nullable=False)  # google_drive, dropbox, onedrive

    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    metadata_info = Column(JSON, nullable=True)  # Extra info like email, display_name

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
