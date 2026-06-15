import pytest
from app.domain.models.user import User
from app.domain.models.intention import PurchaseIntention
from app.domain.schemas.intention import IntentionCreate

def test_capture_intention_new(intention_service, intention_repo, user_repo):
    user = User(id=1, email="test@example.com", credits=10)
    data = IntentionCreate(tier_requested="premium")

    intention_repo.get_by_user_and_tier.return_value = None
    
    # We mock the return value of add so the dict construction doesn't fail
    intention_repo.add.return_value = PurchaseIntention(id=1, user_id=1, tier_requested="premium")

    result = intention_service.capture_intention(user, data)

    assert result["reward_granted"] is True
    assert result["tier_requested"] == "premium"
    assert user.credits == 15
    user_repo.update.assert_called_once_with(user)


def test_capture_intention_existing(intention_service, intention_repo, user_repo):
    user = User(id=1, email="test@example.com", credits=10)
    data = IntentionCreate(tier_requested="premium")

    existing_intention = PurchaseIntention(id=1, user_id=1, tier_requested="premium")
    intention_repo.get_by_user_and_tier.return_value = existing_intention

    result = intention_service.capture_intention(user, data)

    assert result["reward_granted"] is False
    assert result["tier_requested"] == "premium"
    assert user.credits == 10 # Credits not increased
    user_repo.update.assert_not_called()
