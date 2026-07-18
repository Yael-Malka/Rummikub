"""Saved-game turn upload and processing."""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.api.deps import get_current_user
from src.core.database import get_db
from src.core.s3 import upload_file_to_s3
from src.core.celery import celery_app
from src.models.auth import UserSession
from src.models.turn import Turn
from src.models.schemas.turn import TurnCreate, TurnUpdate, TurnResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Turns"])

@router.get("/games/{game_id}/turns", response_model=List[TurnResponse])
async def list_turns(
    game_id: UUID,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List every turn in a game, oldest first.
    The Flutter list re-sorts newest-first for display after fetch.
    """
    query = select(Turn).where(Turn.game_id == game_id).order_by(Turn.created_at.asc())
    result = await db.execute(query)
    return list(result.scalars().all())

@router.post("/games/{game_id}/turns", response_model=TurnResponse, status_code=status.HTTP_201_CREATED)
async def create_turn(
    game_id: UUID,
    payload: TurnCreate,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an empty turn row before images are uploaded.
    Status starts as 'create'. When set, is_first_drop routes solving through the opening-meld path.
    """
    turn = Turn(
        game_id=game_id,
        name=payload.name,
        description=payload.description,
        status="create",
        is_first_drop=payload.is_first_drop,
    )
    db.add(turn)
    await db.commit()
    await db.refresh(turn)
    return turn

@router.get("/games/{game_id}/turns/{turn_id}", response_model=TurnResponse)
async def get_turn(
    game_id: UUID,
    turn_id: UUID,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch one turn by id within a game.
    For solved turns, attach move diff computed from the stored solution.
    Moves are response-only and are not persisted in the database.
    """
    query = select(Turn).where(Turn.id == turn_id, Turn.game_id == game_id)
    result = await db.execute(query)
    turn = result.scalar_one_or_none()
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
        
    if turn.status == "solved" and turn.results and "solution" in turn.results:
        # Build move list for the UI from the stored solution
        from src.services.solve_diff_service import generate_moves
        diff = generate_moves(
            turn.results.get("sets", []),
            turn.results.get("hand", []),
            turn.results["solution"]
        )
        # Deep copy or cast to dict to ensure we can modify it
        new_results = dict(turn.results)
        new_results["moves"] = [m.model_dump() for m in diff.moves]
        new_results["final_board"] = [b.model_dump() for b in diff.final_board]
        new_results["remaining_hand"] = [t.model_dump() for t in diff.remaining_hand]
        
        # Response-only override: not committed to DB
        turn.results = new_results
        
    return turn

@router.patch("/games/{game_id}/turns/{turn_id}", response_model=TurnResponse)
async def update_turn(
    game_id: UUID,
    turn_id: UUID,
    payload: TurnUpdate,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Partial update for turn metadata, status, results, or first-drop flag.
    The preview editor PATCHes corrected board/hand JSON through this endpoint.
    """
    query = select(Turn).where(Turn.id == turn_id, Turn.game_id == game_id)
    result = await db.execute(query)
    turn = result.scalar_one_or_none()
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
    
    if payload.name is not None:
        turn.name = payload.name
    if payload.description is not None:
        turn.description = payload.description
    if payload.status is not None:
        turn.status = payload.status
    if payload.results is not None:
        turn.results = payload.results
    if payload.is_first_drop is not None:
        turn.is_first_drop = payload.is_first_drop

    await db.commit()
    await db.refresh(turn)
    return turn

@router.delete("/games/{game_id}/turns/{turn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_turn(
    game_id: UUID,
    turn_id: UUID,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a turn and its associated S3 image keys.
    Does not affect other turns in the same game.
    """
    query = select(Turn).where(Turn.id == turn_id, Turn.game_id == game_id)
    result = await db.execute(query)
    turn = result.scalar_one_or_none()
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
        
    await db.delete(turn)
    await db.commit()

@router.post("/games/{game_id}/turns/{turn_id}/images", response_model=TurnResponse)
async def upload_turn_images(
    game_id: UUID,
    turn_id: UUID,
    board_image: UploadFile | None = File(None),
    hand_image: UploadFile | None = File(None),
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload board and/or hand images for a turn to S3.
    Each file is stored under turns/{turn_id}/; either image can be sent alone.
    """
    query = select(Turn).where(Turn.id == turn_id, Turn.game_id == game_id)
    result = await db.execute(query)
    turn = result.scalar_one_or_none()
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
        
    turn_id_str = str(turn.id)
    
    if board_image:
        try:
            board_bytes = await board_image.read()
            board_filename = board_image.filename or "board.jpg"
            board_s3_key = f"turns/{turn_id_str}/{board_filename}"
            upload_file_to_s3(
                file_data=board_bytes,
                object_name=board_s3_key,
                content_type=board_image.content_type,
            )
            turn.board_image_url = board_s3_key
        except Exception as e:
            logger.error(f"Failed to upload board image for turn {turn_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload board image")

    if hand_image:
        try:
            hand_bytes = await hand_image.read()
            hand_filename = hand_image.filename or "hand.jpg"
            hand_s3_key = f"turns/{turn_id_str}/{hand_filename}"
            upload_file_to_s3(
                file_data=hand_bytes,
                object_name=hand_s3_key,
                content_type=hand_image.content_type,
            )
            turn.hand_image_url = hand_s3_key
        except Exception as e:
            logger.error(f"Failed to upload hand image for turn {turn_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload hand image")
        
    await db.commit()
    await db.refresh(turn)
    return turn

@router.post("/games/{game_id}/turns/{turn_id}/process", response_model=TurnResponse)
async def process_turn(
    game_id: UUID,
    turn_id: UUID,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark the turn as processing and enqueue process_turn_image in Celery.
    Client should poll GET until status leaves 'processing'.
    """
    query = select(Turn).where(Turn.id == turn_id, Turn.game_id == game_id)
    result = await db.execute(query)
    turn = result.scalar_one_or_none()
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
        
    turn.status = "processing"
    
    await db.commit()
    await db.refresh(turn)
    
    try:
        celery_app.send_task(
            "src.tasks.process_turn_image",
            args=[str(turn.id)],
        )
        logger.info(f"Dispatched Celery task process_turn_image for turn {turn.id}")
    except Exception as e:
        logger.error(f"Failed to dispatch Celery task for turn {turn.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start processing task")
        
    return turn

@router.post("/games/{game_id}/turns/{turn_id}/solve", response_model=TurnResponse, status_code=status.HTTP_202_ACCEPTED)
async def solve_turn(
    game_id: UUID,
    turn_id: UUID,
    current_user: UserSession = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate the corrected layout, then enqueue solve_turn_task.
    Catches illegal sets and duplicate tiles before the worker runs the solver.
    """
    query = select(Turn).where(Turn.id == turn_id, Turn.game_id == game_id)
    result = await db.execute(query)
    turn = result.scalar_one_or_none()
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found")
        
    if not turn.results:
        raise HTTPException(status_code=400, detail="Turn has no results to solve")
        
    # layout checks (mirror frontend BoardValidator)
    sets = turn.results.get("sets", [])
    unassigned = turn.results.get("unassigned", [])
    hand = turn.results.get("hand", [])
    
    if unassigned:
        raise HTTPException(status_code=400, detail="Board has unassigned tiles. All tiles on board must be part of a valid set.")
        
    tile_counts = {}
    
    # count tiles on board
    for s in sets:
        tiles = s.get("tiles", [])
        if len(tiles) < 3:
            raise HTTPException(status_code=400, detail=f"Invalid board: set with less than 3 tiles found.")
        for t in tiles:
            key = f"{t.get('number', '0')}-{t.get('color', 'none')}"
            tile_counts[key] = tile_counts.get(key, 0) + 1
            
    # count tiles in hand
    for t in hand:
        key = f"{t.get('number', '0')}-{t.get('color', 'none')}"
        tile_counts[key] = tile_counts.get(key, 0) + 1
        
    for key, count in tile_counts.items():
        if count > 2 and not "joker" in key:
            raise HTTPException(status_code=400, detail=f"Invalid board: more than 2 tiles of the same kind ({key})")
            
    turn.status = "solving"
    
    await db.commit()
    await db.refresh(turn)
    
    # Enqueue solve task
    try:
        celery_app.send_task(
            "src.tasks.solve_turn_task",
            args=[str(turn.id)],
        )
        logger.info(f"Dispatched Celery task solve_turn_task for turn {turn.id}")
    except Exception as e:
        logger.error(f"Failed to dispatch Celery task for turn {turn.id}: {e}")
        # Revert status if we failed to dispatch
        turn.status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail="Failed to start solver task")
        
    return turn
