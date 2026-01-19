import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)

    password_hash = Column(String, nullable=True)

    provider = Column(String, nullable=False)       # "google"
    provider_id = Column(String, nullable=False)    # Google sub

    plan = Column(String, default="free")
    
    # Profile info
    is_company = Column(Boolean, default=False)
    country = Column(String, nullable=True)
    vat_number = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
