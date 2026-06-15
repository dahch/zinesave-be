from fastapi import APIRouter, Depends

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.services import get_intention_service
from app.domain.models.user import User
from app.domain.schemas.intention import IntentionCreate, IntentionResponse
from app.services.intention_service import IntentionService

router = APIRouter(prefix="/intentions", tags=["Intentions"])

@router.post("", response_model=IntentionResponse)
def capture_intention(
    data: IntentionCreate,
    user: User = Depends(get_current_user),
    intention_service: IntentionService = Depends(get_intention_service)
):
    return intention_service.capture_intention(user, data)
