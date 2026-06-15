from typing import Dict, Any
from app.domain.models.user import User
from app.domain.models.intention import PurchaseIntention
from app.domain.repositories.intention_repository import IntentionRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.schemas.intention import IntentionCreate

class IntentionService:
    def __init__(self, intention_repo: IntentionRepository, user_repo: UserRepository):
        self.intention_repo = intention_repo
        self.user_repo = user_repo

    def capture_intention(self, user: User, data: IntentionCreate) -> Dict[str, Any]:
        existing = self.intention_repo.get_by_user_and_tier(user.id, data.tier_requested)
        if existing:
            return {
                **existing.__dict__,
                "reward_granted": False
            }

        new_intention = PurchaseIntention(
            user_id=user.id,
            tier_requested=data.tier_requested
        )
        new_intention = self.intention_repo.add(new_intention)

        # Reward 5 credits
        user.credits += 5
        self.user_repo.update(user)

        return {
            **new_intention.__dict__,
            "reward_granted": True
        }
