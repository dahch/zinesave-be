from app.services.plan_service import count_active_jobs
from app.core.plans import PLANS
from fastapi import APIRouter, Depends
from app.api.dependencies.auth import get_current_user
from app.domain.models.user import User
from app.domain.models.job import Job
from app.domain.models.cloud_connection import CloudConnection
from sqlalchemy.orm import Session
from app.api.dependencies.database import get_db
from app.domain.schemas.user import UserResponse, UserUpdate


router = APIRouter(prefix="/me", tags=["Me"])

@router.get("", response_model=UserResponse)
def read_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connections = (
        db.query(CloudConnection.provider)
        .filter(CloudConnection.user_id == user.id)
        .all()
    )
    providers = [c[0] for c in connections]
    
    # We convert to dict/object compatible with UserResponse
    # Since 'user' is an ORM object, we can add the property or return a dict
    return {
        **user.__dict__,
        "connected_providers": providers
    }

@router.put("", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.is_company is not None:
        user.is_company = data.is_company
    
    if data.country is not None:
        user.country = data.country
        
    if data.vat_number is not None:
        user.vat_number = data.vat_number
    
    db.commit()
    db.refresh(user)
    return user

@router.get("/usage")
def get_usage(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {
        "plan": user.plan,
        "credits": user.credits,
        "is_beta_tester": user.is_beta_tester
    }

@router.get("/dashboard")
def dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recent_jobs = (
        db.query(Job)
        .filter(Job.user_id == user.id)
        .order_by(Job.created_at.desc())
        .limit(5)
        .all()
    )
    
    connections = (
        db.query(CloudConnection.provider)
        .filter(CloudConnection.user_id == user.id)
        .all()
    )
    
    # connections is a list of tuples [('google_drive',), ('dropbox',)]
    connected_providers = [c[0] for c in connections]

    return {
        "usage": get_usage(user, db),
        "recent_jobs": recent_jobs,
        "connected_providers": connected_providers
    }

