"""
Tests for PDF report generation.
"""


async def test_generate_report(client, auth_headers):
    # Create an analysis
    result = await client.post("/analysis/demo", json={
        "resume_text": "Python developer with Django and React experience",
        "job_description": "Looking for Python developer with Django and React",
    }, headers=auth_headers)
    analysis_id = result.json()["id"]

    # Download report
    response = await client.get(f"/analysis/{analysis_id}/report", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0
    # PDF files start with %PDF
    assert response.content[:4] == b"%PDF"


async def test_report_requires_auth_for_owned(client, auth_headers):
    # Create analysis as user 1
    result = await client.post("/analysis/demo", json={
        "resume_text": "Python developer",
        "job_description": "Python developer needed",
    }, headers=auth_headers)
    analysis_id = result.json()["id"]

    # Register user 2
    await client.post("/auth/register", json={
        "email": "user2@example.com",
        "username": "user2",
        "password": "securepass123",
    })
    login2 = await client.post("/auth/login", json={
        "email": "user2@example.com",
        "password": "securepass123",
    })
    token2 = login2.json()["access_token"]

    # User 2 should not access user 1's report
    response = await client.get(f"/analysis/{analysis_id}/report", headers={"Authorization": f"Bearer {token2}"})
    assert response.status_code == 403


async def test_report_not_found(client, auth_headers):
    response = await client.get("/analysis/99999/report", headers=auth_headers)
    assert response.status_code == 404


async def test_report_anonymous_analysis(client):
    """Anonymous analysis reports should be downloadable by anyone."""
    result = await client.post("/analysis/demo", json={
        "resume_text": "Python developer",
        "job_description": "Python developer needed",
    })
    analysis_id = result.json()["id"]

    response = await client.get(f"/analysis/{analysis_id}/report")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
