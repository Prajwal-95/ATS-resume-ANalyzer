"""
Secure token utilities for email verification and password reset.

Tokens are cryptographically random, single-use, time-limited, and stored as
SHA-256 hashes so a database leak does not expose usable tokens.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.models import User


def generate_token() -> str:
    """Generate a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of a token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_expires_at(minutes: int | None = None) -> datetime:
    """Return an aware UTC expiry timestamp."""
    minutes = minutes if minutes is not None else settings.EMAIL_VERIFICATION_EXPIRE_MINUTES
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        # Treat naive timestamps as UTC for backwards compatibility.
        return datetime.utcnow() > expires_at
    return datetime.now(timezone.utc) > expires_at


async def store_verification_token(db: AsyncSession, user: User) -> str:
    """Generate, hash, and store a verification token for a user."""
    token = generate_token()
    user.verification_token_hash = hash_token(token)
    user.verification_token_expires_at = token_expires_at()
    await db.commit()
    return token


async def store_password_reset_token(db: AsyncSession, user: User) -> str:
    """Generate, hash, and store a password-reset token for a user."""
    token = generate_token()
    user.password_reset_token_hash = hash_token(token)
    user.password_reset_token_expires_at = token_expires_at(settings.PASSWORD_RESET_EXPIRE_MINUTES)
    await db.commit()
    return token


async def consume_verification_token(
    db: AsyncSession,
    token: str,
) -> User | None:
    """Validate and consume a verification token.

    Returns the matching user on success, or None for any invalid/expired/
    previously-used token. Never raises.
    """
    if not token or not isinstance(token, str):
        return None

    token_hash = hash_token(token)
    result = await db.execute(
        select(User).where(User.verification_token_hash == token_hash)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    if is_expired(user.verification_token_expires_at):
        return None

    # Single-use: clear the token hash regardless of outcome.
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    user.email_verified = True
    await db.commit()
    return user


async def consume_password_reset_token(
    db: AsyncSession,
    token: str,
) -> User | None:
    """Validate and consume a password-reset token.

    Returns the matching user on success, or None for any invalid/expired/
    previously-used token. Never raises.
    """
    if not token or not isinstance(token, str):
        return None

    token_hash = hash_token(token)
    result = await db.execute(
        select(User).where(User.password_reset_token_hash == token_hash)
    )
    user = result.scalar_one_or_none()
    if user is None:
        return None

    if is_expired(user.password_reset_token_expires_at):
        return None

    # Single-use: clear the token hash regardless of outcome.
    user.password_reset_token_hash = None
    user.password_reset_token_expires_at = None
    await db.commit()
    return user


async def invalidate_verification_tokens(db: AsyncSession, user: User) -> None:
    """Clear any pending verification tokens for a user."""
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    await db.commit()


async def invalidate_password_reset_tokens(db: AsyncSession, user: User) -> None:
    """Clear any pending password-reset tokens for a user."""
    user.password_reset_token_hash = None
    user.password_reset_token_expires_at = None
    await db.commit()