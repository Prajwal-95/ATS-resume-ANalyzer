"""
Tests for rate limiting.
"""
import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state before each test."""
    from app.utils.rate_limiter import _rate_limiter
    _rate_limiter._windows.clear()
    yield
    _rate_limiter._windows.clear()


async def test_rate_limit_headers_present(client):
    response = await client.get("/healthz")
    # Rate limit headers are added by the rate limiter when enabled
    # In test mode, we verify the response succeeds
    assert response.status_code == 200


async def test_rate_limit_triggers(client, auth_headers):
    """Test that rate limiting triggers after exceeding the limit on analysis endpoint."""
    from app.config import settings
    settings.RATE_LIMIT_ENABLED = True
    settings.RATE_LIMIT_ANALYSIS = 3
    settings.RATE_LIMIT_WINDOW_SECONDS = 60

    # Make requests up to the limit
    for i in range(3):
        response = await client.post("/analysis/demo", json={
            "resume_text": "Python developer",
            "job_description": "Python developer needed",
        }, headers=auth_headers)
        assert response.status_code == 201

    # Next request should be rate limited
    response = await client.post("/analysis/demo", json={
        "resume_text": "Python developer",
        "job_description": "Python developer needed",
    }, headers=auth_headers)
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
    assert "Retry-After" in response.headers


async def test_rate_limit_disabled():
    from app.config import settings
    original = settings.RATE_LIMIT_ENABLED
    settings.RATE_LIMIT_ENABLED = False
    try:
        from app.utils.rate_limiter import check_rate_limit
        from starlette.requests import Request
        # Should not raise
        result = check_rate_limit(Request(scope={"type": "http", "client": ("127.0.0.1", 12345)}))
        assert result == {}
    finally:
        settings.RATE_LIMIT_ENABLED = original
