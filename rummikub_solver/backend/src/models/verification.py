"""Email verification token model."""

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from src.core.database import Base

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    token = Column(String(255), primary_key=True, index=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
