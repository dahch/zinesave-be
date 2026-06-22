import os
import re
import tempfile
from typing import Any, Dict
from urllib.parse import urlparse

from app.domain.models.user import User
from app.domain.repositories.cloud_connection_repository import CloudConnectionRepository
from app.domain.repositories.file_repository import FileRepository
from app.domain.repositories.job_repository import JobRepository
from app.services.cloud_service import CloudService
from app.services.storage_service import storage_service


class UploadService:
    def __init__(
        self,
        job_repo: JobRepository,
        file_repo: FileRepository,
        cloud_conn_repo: CloudConnectionRepository,
        cloud_service: CloudService,
    ):
        self.job_repo = job_repo
        self.file_repo = file_repo
        self.cloud_conn_repo = cloud_conn_repo
        self.cloud_service = cloud_service

    def _determine_target_providers(self, user_id: int, provider_param: str) -> list[str]:
        if provider_param == "all":
            connections = (
                self.cloud_conn_repo.db.query(self.cloud_conn_repo.model.provider)
                .filter(self.cloud_conn_repo.model.user_id == user_id)
                .all()
            )
            return [c[0] for c in connections]
        return [provider_param]

    def _get_safe_filename(self, source_url: str, job_id: str) -> str:
        parsed = urlparse(source_url)
        path_name = parsed.path.strip("/").split("/")[-1]
        path_name = os.path.splitext(path_name)[0]
        safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", path_name)

        if not safe_name:
            safe_name = f"article_{job_id[:8]}"

        return f"{safe_name}.epub"

    def upload_job_to_cloud(self, user: User, job_id: str, provider_param: str) -> Dict[str, Any]:
        job = self.job_repo.get_user_job(job_id, user.id)
        if not job:
            raise ValueError("Job not found")

        epub_file = self.file_repo.get_epub_by_job_id(job.id)
        if not epub_file:
            raise ValueError("EPUB file not ready yet")

        target_providers = self._determine_target_providers(user.id, provider_param)
        if not target_providers:
            raise ValueError("No providers found to upload")

        filename = self._get_safe_filename(job.source_url, job.id)

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = os.path.join(tmp_dir, filename)

            try:
                storage_service.download_file(epub_file.path, temp_path)
            except Exception as e:
                raise ValueError(f"Failed to download EPUB from storage: {str(e)}")

            results = {}
            errors = []
            current_uploads = dict(job.external_uploads) if job.external_uploads else {}

            for provider in target_providers:
                try:
                    result = self.cloud_service.upload_file(user.id, provider, temp_path)
                    current_uploads[provider] = result
                    results[provider] = result
                except Exception as e:
                    errors.append(f"{provider}: {str(e)}")

            job.external_uploads = current_uploads
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(job, "external_uploads")

            self.job_repo.update(job)

            return {"success": results, "errors": errors}
