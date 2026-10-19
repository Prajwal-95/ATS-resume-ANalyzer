"""
Shared pytest configuration and fixtures for backend tests.
"""
import os

# Disable rate limiting for tests BEFORE importing app modules
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENVIRONMENT"] = "development"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app as fastapi_app
from app.database.connection import Base, get_db
import app.models.models  # noqa: F401 — register all models on metadata

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


fastapi_app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test and drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def reset_rate_limiter():
    """Reset rate limiter state before each test to prevent cross-test interference."""
    from app.utils.rate_limiter import _rate_limiter
    _rate_limiter._windows.clear()
    yield
    _rate_limiter._windows.clear()


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing."""
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_email(monkeypatch):
    """Mock the email service so no real emails are sent during tests."""
    sent_emails = []

    async def mock_send_verification_email(to, verify_url):
        sent_emails.append({"to": to, "type": "verification", "url": verify_url})
        return True

    async def mock_send_password_reset_email(to, reset_url):
        sent_emails.append({"to": to, "type": "password_reset", "url": reset_url})
        return True

    async def mock_send_email(to, subject, html_body, text_body):
        sent_emails.append({"to": to, "subject": subject})
        return True

    import app.services.email_service as email_service
    import app.api.auth as auth_module

    # Patch both the service module and the auth module where functions are imported
    monkeypatch.setattr(email_service, "send_verification_email", mock_send_verification_email)
    monkeypatch.setattr(email_service, "send_password_reset_email", mock_send_password_reset_email)
    monkeypatch.setattr(email_service, "send_email", mock_send_email)
    monkeypatch.setattr(auth_module, "send_verification_email", mock_send_verification_email)
    monkeypatch.setattr(auth_module, "send_password_reset_email", mock_send_password_reset_email)

    return sent_emails


@pytest_asyncio.fixture
async def verified_client(client, mock_email):
    """Register a user, verify their email, and return auth headers."""
    await client.post("/auth/register", json={
        "email": "verified@example.com",
        "username": "verifieduser",
        "password": "SecurePass1",
    })
    # Extract verification token from the mocked email for verified@example.com
    verify_token = None
    for email_data in mock_email:
        if email_data.get("type") == "verification" and email_data.get("to") == "verified@example.com":
            url = email_data["url"]
            verify_token = url.split("token=")[-1]
            break

    if verify_token:
        await client.post("/auth/verify-email", json={"token": verify_token})

    login = await client.post("/auth/login", json={
        "email": "verified@example.com",
        "password": "SecurePass1",
    })
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def unverified_client(client, mock_email):
    """Register a user (unverified) and return their email + a login attempt result."""
    await client.post("/auth/register", json={
        "email": "unverified@example.com",
        "username": "unverifieduser",
        "password": "SecurePass1",
    })
    verify_token = None
    for email_data in mock_email:
        if email_data.get("type") == "verification":
            url = email_data["url"]
            verify_token = url.split("token=")[-1]
            break
    return {"email": "unverified@example.com", "verify_token": verify_token}


@pytest_asyncio.fixture
async def auth_headers(verified_client):
    """Provide auth headers for a verified user (alias for verified_client)."""
    return verified_client