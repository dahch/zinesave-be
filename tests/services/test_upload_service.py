import pytest
from unittest.mock import MagicMock, patch
from app.domain.models.user import User
from app.domain.models.job import Job
from app.domain.models.file import File

def test_upload_job_job_not_found(upload_service, job_repo):
    user = User(id=1)
    job_repo.get_user_job.return_value = None
    
    with pytest.raises(ValueError, match="Job not found"):
        upload_service.upload_job_to_cloud(user, "job123", "dropbox")

def test_upload_job_epub_not_found(upload_service, job_repo, file_repo):
    user = User(id=1)
    job_repo.get_user_job.return_value = Job(id="job123")
    file_repo.get_epub_by_job_id.return_value = None
    
    with pytest.raises(ValueError, match="EPUB file not ready yet"):
        upload_service.upload_job_to_cloud(user, "job123", "dropbox")

def test_upload_job_no_providers(upload_service, job_repo, file_repo, cloud_conn_repo):
    user = User(id=1)
    job_repo.get_user_job.return_value = Job(id="job123")
    file_repo.get_epub_by_job_id.return_value = File(id="file123", path="s3://b2/test.epub")
    
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_all = MagicMock(return_value=[])
    
    cloud_conn_repo.db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.all = mock_all
    
    with pytest.raises(ValueError, match="No providers found to upload"):
        upload_service.upload_job_to_cloud(user, "job123", "all")

@patch('app.services.upload_service.storage_service')
def test_upload_job_success(mock_storage_service, upload_service, job_repo, file_repo, cloud_service):
    user = User(id=1)
    mock_job = Job(id="job123", source_url="https://example.com/test-article")
    job_repo.get_user_job.return_value = mock_job
    file_repo.get_epub_by_job_id.return_value = File(id="file123", path="s3://b2/test.epub")
    
    cloud_service.upload_file.return_value = {"id": "external_id", "url": "https://dropbox.com/test"}
    
    result = upload_service.upload_job_to_cloud(user, "job123", "dropbox")
    
    assert "dropbox" in result["success"]
    assert len(result["errors"]) == 0
    
    assert mock_job.external_uploads["dropbox"]["id"] == "external_id"
    job_repo.update.assert_called_once_with(mock_job)
    mock_storage_service.download_file.assert_called_once()
