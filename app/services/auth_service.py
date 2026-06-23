import logging

from app.core.config import settings
from app.core.password import hash_password, verify_password
from app.core.security import create_access_token, create_reset_token, verify_reset_token
from app.domain.exceptions import (
    EmailAlreadyExistsException,
    EmailNotVerifiedException,
    InvalidCredentialsException,
    InvalidTokenException,
    UserNotFoundException,
)
from app.domain.models.cloud_connection import CloudConnection
from app.domain.models.user import User
from app.domain.repositories.cloud_connection_repository import CloudConnectionRepository
from app.domain.repositories.user_repository import UserRepository
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        cloud_conn_repo: CloudConnectionRepository,
        email_service: EmailService,
    ):
        self.user_repo = user_repo
        self.cloud_conn_repo = cloud_conn_repo
        self.email_service = email_service

    def register_user(self, data) -> User:
        if self.user_repo.get_by_email(data.email):
            raise EmailAlreadyExistsException()

        user = User(
            email=data.email,
            name=data.name,
            provider="email",
            provider_id=data.email,
            password_hash=hash_password(data.password),
            plan="free",
            is_company=data.is_company,
            country=data.country,
            vat_number=data.vat_number,
            is_verified=False,
        )

        user = self.user_repo.add(user)

        # Send verification email
        token = create_access_token(user)
        frontend_url = settings.FRONTEND_URL
        verification_link = f"{frontend_url}/verify?token={token}"

        self.email_service.send_verification_email(user.email, verification_link)
        logger.info(f"Verification email sent to {user.email}")

        return user

    def login_user(self, data) -> str:
        user = self.user_repo.get_by_email(data.email)

        if (
            not user
            or user.provider != "email"
            or not verify_password(data.password, user.password_hash)
        ):
            raise InvalidCredentialsException()

        if not user.is_verified:
            raise EmailNotVerifiedException()

        return create_access_token(user)

    def verify_email(self, user: User) -> str:
        if not user.is_verified:
            user.is_verified = True
            self.user_repo.update(user)
        return create_access_token(user)

    def resend_verification(self, email: str) -> None:
        user = self.user_repo.get_by_email(email)
        if not user or user.is_verified:
            return

        token = create_access_token(user)
        frontend_url = settings.FRONTEND_URL
        verification_link = f"{frontend_url}/verify?token={token}"
        self.email_service.send_verification_email(user.email, verification_link)

    def request_password_reset(self, email: str) -> None:
        user = self.user_repo.get_by_email(email)
        if not user or user.provider != "email":
            return

        token = create_reset_token(user.email)
        frontend_url = settings.FRONTEND_URL
        reset_link = f"{frontend_url}/reset-password?token={token}"
        self.email_service.send_password_reset_email(user.email, reset_link)

    def reset_password(self, data) -> None:
        email = verify_reset_token(data.token)
        if not email:
            raise InvalidTokenException()

        user = self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundException()

        user.password_hash = hash_password(data.new_password)
        self.user_repo.update(user)

    def resolve_oauth_user(
        self, email: str, name: str, provider_id: str, provider: str = "google"
    ) -> User:
        user = self.user_repo.get_by_provider(provider, provider_id)
        if user:
            return user

        # Fallback by email
        user = self.user_repo.get_by_email(email)
        if user and user.provider == "email":
            user.provider = provider
            user.provider_id = provider_id
            self.user_repo.update(user)
            return user

        if user:
            user.provider = provider
            user.provider_id = provider_id
            self.user_repo.update(user)
            return user

        new_user = User(
            email=email,
            name=name,
            provider=provider,
            provider_id=provider_id,
            plan="free",
            is_verified=True,
        )
        user = self.user_repo.add(new_user)

        self.email_service.send_welcome_email(user.email)
        logger.info(f"Welcome email sent to {user.email}")

        return user

    def save_cloud_connection(
        self,
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: str = None,
        expiry=None,
        metadata: dict = None,
    ):
        connection = self.cloud_conn_repo.get_by_user_and_provider(user_id, provider)
        if not connection:
            connection = CloudConnection(user_id=user_id, provider=provider)

        connection.access_token = access_token
        if refresh_token:
            connection.refresh_token = refresh_token
        if expiry:
            connection.expires_at = expiry
        if metadata:
            connection.metadata_info = metadata

        if not connection.id:
            self.cloud_conn_repo.add(connection)
        else:
            self.cloud_conn_repo.update(connection)
