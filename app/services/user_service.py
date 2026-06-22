from typing import Any, Dict

from app.domain.models.user import User
from app.domain.repositories.cloud_connection_repository import CloudConnectionRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.schemas.user import UserUpdate


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        job_repo: JobRepository,
        cloud_conn_repo: CloudConnectionRepository,
    ):
        self.user_repo = user_repo
        self.job_repo = job_repo
        self.cloud_conn_repo = cloud_conn_repo

    def get_me(self, user: User) -> Dict[str, Any]:
        connections = (
            self.cloud_conn_repo.db.query(self.cloud_conn_repo.model.provider)
            .filter(self.cloud_conn_repo.model.user_id == user.id)
            .all()
        )
        providers = [c[0] for c in connections]

        return {**user.__dict__, "connected_providers": providers}

    def update_me(self, user: User, data: UserUpdate) -> User:
        if data.is_company is not None:
            user.is_company = data.is_company

        if data.country is not None:
            user.country = data.country

        if data.vat_number is not None:
            user.vat_number = data.vat_number

        return self.user_repo.update(user)

    def get_usage(self, user: User) -> Dict[str, Any]:
        return {"plan": user.plan, "credits": user.credits, "is_beta_tester": user.is_beta_tester}

    def get_dashboard(self, user: User) -> Dict[str, Any]:
        recent_jobs = self.job_repo.get_recent_jobs(user.id, limit=5)

        connections = (
            self.cloud_conn_repo.db.query(self.cloud_conn_repo.model.provider)
            .filter(self.cloud_conn_repo.model.user_id == user.id)
            .all()
        )

        connected_providers = [c[0] for c in connections]

        return {
            "usage": self.get_usage(user),
            "recent_jobs": recent_jobs,
            "connected_providers": connected_providers,
        }
