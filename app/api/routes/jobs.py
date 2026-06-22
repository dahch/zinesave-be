from fastapi import APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.services import get_file_repo, get_job_service
from app.domain.models.user import User
from app.domain.repositories.file_repository import FileRepository
from app.domain.schemas.job import JobCompositeCreate, JobCreate, JobListResponse, JobResponse
from app.services.job_service import JobService
from app.services.storage_service import storage_service

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", response_model=JobResponse, status_code=202)
@limiter.limit("10/minute")
async def create_job_endpoint(
    payload: JobCreate,
    request: Request,
    user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
):
    # Pass request down to queue service if needed? We already injected it in get_job_service
    # So job_service already has access to the queue
    job = await job_service.create_job(str(payload.url), user)
    return job


@router.post("/composite", response_model=JobResponse, status_code=202)
@limiter.limit("10/minute")
async def create_composite_job_endpoint(
    payload: JobCompositeCreate,
    request: Request,
    user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
):
    job = await job_service.create_composite_job(
        [str(u) for u in payload.urls], payload.title, user
    )
    return job


@router.get("", response_model=JobListResponse)
def get_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
):
    return job_service.get_jobs(user, page, per_page)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
):
    return job_service.get_job(job_id, user)


@router.get("/{job_id}/download")
def download_epub(
    job_id: str,
    user: User = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
    file_repo: FileRepository = Depends(get_file_repo),
):
    # Verify job belongs to user
    job = job_service.get_job(job_id, user)

    file = file_repo.get_epub_by_job_id(job.id)

    if not file:
        raise ValueError("File not found or expired")

    presigned_url = storage_service.generate_presigned_url(file.path)

    if not presigned_url:
        raise ValueError("Failed to generate download link")

    return {"download_url": presigned_url}
