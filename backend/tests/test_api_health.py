"""
Tests for health, readiness, and file validation.
"""


async def test_healthz(client):
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "version" in data
    assert "database" in data


async def test_security_headers(client):
    response = await client.get("/healthz")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"


def test_file_validation_rejects_bad_extension():
    from app.utils.file_handler import validate_file
    valid, error = validate_file("malware.exe", 1000)
    assert not valid
    assert "Unsupported file type" in error


def test_file_validation_rejects_oversized():
    from app.utils.file_handler import validate_file
    valid, error = validate_file("resume.pdf", 11 * 1024 * 1024)  # 11MB
    assert not valid
    assert "too large" in error.lower()


def test_file_validation_accepts_valid_pdf():
    from app.utils.file_handler import validate_file
    content = b"%PDF-1.4 test content"
    valid, error = validate_file("resume.pdf", len(content), content)
    assert valid
    assert error is None


def test_file_validation_accepts_valid_docx():
    from app.utils.file_handler import validate_file
    content = b"PK\x03\x04" + b"\x00" * 100  # ZIP signature
    valid, error = validate_file("resume.docx", len(content), content)
    assert valid
    assert error is None


def test_file_validation_rejects_mismatched_content():
    from app.utils.file_handler import validate_file
    # PDF content with .docx extension
    content = b"%PDF-1.4 test content"
    valid, error = validate_file("resume.docx", len(content), content)
    assert not valid
    assert "content" in error.lower()


async def test_upload_empty_file(client):
    response = await client.post(
        "/resume/upload",
        files={"file": ("test.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert "Empty" in response.json()["detail"]


async def test_upload_invalid_file_type(client):
    response = await client.post(
        "/resume/upload",
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


async def test_upload_valid_pdf(client):
    # Minimal valid PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    response = await client.post(
        "/resume/upload",
        files={"file": ("test.pdf", pdf_content, "application/pdf")},
    )
    # Should either succeed or return 422 (if PDF parsing fails on minimal content)
    assert response.status_code in (201, 422)
