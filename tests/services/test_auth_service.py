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
