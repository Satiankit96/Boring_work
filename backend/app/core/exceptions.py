"""
Domain Exceptions Module
========================
Role: Define domain-specific exceptions used by the service layer.
These are NOT HTTP exceptions — they are caught and mapped to HTTP responses in the API layer.
This separation allows the same business logic to be used with different interfaces (CLI, gRPC, etc.)
"""


class AuthException(Exception):
    """Base exception for all authentication-related errors."""
    
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidCredentialsError(AuthException):
    """
    Raised when login credentials are invalid.
    Uses generic message to prevent email enumeration attacks.
    """
    
    def __init__(self):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message="Email or password is incorrect"
        )


class EmailAlreadyExistsError(AuthException):
    """Raised when attempting to register with an email that's already in use."""
    
    def __init__(self):
        super().__init__(
            code="EMAIL_ALREADY_EXISTS",
            message="An account with this email already exists"
        )


class InvalidTokenError(AuthException):
    """Raised when a JWT token is invalid or expired."""
    
    def __init__(self):
        super().__init__(
            code="INVALID_TOKEN",
            message="Token is invalid or expired"
        )


class UserNotFoundError(AuthException):
    """Raised when a user cannot be found by ID."""
    
    def __init__(self):
        super().__init__(
            code="USER_NOT_FOUND",
            message="User not found"
        )
