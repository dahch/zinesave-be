from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.domain.models.job import Job
from app.domain.models.file import File
from app.domain.models.user import User
from app.domain.schemas.job import JobCreate, JobResponse, JobListResponse
from app.core.plans import PLANS
from app.services.job_service import create_job
from app.api.dependencies.auth import get_current_user
from app.services.plan_service import count_active_jobs
from app.api.dependencies.database import get_db
from app.services.storage_service import storage_service

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/jobs", tags=["Jobs"])

def enforce_plan_limits(db: Session, user: User):
    plan = PLANS.get(user.plan)

    if not plan:
        raise HTTPException(403, "Invalid plan")

    limit = plan["jobs_limit"]
    if limit is None:
        return
    
    used = count_active_jobs(db, user.id)

    if used >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Jobs limit reached: {used}/{limit}")


@router.post("", response_model=JobResponse, status_code=202)
@limiter.limit("10/minute")
async def create_job_endpoint(
    payload: JobCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    enforce_plan_limits(db, user)

    # Duplicate detection: check if same URL was submitted in the last 10 minutes
    recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=10)
    existing = (
        db.query(Job)
        .filter(
            Job.user_id == user.id,
            Job.source_url == str(payload.url),
            Job.created_at > recent_cutoff,
            Job.status.in_(["queued", "processing"])
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A job for this URL is already in progress (job {existing.id})"
        )

    job = create_job(db, payload.url, user)

    # Enqueue in Redis
    # Function name must match what's defined in WorkerSettings.functions
    await request.app.state.redis.enqueue_job("execute_pipeline", job.id)

    return job

@router.get("", response_model=JobListResponse)
def get_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    offset = (page - 1) * per_page

    total = db.query(Job).filter(Job.user_id == user.id).count()

    jobs = (
        db.query(Job)
        .filter(Job.user_id == user.id)
        .order_by(Job.created_at.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    return {
        "jobs": jobs,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total > 0 else 1,
    }

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.user_id == user.id
        ).first()
    )
    if not job:
        raise HTTPException(404, "Job not found")
    return job

@router.get("/{job_id}/download")
def download_epub(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Verify job belongs to user
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(404, "Job not found")

    file = (
        db.query(File)
        .filter(File.job_id == job_id, File.type == "epub", File.is_deleted == False)
        .first()
    )

    if not file:
        raise HTTPException(404, "File not found or expired")

    presigned_url = storage_service.generate_presigned_url(file.path)

    if not presigned_url:
        raise HTTPException(500, "Failed to generate download link")
        
    return RedirectResponse(url=presigned_url)