"""Password hashing and JWT helpers."""

from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from src.core.config import settings
from src.core.exceptions import TokenExpiredError, TokenInvalidError


def create_access_token(subject: str, email: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token for an authenticated user session.

    Args:
        subject (str): The unique identifier of the user.
        email (str): The email address of the user.
        expires_delta (timedelta, optional): Custom expiration duration.

    Returns:
        str: Encoded JWT token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": subject,
        "email": email,
        "exp": int(expire.timestamp()),
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate an application JWT token.

    Args:
        token (str): The JWT string to decode and validate.

    Raises:
        TokenExpiredError: If the token's expiration claim has expired.
        TokenInvalidError: If decoding fails or any other signature checks fail.

    Returns:
        dict: The decoded token payload.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredError() from e
    except JWTError as e:
        raise TokenInvalidError() from e
