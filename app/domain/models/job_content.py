import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class JobContent(Base):
    __tablename__ = "job_contents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    
    step = Column(String, nullable=False) # extracted | normalized
    content_type = Column(String, nullable=False) # html | text
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, nullable=False, default=func.now())