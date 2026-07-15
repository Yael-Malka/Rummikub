"""Turn API schemas."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

class TurnCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_first_drop: bool = False

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class TurnUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    is_first_drop: Optional[bool] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class TurnResponse(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    board_image_url: Optional[str] = None
    hand_image_url: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    is_first_drop: bool
    created_at: datetime

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
