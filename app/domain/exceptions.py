class DomainException(Exception):
    """Base class for all domain-level exceptions."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UserNotFoundException(DomainException):
    def __init__(self, message: str = "User not found"):
        super().__init__(message, status_code=404)


class EmailAlreadyExistsException(DomainException):
    def __init__(self, message: str = "Email already exists"):
        super().__init__(message, status_code=400)


class InvalidCredentialsException(DomainException):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, status_code=401)


class EmailNotVerifiedException(DomainException):
    def __init__(self, message: str = "Email not verified"):
        super().__init__(message, status_code=403)


class InvalidTokenException(DomainException):
    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message, status_code=400)
