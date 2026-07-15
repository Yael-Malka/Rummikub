"""JWT token creation and verification."""

import logging
from datetime import datetime, timedelta, timezone
import jwt
from src.core.config import settings

logger = logging.getLogger(__name__)


def create_access_token(data: dict) -> str:
    """Encode a JWT with exp based on ACCESS_TOKEN_EXPIRE_MINUTES.
    Caller must include sub, email, and jti in data for session tracking.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """Decode and verify a JWT signed with SECRET_KEY.
    Raises ValueError on expiry or any PyJWT validation error.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        raise ValueError("Token has expired") from e
    except jwt.PyJWTError as e:
        raise ValueError("Invalid token") from e
