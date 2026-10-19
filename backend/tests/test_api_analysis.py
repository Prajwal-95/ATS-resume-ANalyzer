"""
Integration tests for analysis API endpoints.
"""


async def test_demo_analysis(client):
    response = await client.post("/analysis/demo", json={
        "resume_text": "Python developer with experience in Django and React",
        "job_description": "Looking for a Python developer with Django and React experience",
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "total_score" in data
    assert 0 <= data["total_score"] <= 100
    assert len(data["scores"]) == 6
    assert data["disclaimer"]


async def test_demo_empty_resume(client):
    response = await client.post("/analysis/demo", json={
        "resume_text": "",
        "job_description": "Some job description",
    })
    assert response.status_code == 400


async def test_demo_empty_job_description(client):
    response = await client.post("/analysis/demo", json={
        "resume_text": "Some resume text",
        "job_description": "",
    })
    assert response.status_code == 400


async def test_analysis_history(client, auth_headers):
    # Create an analysis first
    await client.post("/analysis/demo", json={
        "resume_text": "Python developer",
        "job_description": "Python developer needed",
    }, headers=auth_headers)

    response = await client.get("/analysis/history", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["total_score"] > 0


async def test_history_requires_auth(client):
    response = await client.get("/analysis/history")
    assert response.status_code == 401


async def test_get_analysis(client, auth_headers):
    # Create analysis
    result = await client.post("/analysis/demo", json={
        "resume_text": "Python developer",
        "job_description": "Python developer needed",
    }, headers=auth_headers)
    analysis_id = result.json()["id"]

    # Retrieve it
    response = await client.get(f"/analysis/{analysis_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == analysis_id
    assert "scores" in data


async def test_get_analysis_not_found(client, auth_headers):
    response = await client.get("/analysis/99999", headers=auth_headers)
    assert response.status_code == 404


async def test_delete_analysis(client, auth_headers):
    # Create analysis
    result = await client.post("/analysis/demo", json={
        "resume_text": "Python developer",
        "job_description": "Python developer needed",
    }, headers=auth_headers)
    analysis_id = result.json()["id"]

    # Delete it
    response = await client.delete(f"/analysis/{analysis_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone
    response = await client.get(f"/analysis/{analysis_id}", headers=auth_headers)
    assert response.status_code == 404


async def test_user_isolation(client, mock_email):
    """Users should not see each other's analyses."""
    # Register user 1
    await client.post("/auth/register", json={
        "email": "user1@example.com",
        "username": "user1",
        "password": "SecurePass1",
    })
    # Get verification token for user 1
    verify_token1 = None
    for email_data in mock_email:
        if email_data.get("type") == "verification":
            url = email_data["url"]
            verify_token1 = url.split("token=")[-1]
            break
    assert verify_token1
    await client.post("/auth/verify-email", json={"token": verify_token1})
    
    login1 = await client.post("/auth/login", json={
        "email": "user1@example.com",
        "password": "SecurePass1",
    })
    token1 = login1.json()["access_token"]

    # Clear mock emails for user 2
    mock_email.clear()

    # Register user 2
    await client.post("/auth/register", json={
        "email": "user2@example.com",
        "username": "user2",
        "password": "SecurePass1",
    })
    # Get verification token for user 2
    verify_token2 = None
    for email_data in mock_email:
        if email_data.get("type") == "verification":
            url = email_data["url"]
            verify_token2 = url.split("token=")[-1]
            break
    assert verify_token2
    await client.post("/auth/verify-email", json={"token": verify_token2})

    login2 = await client.post("/auth/login", json={
        "email": "user2@example.com",
        "password": "SecurePass1",
    })
    token2 = login2.json()["access_token"]

    # User 1 creates analysis
    result = await client.post("/analysis/demo", json={
        "resume_text": "Python developer",
        "job_description": "Python developer needed",
    }, headers={"Authorization": f"Bearer {token1}"})
    analysis_id = result.json()["id"]

    # User 2 should not see it in history
    response = await client.get("/analysis/history", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 200
    assert len(response.json()) == 0

    # User 2 should not be able to access it directly
    response = await client.get(f"/analysis/{analysis_id}", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 403


async def test_anonymous_analysis_public(client):
    """Anonymous analyses should be viewable by anyone."""
    result = await client.post("/analysis/demo", json={
        "resume_text": "Python developer",
        "job_description": "Python developer needed",
    })
    analysis_id = result.json()["id"]

    # Anyone can view it
    response = await client.get(f"/analysis/{analysis_id}")
    assert response.status_code == 200
    assert response.json()["id"] == analysis_id
