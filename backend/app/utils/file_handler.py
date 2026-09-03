"""
Secure file handling utilities.
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "10")) * 1024 * 1024  # Default 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_file(filename: str, file_size: int) -> tuple[bool, Optional[str]]:
    """Validate uploaded file type and size."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Allowed types: PDF, DOCX."
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        return False, f"File too large. Maximum size is {max_mb} MB."
    return True, None


def get_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent collisions."""
    ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


async def save_upload(file_content: bytes, original_filename: str) -> Path:
    """Save an uploaded file and return the path."""
    unique_name = get_unique_filename(original_filename)
    file_path = UPLOAD_DIR / unique_name
    file_path.write_bytes(file_content)
    return file_path


async def delete_file(file_path: Path) -> bool:
    """Safely delete a file."""
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except OSError:
        return False


async def cleanup_old_files(max_age_hours: int = 24) -> int:
    """Delete upload files older than max_age_hours."""
    deleted = 0
    import time
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            if file_path.stat().st_mtime < cutoff:
                await delete_file(file_path)
                deleted += 1
    return deleted
