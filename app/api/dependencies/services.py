from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
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


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_job_repo(db: Session = Depends(get_db)) -> JobRepository:
    return JobRepository(db)


def get_file_repo(db: Session = Depends(get_db)) -> FileRepository:
    return FileRepository(db)


def get_cloud_conn_repo(db: Session = Depends(get_db)) -> CloudConnectionRepository:
    return CloudConnectionRepository(db)


def get_intention_repo(db: Session = Depends(get_db)) -> IntentionRepository:
    return IntentionRepository(db)


def get_queue_service(request: Request) -> QueueService:
    return QueueService(request.app.state.redis)


def get_cloud_service(
    cloud_conn_repo: CloudConnectionRepository = Depends(get_cloud_conn_repo),
) -> CloudService:
    return CloudService(cloud_conn_repo)


def get_email_service() -> EmailService:
    return EmailService()


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
    cloud_conn_repo: CloudConnectionRepository = Depends(get_cloud_conn_repo),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    return AuthService(user_repo, cloud_conn_repo, email_service)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo),
    job_repo: JobRepository = Depends(get_job_repo),
    cloud_conn_repo: CloudConnectionRepository = Depends(get_cloud_conn_repo),
) -> UserService:
    return UserService(user_repo, job_repo, cloud_conn_repo)


def get_job_service(
    job_repo: JobRepository = Depends(get_job_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    queue_service: QueueService = Depends(get_queue_service),
) -> JobService:
    return JobService(job_repo, user_repo, queue_service)


def get_intention_service(
    intention_repo: IntentionRepository = Depends(get_intention_repo),
    user_repo: UserRepository = Depends(get_user_repo),
) -> IntentionService:
    return IntentionService(intention_repo, user_repo)


def get_upload_service(
    job_repo: JobRepository = Depends(get_job_repo),
    file_repo: FileRepository = Depends(get_file_repo),
    cloud_conn_repo: CloudConnectionRepository = Depends(get_cloud_conn_repo),
    cloud_service: CloudService = Depends(get_cloud_service),
) -> UploadService:
    return UploadService(job_repo, file_repo, cloud_conn_repo, cloud_service)
