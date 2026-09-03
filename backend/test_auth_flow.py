import httpx
import json

BASE = "http://127.0.0.1:8000"

# 1. Login
r = httpx.post(f"{BASE}/auth/login", json={"email": "test@example.com", "password": "test1234"})
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("Login OK")

# 2. Authenticated analysis
jd = "We need a Senior Python developer skilled in Django, React, SQL, Docker and AWS to lead backend engineering."
with open("test_resume.docx", "rb") as f:
    r = httpx.post(
        f"{BASE}/analysis/analyze",
        files={"file": ("test_resume.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"job_description": jd},
        headers=headers,
    )
print("Analysis status:", r.status_code)
aid = r.json().get("id")
print("Analysis ID:", aid, "| total:", r.json().get("total_score"))

# 3. Check history
r = httpx.get(f"{BASE}/analysis/history", headers=headers)
print("History:", json.dumps(r.json(), indent=2))

# 4. Get specific analysis
if aid:
    r = httpx.get(f"{BASE}/analysis/{aid}", headers=headers)
    print("Get analysis:", r.status_code, "| scores count:", len(r.json().get("scores", [])))
