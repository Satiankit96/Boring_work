# core/exceptions.py
# Role: Domain-level exceptions. These are NOT HTTP exceptions.
# Route handlers catch these and convert them to HTTP responses with structured error codes.

class AuthModuleError(Exception):
    """Base exception for all auth module domain errors."""
    pass


class InvalidCredentialsError(AuthModuleError):
    """Raised when email/password combination is invalid. Generic on purpose — prevents email enumeration."""
    code = "INVALID_CREDENTIALS"
    message = "Email or password is incorrect"


class EmailAlreadyExistsError(AuthModuleError):
    """Raised when attempting to register with an already-registered email."""
    code = "EMAIL_ALREADY_EXISTS"
    message = "An account with this email already exists"


class UserNotFoundError(AuthModuleError):
    """Raised when a user lookup by ID returns nothing."""
    code = "USER_NOT_FOUND"
    message = "User not found"


class TokenExpiredError(AuthModuleError):
    """Raised when a JWT has expired."""
    code = "TOKEN_EXPIRED"
    message = "Access token has expired"


class InvalidTokenError(AuthModuleError):
    """Raised when a JWT is malformed or invalid."""
    code = "INVALID_TOKEN"
    message = "Invalid access token"
