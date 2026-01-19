import tempfile
import os
import re
from urllib.parse import urlparse
from app.services.storage_service import storage_service

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_db
from app.domain.models.user import User
from app.domain.models.job import Job
from app.domain.models.file import File
from app.services.cloud_service import CloudService

router = APIRouter(prefix="/jobs", tags=["Upload"])

class UploadRequest(BaseModel):
    provider: str # google_drive, dropbox, onedrive

@router.post("/{job_id}/upload")
def upload_job_to_cloud(
    job_id: str,
    data: UploadRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Verify Job Ownership
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.user_id == user.id)
        .first()
    )

    if not job:
        raise HTTPException(404, "Job not found")

    # 2. Get EPUB file path
    epub_file = (
        db.query(File)
        .filter(File.job_id == job.id, File.type == "epub")
        .first()
    )

    if not epub_file:
        raise HTTPException(400, "EPUB file not ready yet")

    # 3. Determine Providers
    from app.domain.models.cloud_connection import CloudConnection
    
    target_providers = []
    if data.provider == "all":
        connections = (
            db.query(CloudConnection.provider)
            .filter(CloudConnection.user_id == user.id)
            .all()
        )
        target_providers = [c[0] for c in connections]
    else:
        target_providers = [data.provider]

    if not target_providers:
        raise HTTPException(400, "No providers found to upload")

    # 4. Determine Filename from URL
    parsed = urlparse(job.source_url)
    # Get last part of path, e.g. /foo/bar/baz -> baz
    path_name = parsed.path.strip("/").split("/")[-1]
    # Remove extension if present
    path_name = os.path.splitext(path_name)[0]
    
    # Sanitize
    safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', path_name)
    
    if not safe_name:
        safe_name = f"article_{job.id[:8]}"
        
    filename = f"{safe_name}.epub"

    # 5. Download from B2 to Temp Directory with Nice Name
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_path = os.path.join(tmp_dir, filename)
        
        try:
            storage_service.download_file(epub_file.path, temp_path) 

            # 6. Upload Loop
            results = {}
            errors = []

            # Ensure dict exists (mutable)
            current_uploads = dict(job.external_uploads) if job.external_uploads else {}

            for provider in target_providers:
                try:
                    # We pass the temp_path which now has the proper filename
                    result = CloudService.upload_file(db, user.id, provider, temp_path)
                    current_uploads[provider] = result
                    results[provider] = result
                except Exception as e:
                    errors.append(f"{provider}: {str(e)}")
            
            # 7. Update Job
            job.external_uploads = current_uploads
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(job, "external_uploads")
            
            db.commit()

            return {
                "success": results,
                "errors": errors
            }
            
        except Exception as e:
             raise HTTPException(500, f"Upload flow failed: {str(e)}")
