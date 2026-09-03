import httpx
import json

jd = (
    "We are looking for a Python developer with Django experience to build REST APIs. "
    "Must know React, JavaScript, SQL, and Docker. AWS experience preferred."
)

with open("test_resume.docx", "rb") as f:
    r = httpx.post(
        "http://127.0.0.1:8000/analysis/analyze",
        files={
            "file": (
                "test_resume.docx",
                f,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"job_description": jd},
    )

print("Status:", r.status_code)
data = r.json()
if r.status_code == 201:
    print("Total score:", data.get("total_score"))
    print("Job title:", data.get("job_title"))
    print("Scores:", json.dumps(data.get("scores", {}), indent=2)[:800])
    print("Matched:", [k["keyword"] for k in data.get("matched_keywords", [])])
    print("Missing:", [k["keyword"] for k in data.get("missing_keywords", [])])
    print("Suggestions:", [s["message"][:60] for s in data.get("suggestions", [])])
    print("Analysis ID:", data.get("id"))
else:
    print("Error response:", json.dumps(data, indent=2)[:1000])
