"""
Integration tests for authentication API endpoints.
"""


async def test_register_user(client):
    response = await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepass123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "id" in data


async def test_register_duplicate_email(client):
    await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser1",
        "password": "securepass123",
    })
    response = await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser2",
        "password": "securepass123",
    })
    assert response.status_code == 400


async def test_register_short_password(client):
    response = await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "123",
    })
    assert response.status_code == 422


async def test_login_success(client):
    await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepass123",
    })
    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "securepass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client):
    await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepass123",
    })
    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


async def test_get_me(client):
    await client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepass123",
    })
    login = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "securepass123",
    })
    token = login.json()["access_token"]

    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


async def test_get_me_invalid_token(client):
    response = await client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401


async def test_get_me_malformed_authorization_header(client):
    # Wrong scheme (not Bearer) previously returned 403 from HTTPBearer;
    # it must return 401 for missing/invalid authentication credentials.
    response = await client.get("/auth/me", headers={"Authorization": "Basic some-token"})
    assert response.status_code == 401


async def test_get_me_no_token(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401


def test_password_hashed():
    """Verify password is not stored in plaintext."""
    from app.utils.auth import hash_password
    hashed = hash_password("securepass123")
    assert hashed != "securepass123"
    assert hashed.startswith("$2b$")  # bcrypt prefix
