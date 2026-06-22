from unittest.mock import patch

import pytest

from app.domain.models.job import Job
from app.domain.models.user import User


@pytest.mark.asyncio
async def test_create_job_insufficient_credits(job_service):
    user = User(id=1, email="test@example.com", credits=0)

    with pytest.raises(ValueError, match="INSUFFICIENT_CREDITS"):
        await job_service.create_job("https://example.com/article", user)


@pytest.mark.asyncio
@patch("app.services.job_service.socket.getaddrinfo")
async def test_create_job_duplicate(mock_getaddrinfo, job_service, job_repo):
    mock_getaddrinfo.return_value = [(2, 1, 6, "", ("93.184.216.34", 0))]
    user = User(id=1, email="test@example.com", credits=10)

    job_repo.get_recent_duplicate.return_value = Job(
        id="123", source_url="https://example.com/article"
    )

    with pytest.raises(ValueError, match="already in progress"):
        await job_service.create_job("https://example.com/article", user)


@pytest.mark.asyncio
@patch("app.services.job_service.socket.getaddrinfo")
async def test_create_job_success(
    mock_getaddrinfo, job_service, job_repo, user_repo, queue_service
):
    mock_getaddrinfo.return_value = [(2, 1, 6, "", ("93.184.216.34", 0))]
    user = User(id=1, email="test@example.com", credits=10)

    job_repo.get_recent_duplicate.return_value = None

    # We mock add to return a Job with an ID to avoid AttributeError
    mock_job = Job(id="abc-123", source_url="https://example.com/article")
    job_repo.add.return_value = mock_job

    job = await job_service.create_job("https://example.com/article", user)

    assert job.source_url == "https://example.com/article"
    assert user.credits == 9

    job_repo.add.assert_called_once()
    user_repo.update.assert_called_once_with(user)
    queue_service.enqueue_job.assert_called_once_with("execute_pipeline", "abc-123")
