"""Board rows and Redis polling cache."""

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.db_models import Board

logger = logging.getLogger(__name__)


async def create_board(db: AsyncSession, user_id: str) -> Board:
    """Create a new board row for a user upload session.
    flush() assigns the UUID before we store S3 paths on the same row.
    """
    board = Board(
        user_id=user_id,
        in_progress=False,
    )
    db.add(board)
    await db.flush()
    logger.info("Created board record %s for user %s", board.id, user_id)
    return board


async def get_board_by_id(db: AsyncSession, board_id: UUID) -> Board | None:
    """Load a board by primary key.
    Returns None if the id does not exist (deleted or never created).
    """
    result = await db.execute(select(Board).where(Board.id == board_id))
    return result.scalars().first()


async def update_board_image_path(db: AsyncSession, board_id: UUID, image_path: str) -> Board | None:
    """Store the S3 key for the table photo after the client uploads it.
    image_path is the object key, not a public URL.
    """
    board = await get_board_by_id(db, board_id)
    if board:
        board.image_path = image_path
        db.add(board)
        await db.flush()
        logger.info("Updated board %s image_path to %s", board_id, image_path)
    return board


async def update_hand_image_path(db: AsyncSession, board_id: UUID, hand_image_path: str) -> Board | None:
    """Store the S3 key for the rack/hand photo.
    Both board and hand images are required before recognition can run.
    """
    board = await get_board_by_id(db, board_id)
    if board:
        board.hand_image_path = hand_image_path
        db.add(board)
        await db.flush()
        logger.info("Updated board %s hand_image_path to %s", board_id, hand_image_path)
    return board


async def update_classification_results(db: AsyncSession, board_id: UUID, results: dict) -> Board | None:
    """Save ML pipeline output and mark the board completed.
    The worker calls this when recognition finishes successfully.
    """
    board = await get_board_by_id(db, board_id)
    if board:
        board.classification_results = results
        board.in_progress = True
        board.status = "completed"
        db.add(board)
        await db.flush()
        logger.info("Completed classification for board %s", board_id)
    return board


from datetime import datetime, timezone, timedelta
from src.core.config import settings
from src.core.exceptions import PlayNotFoundError, PlayProcessingError, PlayFailedError
from redis.asyncio import Redis
import json


async def check_board_status(play_id: str, user_id: str, redis: Redis, db: AsyncSession):
    """Return recognition/solver results for a play, or raise while still running.
    Reads Redis first for speed; falls back to Postgres. Marks boards as failed
    if processing exceeds the configured timeout so clients do not poll forever.
    """
    import uuid
    try:
        board_uuid = uuid.UUID(play_id)
    except ValueError as e:
        raise PlayNotFoundError("Invalid play ID format") from e

    board = await get_board_by_id(db, board_uuid)
    if not board or board.user_id != user_id:
        raise PlayNotFoundError()

    # fail boards stuck in processing too long
    if board.status == "processing":
        max_duration = settings.PROCESSING_TIMEOUT_SECONDS + settings.PROCESSING_TIMEOUT_GRACE_SECONDS
        
        now = datetime.now(timezone.utc)
        if board.created_at:
            created_at = board.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
                
            if now - created_at > timedelta(seconds=max_duration):
                board.status = "failed"
                board.failure_code = "PROCESSING_TIMED_OUT"
                board.failure_message = "Processing took too long and was stopped. Please try again."
                db.add(board)
                await db.commit()

    # fast path: redis envelope
    redis_key = f"boards:{play_id}"
    cached_data = await redis.get(redis_key)
    
    if cached_data:
        envelope = json.loads(cached_data)
        if envelope.get("status") == "completed":
            res = envelope.get("result", {})
            if "solution" in envelope:
                res["solution"] = envelope["solution"]
                from src.services.solve_diff_service import generate_moves
                diff = generate_moves(res.get("sets", []), res.get("hand", []), envelope["solution"])
                res["moves"] = [m.model_dump() for m in diff.moves]
            return res
        elif envelope.get("status") == "failed":
            err = envelope.get("error", {})
            raise PlayFailedError(failure_code=err.get("code", "UNKNOWN_ERROR"), failure_message=err.get("message", "An unknown error occurred."))
            
    # slow path: reconstruct from DB
    if board.status == "completed":
        res = dict(board.classification_results) if board.classification_results else {}
        if board.fix_results is not None:
            res["sets"] = board.fix_results.get("sets", [])
            res["unassigned"] = board.fix_results.get("unassigned", [])
        res["hand"] = board.hand_results or []
        if board.solution is not None:
            res["solution"] = board.solution
            from src.services.solve_diff_service import generate_moves
            diff = generate_moves(res.get("sets", []), res.get("hand", []), board.solution)
            res["moves"] = [m.model_dump() for m in diff.moves]
        return res
    elif board.status == "failed":
        raise PlayFailedError(failure_code=board.failure_code or "UNKNOWN_ERROR", failure_message=board.failure_message or "An unknown error occurred.")
    
    raise PlayProcessingError()


async def update_board_correction(db: AsyncSession, board_id: UUID, corrected_sets: list, corrected_hand: list) -> Board | None:
    """Persist user-edited sets and hand after the correction UI.
    Clears failure fields and forces status back to completed.
    """
    board = await get_board_by_id(db, board_id)
    if board:
        board.fix_results = {
            "sets": corrected_sets,
            "unassigned": []
        }
        board.hand_results = corrected_hand
        board.status = "completed"
        board.failure_code = None
        board.failure_message = None
        db.add(board)
        await db.flush()
        logger.info("Saved user board/hand correction for board %s in DB", board_id)
    return board


async def update_board_redis_cache(redis: Redis, board: Board, corrected_sets: list, corrected_hand: list) -> None:
    """Push the corrected layout into Redis so the next poll sees it immediately.
    Uses the same envelope shape the worker writes after recognition.
    """
    res = dict(board.classification_results) if board.classification_results else {}
    res["sets"] = corrected_sets
    res["unassigned"] = []
    res["hand"] = corrected_hand
    
    envelope = {
        "id": str(board.id),
        "status": "completed",
        "result": res,
        "error": None
    }
    
    redis_key = f"boards:{board.id}"
    await redis.set(redis_key, json.dumps(envelope), ex=settings.REDIS_TTL_SECONDS)
    logger.info("Updated Redis cache boards:%s with corrected layout", board.id)
