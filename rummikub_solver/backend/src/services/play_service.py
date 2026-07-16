"""Quick-play orchestration (S3 + Celery)."""

import json
import logging
import uuid
from fastapi import UploadFile
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import PlayNotFoundError
from src.core.s3 import upload_file_to_s3
from src.core.celery import celery_app
from src.services import board_service
from src.models.play import GamePlayRecord

logger = logging.getLogger(__name__)


async def get_play_by_id(play_id: str, user_id: str, redis: Redis, db: AsyncSession) -> dict:
    """Return recognition/solver results for a play owned by the user.

    Delegates to board_service.check_board_status (Redis first, then DB).
    """
    return await board_service.check_board_status(play_id, user_id, redis, db)


async def process_play_request(
    board_file: UploadFile,
    hand_file: UploadFile,
    user_id: str,
    redis: Redis,
    db: AsyncSession
) -> str:
    """Handle a new quick-play upload end to end.
    Creates the board row, stores both images in S3, commits, and dispatches
    process_board_image. Returns the board UUID string for polling.
    """
    logger.info("Processing play request upload: board=%s, hand=%s", board_file.filename, hand_file.filename)

    board = await board_service.create_board(db, user_id)
    board_id_str = str(board.id)

    try:
        board_bytes = await board_file.read()
    except Exception as e:
        logger.error("Failed to read board file: %s", e)
        raise

    try:
        hand_bytes = await hand_file.read()
    except Exception as e:
        logger.error("Failed to read hand file: %s", e)
        raise

    board_filename = board_file.filename or "board.jpg"
    board_s3_key = f"boards/{board_id_str}/{board_filename}"
    try:
        upload_file_to_s3(
            file_data=board_bytes,
            object_name=board_s3_key,
            content_type=board_file.content_type,
        )
    except Exception as e:
        logger.error("Failed to upload board image %s to S3: %s", board_id_str, e)
        raise

    hand_filename = hand_file.filename or "hand.jpg"
    hand_s3_key = f"boards/{board_id_str}/{hand_filename}"
    try:
        upload_file_to_s3(
            file_data=hand_bytes,
            object_name=hand_s3_key,
            content_type=hand_file.content_type,
        )
    except Exception as e:
        logger.error("Failed to upload hand image %s to S3: %s", board_id_str, e)
        raise

    await board_service.update_board_image_path(db, board.id, board_s3_key)
    await board_service.update_hand_image_path(db, board.id, hand_s3_key)

    # worker runs in another process: commit before enqueue
    await db.commit()

    try:
        celery_app.send_task(
            "src.tasks.process_board_image",
            args=[board_id_str],
        )
        logger.info("Dispatched Celery task process_board_image for board %s", board_id_str)
    except Exception as e:
        logger.error("Failed to dispatch Celery task for board %s: %s", board_id_str, e)
        raise

    return board_id_str


async def solve_board(play_id: str, user_id: str, db: AsyncSession) -> None:
    """Mark a completed board as solving and enqueue solve_board_task."""
    try:
        board_uuid = uuid.UUID(play_id)
    except ValueError:
        raise PlayNotFoundError("Play ID not found")
        
    board = await board_service.get_board_by_id(db, board_uuid)
    if not board:
        raise PlayNotFoundError("Play ID not found")
        
    if board.user_id != user_id:
        raise ValueError("Not authorized to access this board")
        
    if board.status != "completed":
        raise ValueError("Cannot solve a board that is not completed")
        
    if board.solution is not None:
        raise ValueError("Board is already locked or solved")
        
    board.solution = {}
    db.add(board)
    await db.commit()
    
    try:
        celery_app.send_task(
            "src.tasks.solve_board_task",
            args=[play_id],
        )
        logger.info("Dispatched Celery task solve_board_task for board %s", play_id)
    except Exception as e:
        logger.error("Failed to dispatch Celery task for board %s: %s", play_id, e)
        raise
