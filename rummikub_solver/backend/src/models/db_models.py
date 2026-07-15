"""Shared SQLAlchemy base imports."""

import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from src.core.database import Base

class Board(Base):
    __tablename__ = "boards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    image_path = Column(Text, nullable=True)
    hand_image_path = Column(Text, nullable=True)
    classification_results = Column(JSONB, nullable=True)
    fix_results = Column(JSONB, nullable=True)
    hand_results = Column(JSONB, nullable=True)
    solution = Column(JSONB, nullable=True)
    is_discarded = Column(Boolean, nullable=True)
    in_progress = Column(Boolean, nullable=False, default=False, index=True) # Legacy, to be deprecated
    status = Column(String(16), nullable=False, server_default='processing', index=True)
    failure_code = Column(String(32), nullable=True)
    failure_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
