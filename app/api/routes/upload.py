from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.services import get_upload_service
from app.domain.models.user import User
from app.services.upload_service import UploadService

router = APIRouter(prefix="/jobs", tags=["Upload"])

class UploadRequest(BaseModel):
    provider: str # google_drive, dropbox, onedrive, all

@router.post("/{job_id}/upload")
def upload_job_to_cloud(
    job_id: str,
    data: UploadRequest,
    user: User = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service)
):
    return upload_service.upload_job_to_cloud(user, job_id, data.provider)
