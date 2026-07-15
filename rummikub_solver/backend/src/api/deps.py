"""Auth dependency: load user from JWT."""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis
from src.core.exceptions import TokenInvalidError
from src.core.redis import get_redis
from src.core.security import decode_access_token
from src.models.auth import UserSession

reusable_oauth2 = HTTPBearer()


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    redis: Redis = Depends(get_redis),
) -> UserSession:
    """Extract and validate the JWT from the Authorization header.
    Rejects blacklisted tokens (logout) and malformed payloads missing sub/email.
    """
    token_str = token.credentials

    is_blacklisted = await redis.exists(f"blacklist:{token_str}")
    if is_blacklisted:
        raise TokenInvalidError("Token has been revoked/logged out")

    import logging
    logger = logging.getLogger(__name__)
    try:
        payload = decode_access_token(token_str)
    except Exception as e:
        logger.error(f"Token decode failed: {e}")
        raise TokenInvalidError("Invalid session token")

    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id or not email:
        raise TokenInvalidError("Invalid token payload structure")

    return UserSession(user_id=str(user_id), email=str(email))
