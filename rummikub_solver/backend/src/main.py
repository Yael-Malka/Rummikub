"""FastAPI app entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from src.api.routes.auth import router as auth_router
from src.api.routes.play import router as play_router
from src.core.config import settings
from src.core.redis import close_redis_pool, init_redis_pool, check_redis_health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the Redis pool at startup and close it on shutdown."""
    logger.info("Starting up Rummikub Solver API...")
    init_redis_pool()

    yield

    logger.info("Shutting down Rummikub Solver API...")
    await close_redis_pool()


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

if settings.REDIRECT_TO_HTTPS:
    logger.info("Enforcing HTTPS redirect middleware")
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(play_router, prefix="/api/v1/play")


@app.get("/")
async def root() -> dict[str, str]:
    """Simple health/welcome route for sanity checks."""
    return {"message": "Welcome to Rummikub Solver API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Report whether the API process is up and Redis is reachable.
    """
    redis_healthy = await check_redis_health()
    status = "ok" if redis_healthy else "degraded"
    redis_status = "connected" if redis_healthy else "disconnected"

    return {
        "status": status,
        "redis": redis_status,
        "app": "running",
    }
