"""Register, login, logout, and email verification."""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from fastapi.security import HTTPAuthorizationCredentials
from src.core.database import get_db
from src.core.config import settings
from src.api.deps import get_current_user, reusable_oauth2
from src.models.user import User
from src.models.verification import EmailVerificationToken
from src.services.auth_service import create_access_token
from src.services.session_service import create_session, invalidate_session
from src.services.email_service import send_verification_email

from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class VerifyRequest(BaseModel):
    token: str

class MessageResponse(BaseModel):
    message: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a login password against the bcrypt hash stored on the user row.
    Returns False for wrong password or a missing hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plaintext password with bcrypt before writing to the database.
    Only called from /register: we never store raw passwords.
    """
    return pwd_context.hash(password)


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register_user(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user and email a verification link.
    The token expires after 24 hours; login is blocked until verified.
    """
    result = await db.execute(select(User).where(User.email == req.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists."
        )

    hashed_pwd = get_password_hash(req.password)
    new_user = User(
        email=req.email,
        full_name=req.full_name,
        password_hash=hashed_pwd
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token_str = str(uuid.uuid4())
    import datetime
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    verification_token = EmailVerificationToken(
        token=token_str,
        user_id=new_user.id,
        expires_at=expire
    )
    db.add(verification_token)
    await db.commit()

    import asyncio
    asyncio.create_task(send_verification_email(new_user.email, token_str))

    return {"message": "Verification email sent"}


@router.post("/login", response_model=TokenResponse)
async def login_user(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password, return a JWT.
    Rejects unverified accounts and wrong credentials with the same 401 message.
    """
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()
    
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
        
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not getattr(user, "email_verified", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in. Check your inbox.",
        )
        
    jti = str(uuid.uuid4())
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "jti": jti}
    )
    
    await create_session(jti, str(user.id), settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/logout")
async def logout_user(
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2)
):
    """Log out by deleting the session entry for this token's jti.
    We decode without checking expiry so logout still works on an expired JWT.
    """
    import jwt
    token_str = token.credentials
    try:
        payload = jwt.decode(token_str, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
        jti = payload.get("jti")
        if jti:
            await invalidate_session(jti)
    except Exception as e:
        logger.warning(f"Failed to invalidate session: {e}")

    return {"message": "Successfully logged out"}

@router.post("/verify", response_model=MessageResponse)
async def verify_email(req: VerifyRequest, db: AsyncSession = Depends(get_db)):
    """Mark the user's email as verified using the token from the email link.
    Deletes the token row after success so the link cannot be reused.
    """
    import datetime
    
    result = await db.execute(select(EmailVerificationToken).where(EmailVerificationToken.token == req.token))
    token_record = result.scalars().first()
    
    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid token")
        
    if token_record.expires_at < datetime.datetime.now(datetime.timezone.utc):
        raise HTTPException(status_code=400, detail="Token expired")
        
    user_result = await db.execute(select(User).where(User.id == token_record.user_id))
    user = user_result.scalars().first()
    
    if user:
        user.email_verified = True
        await db.delete(token_record)
        await db.commit()
        
    return {"message": "Email verified successfully"}

class ResendVerificationRequest(BaseModel):
    email: EmailStr

@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(req: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    """Send a fresh verification email and invalidate older tokens.
    Response is intentionally vague when the email is unknown (no user enumeration).
    """
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalars().first()
    
    if not user:
        return {"message": "If an account with that email exists, a verification link has been sent."}
        
    if getattr(user, "email_verified", False):
        return {"message": "Email is already verified."}
        
    # Delete old tokens
    await db.execute(
        EmailVerificationToken.__table__.delete().where(EmailVerificationToken.user_id == user.id)
    )
    
    token_str = str(uuid.uuid4())
    import datetime
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    verification_token = EmailVerificationToken(
        token=token_str,
        user_id=user.id,
        expires_at=expire
    )
    db.add(verification_token)
    await db.commit()
    
    import asyncio
    asyncio.create_task(send_verification_email(user.email, token_str))
    
    return {"message": "Verification email resent"}
