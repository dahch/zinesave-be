import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func

from app.core.database import Base


class PurchaseIntention(Base):
    __tablename__ = "purchase_intentions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    tier_requested = Column(String, nullable=False)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now())
