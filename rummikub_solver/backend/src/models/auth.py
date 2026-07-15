"""Pydantic models for auth requests/responses."""

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    """Response containing the application-specific JWT bearer token."""

    access_token: str = Field(..., description="Application session JWT token")
    token_type: str = Field("bearer", description="Token schema type")


class UserSession(BaseModel):
    """User data representation extracted from the validated session JWT."""

    user_id: str = Field(..., description="Unique subject/user ID")
    email: EmailStr = Field(..., description="User's verified email address")
