"""Persist and revoke user sessions."""

import logging
from src.core.redis import init_redis_pool
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

async def create_session(jti: str, user_id: str, expires_in_seconds: int) -> None:
    """Create a new session in Redis using the JWT token's JTI.

    Args:
        jti (str): Unique identifier for the JWT.
        user_id (str): The user's ID.
        expires_in_seconds (int): Session TTL in seconds.
    """
    redis_pool = init_redis_pool()
    client = Redis(connection_pool=redis_pool)
    try:
        await client.setex(f"session:{jti}", expires_in_seconds, user_id)
        logger.info(f"Created session for user {user_id} with JTI {jti}")
    finally:
        await client.aclose()


async def is_session_valid(jti: str) -> bool:
    """Check if a session (JTI) is valid (exists in Redis).

    Args:
        jti (str): Unique identifier for the JWT.

    Returns:
        bool: True if valid, False otherwise.
    """
    redis_pool = init_redis_pool()
    client = Redis(connection_pool=redis_pool)
    try:
        exists = await client.exists(f"session:{jti}")
        return exists > 0
    finally:
        await client.aclose()


async def invalidate_session(jti: str) -> None:
    """Invalidate a session by removing its JTI from Redis.

    Args:
        jti (str): Unique identifier for the JWT.
    """
    redis_pool = init_redis_pool()
    client = Redis(connection_pool=redis_pool)
    try:
        await client.delete(f"session:{jti}")
        logger.info(f"Invalidated session with JTI {jti}")
    finally:
        await client.aclose()
