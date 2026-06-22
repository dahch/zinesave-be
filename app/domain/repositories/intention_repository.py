from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models.intention import PurchaseIntention
from app.domain.repositories.base import BaseRepository


class IntentionRepository(BaseRepository[PurchaseIntention]):
    def __init__(self, db: Session):
        super().__init__(PurchaseIntention, db)

    def get_by_user_and_tier(self, user_id: int, tier: str) -> Optional[PurchaseIntention]:
        return (
            self.db.query(PurchaseIntention)
            .filter(PurchaseIntention.user_id == user_id, PurchaseIntention.tier_requested == tier)
            .first()
        )
