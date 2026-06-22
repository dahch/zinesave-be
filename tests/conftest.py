from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from app.domain.repositories.cloud_connection_repository import CloudConnectionRepository
from app.domain.repositories.file_repository import FileRepository
from app.domain.repositories.intention_repository import IntentionRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.cloud_service import CloudService
from app.services.email_service import EmailService
from app.services.intention_service import IntentionService
from app.services.job_service import JobService
from app.services.queue_service import QueueService
from app.services.upload_service import UploadService
from app.services.user_service import UserService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def user_repo(mock_db):
    repo = UserRepository(mock_db)
    repo.get_by_email = Mock(return_value=None)
    repo.add = Mock(side_effect=lambda x: x)
    repo.update = Mock(side_effect=lambda x: x)
    return repo


@pytest.fixture
def cloud_conn_repo(mock_db):
    return CloudConnectionRepository(mock_db)


@pytest.fixture
def job_repo(mock_db):
    repo = JobRepository(mock_db)
    repo.get_recent_duplicate = Mock()
    repo.get_user_job = Mock()
    repo.add = Mock()
    repo.update = Mock()
    return repo


@pytest.fixture
def file_repo(mock_db):
    repo = FileRepository(mock_db)
    repo.get_epub_by_job_id = Mock()
    return repo


@pytest.fixture
def intention_repo(mock_db):
    repo = IntentionRepository(mock_db)
    repo.get_by_user_and_tier = Mock()
    repo.add = Mock(side_effect=lambda x: x)
    return repo


@pytest.fixture
def email_service():
    service = Mock(spec=EmailService)
    service.send_verification_email = Mock()
    service.send_password_reset_email = Mock()
    return service


@pytest.fixture
def queue_service():
    service = Mock(spec=QueueService)
    service.enqueue_job = AsyncMock()
    return service


@pytest.fixture
def cloud_service(cloud_conn_repo):
    service = Mock(spec=CloudService)
    service.upload_file = Mock()
    return service


@pytest.fixture
def auth_service(user_repo, cloud_conn_repo, email_service):
    return AuthService(user_repo, cloud_conn_repo, email_service)


@pytest.fixture
def user_service(user_repo, job_repo, cloud_conn_repo):
    return UserService(user_repo, job_repo, cloud_conn_repo)


@pytest.fixture
def intention_service(intention_repo, user_repo):
    return IntentionService(intention_repo, user_repo)


@pytest.fixture
def job_service(job_repo, user_repo, queue_service):
    return JobService(job_repo, user_repo, queue_service)


@pytest.fixture
def upload_service(job_repo, file_repo, cloud_conn_repo, cloud_service):
    return UploadService(job_repo, file_repo, cloud_conn_repo, cloud_service)
