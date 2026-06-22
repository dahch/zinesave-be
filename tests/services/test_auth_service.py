import pytest

from app.domain.exceptions import EmailAlreadyExistsException, InvalidCredentialsException
from app.domain.models.user import User
from app.domain.schemas.auth import Login, Register


def test_register_user_success(auth_service, email_service, user_repo):
    data = Register(
        email="test@example.com",
        name="Test User",
        password="Password123!",
        is_company=False,
        country="US",
        vat_number=None,
    )

    user = auth_service.register_user(data)

    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.is_verified is False

    user_repo.add.assert_called_once()
    email_service.send_verification_email.assert_called_once()


def test_register_user_email_exists(auth_service, user_repo):
    user_repo.get_by_email.return_value = User(email="test@example.com")

    data = Register(
        email="test@example.com",
        name="Test User",
        password="Password123!",
        is_company=False,
        country="US",
        vat_number=None,
    )

    with pytest.raises(EmailAlreadyExistsException):
        auth_service.register_user(data)


def test_login_user_not_found(auth_service, user_repo):
    user_repo.get_by_email.return_value = None
    data = Login(email="test@example.com", password="Password123!")

    with pytest.raises(InvalidCredentialsException):
        auth_service.login_user(data)

from app.domain.exceptions import EmailNotVerifiedException, InvalidTokenException, UserNotFoundException
from app.domain.schemas.auth import ResetPassword
from unittest.mock import patch
from app.core.password import hash_password

def test_login_user_not_verified(auth_service, user_repo):
    hashed = hash_password("Password123!")
    user_repo.get_by_email.return_value = User(id="1", email="test@example.com", provider="email", password_hash=hashed, is_verified=False)
    data = Login(email="test@example.com", password="Password123!")
    
    with pytest.raises(EmailNotVerifiedException):
        auth_service.login_user(data)

def test_verify_email(auth_service, user_repo):
    user = User(id="1", email="test@example.com", is_verified=False)
    token = auth_service.verify_email(user)
    assert user.is_verified is True
    user_repo.update.assert_called_once_with(user)
    assert isinstance(token, str)

def test_request_password_reset(auth_service, user_repo, email_service):
    user = User(id="1", email="test@example.com", provider="email")
    user_repo.get_by_email.return_value = user
    auth_service.request_password_reset("test@example.com")
    email_service.send_password_reset_email.assert_called_once()

@patch("app.services.auth_service.verify_reset_token")
def test_reset_password(mock_verify_reset_token, auth_service, user_repo):
    mock_verify_reset_token.return_value = "test@example.com"
    user = User(id="1", email="test@example.com")
    user_repo.get_by_email.return_value = user
    data = ResetPassword(token="valid_token", new_password="NewPassword123!")
    
    auth_service.reset_password(data)
    user_repo.update.assert_called_once()
    
def test_resolve_oauth_user_new(auth_service, user_repo):
    user_repo.get_by_provider.return_value = None
    user_repo.get_by_email.return_value = None
    auth_service.resolve_oauth_user("test@example.com", "Test", "123", "google")
    user_repo.add.assert_called_once()
