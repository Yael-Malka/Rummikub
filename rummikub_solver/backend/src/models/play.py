"""Pydantic models for quick-play flow."""

from fastapi import UploadFile
from pydantic import BaseModel, Field
from src.core.config import settings
from src.core.exceptions import InvalidImageError


def validate_image_file(file: UploadFile) -> None:
    """Validate that the uploaded file is a valid image and within size limits.

    Args:
        file (UploadFile): The uploaded file to validate.

    Raises:
        InvalidImageError: If the file is not a JPEG/PNG or exceeds size limits.
    """
    allowed_content_types = ["image/jpeg", "image/jpg", "image/png"]
    if file.content_type not in allowed_content_types:
        raise InvalidImageError(f"Unsupported media type: {file.content_type}. Only JPEG and PNG are supported.")

    # Validate file size if available
    if file.size is not None and file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        raise InvalidImageError(f"File size exceeds the maximum allowed limit of {max_mb:.1f} MB.")


class GamePlayRecord(BaseModel):
    """Internal schema representing the gameplay calculation results stored in Redis."""

    id: str = Field(..., description="Unique play UUID identifier")
    user_id: str = Field(..., description="ID of the user who owns this session play")
    result: int = Field(..., description="Calculated next play decision/number")


class PlaySubmissionResponse(BaseModel):
    """Response returned immediately after submitting a board image."""

    id: str = Field(..., description="Unique play UUID for tracking status and results")
    status: str = Field("processing", description="Submission status")


from typing import Optional, List

class ErrorDetail(BaseModel):
    code: str
    message: str

class HandTile(BaseModel):
    color: str
    number: str

class NextPlayResponse(BaseModel):
    """Response containing the calculated game play results or status."""

    id: str = Field(..., description="Unique play UUID identifier")
    status: str = Field(..., description="Lifecycle status: processing, completed, or failed")
    result: Optional[dict] = Field(None, description="Calculated next play decision/number")
    error: Optional[ErrorDetail] = Field(None, description="Error detail if status is failed")

class TileMove(BaseModel):
    tile_id: str = Field(..., description="Unique identifier for the tile")
    tile: 'Tile' = Field(..., description="The tile object itself")
    source_type: str = Field(..., description="Origin of the tile (e.g., hand, board_set)")
    source_id: Optional[str] = Field(None, description="The ID of the set the tile is moving from")
    destination_id: str = Field(..., description="The ID of the set the tile is moving to")
    step_index: int = Field(..., description="The sequence number of this move")

class SolveResult(BaseModel):
    status: str = Field(..., description="Status of the solve (e.g., solved, no_moves)")
    final_board: List['BoardSet'] = Field(..., description="The completed board state")
    remaining_hand: List['Tile'] = Field(..., description="The tiles left in the user's hand")
    moves: List[TileMove] = Field(..., description="Sequence of atomic moves")
    error: Optional[ErrorDetail] = Field(None, description="Error detail if status is failed")


class SolveBoardResponse(BaseModel):
    """Response returned when a board solve is triggered."""
    message: str
    play_id: str


class Tile(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the tile")
    color: str = Field(..., description="Tile color: red, blue, black, orange, or joker")
    number: str = Field(..., description="Tile number: 1-13, or joker")


class BoardSet(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the set")
    tiles: List[Tile] = Field(..., description="List of tiles in the set")


class CorrectPlayRequest(BaseModel):
    sets: List[BoardSet] = Field(..., description="All sets on the board")
    unassigned: List[Tile] = Field(..., description="Unassigned tiles on the board (must be empty)")
    hand: List[Tile] = Field(..., description="Tiles in the user's hand")
