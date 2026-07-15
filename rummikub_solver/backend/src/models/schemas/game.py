"""Game API schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class GameBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the game")
    description: Optional[str] = Field(None, max_length=500, description="Optional description of the game")

class GameCreate(GameBase):
    pass

class GameUpdateShare(BaseModel):
    is_shared: bool = Field(..., description="Whether the game is publicly shared")

class GameResponse(GameBase):
    id: UUID
    user_id: UUID
    is_shared: bool
    created_at: datetime
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

class GamePublicResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)
