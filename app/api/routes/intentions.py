from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db
from app.api.dependencies.auth import get_current_user
from app.domain.models.user import User
from app.domain.models.intention import PurchaseIntention
from app.domain.schemas.intention import IntentionCreate, IntentionResponse

router = APIRouter(prefix="/intentions", tags=["Intentions"])

@router.post("", response_model=IntentionResponse)
def capture_intention(
    data: IntentionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if intention already exists
    existing = (
        db.query(PurchaseIntention)
        .filter(
            PurchaseIntention.user_id == user.id,
            PurchaseIntention.tier_requested == data.tier_requested
        )
        .first()
    )

    if existing:
        return {
            **existing.__dict__,
            "reward_granted": False
        }

    # Create new intention
    new_intention = PurchaseIntention(
        user_id=user.id,
        tier_requested=data.tier_requested
    )
    db.add(new_intention)
    
    # Reward 5 credits
    user.credits += 5
    
    db.commit()
    db.refresh(new_intention)

    return {
        **new_intention.__dict__,
        "reward_granted": True
    }
