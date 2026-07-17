"""Quick-play upload, poll, and saved-game CRUD."""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, File, UploadFile, status, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.redis import get_redis
from src.core.database import get_db
from sqlalchemy import select
from typing import List
from src.models.game import Game
from src.models.schemas.game import GameResponse, GameCreate, GameUpdateShare, GamePublicResponse
from src.models.auth import UserSession
from src.core.exceptions import PlayNotFoundError
from src.models.play import NextPlayResponse, PlaySubmissionResponse, validate_image_file, CorrectPlayRequest, SolveBoardResponse
from src.services.play_service import get_play_by_id, process_play_request, solve_board
from src.services.validation_service import validate_board_layout
from src.services.board_service import get_board_by_id, update_board_correction, update_board_redis_cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Gameplay"])


@router.get("/next-play/{play_id}", response_model=NextPlayResponse)
async def get_next_play(
    play_id: str,
    current_user: UserSession = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> NextPlayResponse:
    """Poll recognition or solver output for a quick-play session.
    Returns completed results or raises while the worker is still running.
    """
    logger.info("Retrieve play request: id=%s by user=%s", play_id, current_user.email)
    record_result = await get_play_by_id(play_id, current_user.user_id, redis, db)
    return NextPlayResponse(id=play_id, status="completed", result=record_result)


@router.post("/send-play", response_model=PlaySubmissionResponse)
async def send_play(
    board_image: UploadFile = File(...),
    hand_image: UploadFile = File(...),
    current_user: UserSession = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> PlaySubmissionResponse:
    """Accept board + hand images, store them, and enqueue recognition.
    Response play_id is what the client passes to /next-play for polling.
    """
    logger.info(
        "Board & hand image upload request: board=%s, hand=%s by user=%s",
        board_image.filename,
        hand_image.filename,
        current_user.email,
    )
    validate_image_file(board_image)
    validate_image_file(hand_image)

    play_id = await process_play_request(board_image, hand_image, current_user.user_id, redis, db)
    return PlaySubmissionResponse(id=play_id, status="processing")


@router.post("/next-play/{play_id}/solve", response_model=SolveBoardResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_solve_board(
    play_id: str,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SolveBoardResponse:
    """Dispatch the solver Celery task for an already-recognized board.
    Board must belong to the caller and must not already have a solution.
    """
    logger.info("Manual solve request: id=%s by user=%s", play_id, current_user.email)
    
    try:
        await solve_board(play_id, current_user.user_id, db)
        return SolveBoardResponse(message="Solver task dispatched", play_id=play_id)
    except PlayNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        if "authorized" in str(e):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/correct/{play_id}", response_model=NextPlayResponse)
async def correct_board(
    play_id: str,
    payload: CorrectPlayRequest,
    current_user: UserSession = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> NextPlayResponse:
    """Save user-corrected sets and hand after the preview editor.
    Validates layout server-side, then updates Postgres and the Redis cache.
    """
    logger.info("Manual correction request: id=%s by user=%s", play_id, current_user.email)

    # 1. Parse and validate UUID format
    try:
        board_uuid = UUID(play_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Play ID not found"
        )

    # 2. Retrieve the board from DB
    board = await get_board_by_id(db, board_uuid)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Play ID not found"
        )

    # 3. Check ownership
    if board.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this board"
        )

    # 4. Check status is completed or failed (cannot correct while work is running)
    if board.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot correct a board in processing status"
        )

    # 4.5 Check if board is locked
    if board.solution is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Board is locked for solving and cannot be corrected"
        )

    # 5. Extract raw data from payload for validation
    raw_sets = [s.model_dump() for s in payload.sets]
    raw_unassigned = [u.model_dump() for u in payload.unassigned]
    raw_hand = [h.model_dump() for h in payload.hand]

    # 6. Run Rummikub and structural validation
    try:
        validate_board_layout(raw_sets, raw_unassigned, raw_hand)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid board layout: {str(e)}"
        )

    # 7. Persist corrections to Database
    updated_board = await update_board_correction(db, board_uuid, raw_sets, raw_hand)
    await db.commit()

    # 8. Update Redis cache with the corrected result envelope
    await update_board_redis_cache(redis, updated_board, raw_sets, raw_hand)

    # 9. Return the updated NextPlayResponse
    res = dict(updated_board.classification_results) if updated_board.classification_results else {}
    res["sets"] = raw_sets
    res["unassigned"] = []
    res["hand"] = raw_hand

    return NextPlayResponse(
        id=play_id,
        status="completed",
        result=res,
        error=None
    )


# Game Endpoints
@router.get("/games", response_model=List[GameResponse])
async def get_games(
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[GameResponse]:
    """Return all non-deleted games owned by the signed-in user.
    Ordered by last_updated descending so recent games appear first.
    """
    logger.info("Retrieve games request by user=%s", current_user.email)
    query = select(Game).where(Game.user_id == current_user.user_id, Game.is_deleted == False).order_by(Game.last_updated.desc())
    result = await db.execute(query)
    return list(result.scalars().all())

@router.post("/games", response_model=GameResponse)
async def create_game(
    payload: GameCreate,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameResponse:
    """Create a game row for the current user.

    Name and description are optional labels shown in the games list.
    """
    logger.info("Create game request: name=%s by user=%s", payload.name, current_user.email)
    game = Game(
        user_id=current_user.user_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return game

@router.patch("/games/{game_id}/share", response_model=GameResponse)
async def share_game(
    game_id: UUID,
    payload: GameUpdateShare,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GameResponse:
    """Toggle whether a game is visible on the public /public endpoint.
    Only the owner can change sharing; deleted games cannot be shared.
    """
    logger.info("Share game request: id=%s by user=%s", game_id, current_user.email)
    query = select(Game).where(Game.id == game_id, Game.user_id == current_user.user_id, Game.is_deleted == False)
    result = await db.execute(query)
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game.is_shared = payload.is_shared
    await db.commit()
    await db.refresh(game)
    return game

@router.delete("/games/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_game(
    game_id: UUID,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a game: sets is_deleted without removing turn rows.
    The game disappears from the owner's list but data stays for recovery.
    """
    logger.info("Delete game request: id=%s by user=%s", game_id, current_user.email)
    query = select(Game).where(Game.id == game_id, Game.user_id == current_user.user_id, Game.is_deleted == False)
    result = await db.execute(query)
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game.is_deleted = True
    await db.commit()

@router.get("/games/{game_id}/public", response_model=GamePublicResponse)
async def get_public_game(
    game_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> GamePublicResponse:
    """Public read-only view of a shared game: no auth required.
    Returns 404 if the game is not shared, deleted, or does not exist.
    """
    logger.info("Retrieve public game request: id=%s", game_id)
    query = select(Game).where(Game.id == game_id, Game.is_shared == True, Game.is_deleted == False)
    result = await db.execute(query)
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game
