"""
Authentication API endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import get_db
from app.models.models import User
from app.schemas.schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    VerifyEmailRequest, ResendVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    MessageResponse,
)
from app.utils.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
    validate_password,
)
from app.utils.rate_limiter import check_rate_limit
from app.utils.tokens import (
    store_verification_token, store_password_reset_token,
    consume_verification_token, consume_password_reset_token,
    invalidate_verification_tokens,
)
from app.services.email_service import (
    send_verification_email, send_password_reset_email,
)

logger = logging.getLogger("ats_resume_checker")

router = APIRouter()


def _normalize_email(email: str) -> str:
    """Normalize email for consistent storage and comparison."""
    return email.strip().lower()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user. Account starts as unverified; a verification email is sent."""
    check_rate_limit(request, prefix="auth", max_requests=settings.RATE_LIMIT_AUTH)

    email = _normalize_email(payload.email)

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Enforce password requirements
    password_error = validate_password(payload.password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)

    user = User(
        email=email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        email_verified=False,
    )
    try:
        db.add(user)
        await db.flush()

        # Generate verification token and store its hash on the user object.
        # We intentionally do NOT call store_verification_token here because it
        # issues its own db.commit(), which would split the user creation and
        # token storage into two separate transactions. Instead we replicate the
        # token-generation logic inline so everything commits atomically below.
        from app.utils.tokens import generate_token, hash_token, token_expires_at
        token = generate_token()
        user.verification_token_hash = hash_token(token)
        user.verification_token_expires_at = token_expires_at()

        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        logger.error("Registration failed for email=%s: %s", email, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )

    # Send verification email (never fails the registration if email delivery fails)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    sent = await send_verification_email(user.email, verify_url)
    if not sent:
        logger.warning(
            "Verification email could not be sent for new user id=%s",
            user.id,
        )

    return user


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    request: Request,
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify an email address using a token from the verification email."""
    check_rate_limit(request, prefix="auth", max_requests=settings.RATE_LIMIT_AUTH)

    user = await consume_verification_token(db, payload.token)
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid, expired, or already-used verification token",
        )
    return {"message": "Email address verified successfully. You can now log in."}


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Resend the verification email for an account.

    Returns the same response whether or not the email is registered, to
    avoid account enumeration.
    """
    check_rate_limit(request, prefix="auth", max_requests=settings.RATE_LIMIT_AUTH)

    email = _normalize_email(payload.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is not None and not user.email_verified:
        # Invalidate any previous token, then generate a new one
        await invalidate_verification_tokens(db, user)
        token = await store_verification_token(db, user)
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        await send_verification_email(user.email, verify_url)

    # Always return success to avoid account enumeration
    return {"message": "If an account exists, a verification email has been sent."}


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Login and get a JWT token. Blocked for unverified accounts."""
    check_rate_limit(request, prefix="auth", max_requests=settings.RATE_LIMIT_AUTH)

    email = _normalize_email(payload.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please check your inbox and verify your email address.",
        )

    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset email.

    Returns the same response whether or not the email is registered, to
    avoid account enumeration.
    """
    check_rate_limit(request, prefix="auth", max_requests=settings.RATE_LIMIT_AUTH)

    email = _normalize_email(payload.email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is not None:
        token = await store_password_reset_token(db, user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        await send_password_reset_email(user.email, reset_url)

    return {"message": "If an account exists, a password reset link has been sent."}


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset a password using a token from the reset email."""
    check_rate_limit(request, prefix="auth", max_requests=settings.RATE_LIMIT_AUTH)

    if len(payload.new_password) < settings.PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters",
        )

    password_error = validate_password(payload.new_password)
    if password_error:
        raise HTTPException(status_code=400, detail=password_error)

    user = await consume_password_reset_token(db, payload.token)
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid, expired, or already-used reset token",
        )

    user.hashed_password = hash_password(payload.new_password)
    await db.commit()
    return {"message": "Password has been reset successfully. You can now log in."}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return user