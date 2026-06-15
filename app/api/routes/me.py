from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user
from app.api.dependencies.services import get_user_service
from app.domain.models.user import User
from app.domain.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/me", tags=["Me"])

@router.get("", response_model=UserResponse)
def read_me(
    user: User = Depends(get_current_user), 
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_me(user)

@router.put("", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return user_service.update_me(user, data)

@router.get("/usage")
def get_usage(
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_usage(user)

@router.get("/dashboard")
def dashboard(
    user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_dashboard(user)

