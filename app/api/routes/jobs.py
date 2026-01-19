from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.domain.models.job import Job
from app.domain.models.file import File
from app.domain.models.user import User
from app.domain.schemas.job import JobCreate, JobResponse
from app.core.plans import PLANS
from app.services.job_service import create_job
from app.api.dependencies.auth import get_current_user
from app.services.plan_service import count_jobs
from app.api.dependencies.database import get_db

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def enforce_plan_limits(db: Session, user: User):
    plan = PLANS[user.plan]

    if not plan:
        raise HTTPException(403, "Invalid plan")

    limit = plan["jobs_limit"]
    if limit is None:
        return
    
    used = count_jobs(db, user.id)

    if used >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Jobs limit reached: {used}/{limit}")


@router.post("", response_model=JobResponse, status_code=202)
async def create_job_endpoint(
    payload: JobCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    enforce_plan_limits(db, user)
    job = create_job(db, payload.url, user)

    # Enqueue in Redis
    # Function name must match what's defined in WorkerSettings.functions
    await request.app.state.redis.enqueue_job("execute_pipeline", job.id)

    return job

@router.get("", response_model=list[JobResponse])
def get_jobs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return (
        db.query(Job)
        .filter(Job.user_id == user.id)
        .order_by(Job.created_at.desc())
        .all()
    )

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
        return {"error": "Job not found"}
    return job

@router.get("/{job_id}/download")
def download_epub(job_id: str, db: Session = Depends(get_db)):
    file = (
        db.query(File)
        .filter(File.job_id == job_id, File.type == "epub")
        .first()
    )

    if not file:
        return {"error": "File not found"}

    from fastapi.responses import RedirectResponse
    from app.services.storage_service import storage_service
    
    presigned_url = storage_service.generate_presigned_url(file.path)

    if not presigned_url:
        raise HTTPException(500, "Failed to generate download link")
        
    return RedirectResponse(url=presigned_url)