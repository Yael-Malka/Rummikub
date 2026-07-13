"""Async Redis connection pool."""

import logging
from redis.asyncio import ConnectionPool, Redis
from src.core.config import settings

logger = logging.getLogger(__name__)

# Global connection pool instance
_redis_pool: ConnectionPool | None = None


def init_redis_pool() -> ConnectionPool:
    """Initialize the Redis connection pool if it hasn't been initialized yet.

    Returns:
        ConnectionPool: The initialized Redis connection pool.
    """
    global _redis_pool
    if _redis_pool is None:
        if settings.REDIS_URL:
            logger.info("Initializing Redis connection pool from REDIS_URL")
            _redis_pool = ConnectionPool.from_url(
                url=settings.REDIS_URL,
                decode_responses=True,
            )
        else:
            logger.info(
                "Initializing Redis connection pool: %s:%s",
                settings.REDIS_HOST,
                settings.REDIS_PORT,
            )
            _redis_pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
            )
    return _redis_pool


async def close_redis_pool() -> None:
    """Close the global Redis connection pool and disconnect all connections."""
    global _redis_pool
    if _redis_pool is not None:
        logger.info("Disconnecting Redis connection pool")
        try:
            await _redis_pool.disconnect()
        except RuntimeError:
            # Handle case where the event loop has already closed
            pass
        finally:
            _redis_pool = None



async def get_redis() -> Redis:
    """Dependency generator that provides a Redis client instance from the pool.

    Yields:
        Redis: An active async Redis client.
    """
    if _redis_pool is None:
        init_redis_pool()
    client = Redis(connection_pool=_redis_pool)
    try:
        yield client
    finally:
        try:
            await client.aclose()
        except RuntimeError:
            # Handle case where FastAPI's TestClient closes the event loop
            # before generator teardown is fully processed
            pass


async def check_redis_health() -> bool:
    """Ping the Redis server to verify that the connection is active.

    Returns:
        bool: True if connection is healthy, False otherwise.
    """
    try:
        if _redis_pool is None:
            init_redis_pool()
        client = Redis(connection_pool=_redis_pool)
        await client.ping()
        await client.aclose()
        return True
    except Exception as e:
        logger.error("Redis connection check failed: %s", e)
        return False
