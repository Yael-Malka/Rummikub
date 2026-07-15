"""HTTP-friendly domain errors."""

from fastapi import HTTPException, status


class AuthError(HTTPException):
    """Base exception for authentication and authorization failures."""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredError(AuthError):
    """Exception raised when the application JWT token has expired."""

    def __init__(self, detail: str = "Session token has expired"):
        super().__init__(detail=detail)


class TokenInvalidError(AuthError):
    """Exception raised when the application JWT token is invalid."""

    def __init__(self, detail: str = "Invalid session token"):
        super().__init__(detail=detail)


class RedisConnectionError(HTTPException):
    """Exception raised when the server cannot connect to Redis."""

    def __init__(self, detail: str = "Storage connection failed"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )


class InvalidImageError(HTTPException):
    """Exception raised when the uploaded image is invalid or has incorrect format."""

    def __init__(self, detail: str = "Invalid image file format or size"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )

