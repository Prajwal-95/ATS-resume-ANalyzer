"""
Secure file handling utilities.
Validates file magic bytes (not just extension), enforces size limits,
generates server-controlled UUID filenames, and cleans up temp files.
"""
import os
import uuid
import asyncio
import logging
import time
from pathlib import Path
from typing import Optional

from app.config import settings

logger = logging.getLogger("ats_resume_checker")

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# Magic bytes for file type validation
MAGIC_BYTES = {
    b"%PDF": ".pdf",           # PDF files start with %PDF
    b"PK\x03\x04": ".docx",     # DOCX is a ZIP archive (PK zip signature)
}

# Ensure upload directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_file(filename: str, file_size: int, content: Optional[bytes] = None) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file type and size.
    If content is provided, also validates magic bytes.
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Allowed types: PDF, DOCX."
    if file_size > settings.max_file_size_bytes:
        return False, f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB} MB."
    if content is not None:
        detected = _detect_file_type(content)
        if detected is None:
            return False, "File content does not match a supported format (PDF or DOCX)."
        if detected != ext:
            return False, f"File content appears to be {detected} but extension is {ext}."
    return True, None


def _detect_file_type(content: bytes) -> Optional[str]:
    """Detect file type from magic bytes."""
    for magic, ext in MAGIC_BYTES.items():
        if content[:len(magic)] == magic:
            return ext
    return None


def get_unique_filename(original_filename: str) -> str:
    """Generate a unique filename to prevent collisions."""
    ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


async def save_upload(file_content: bytes, original_filename: str) -> Path:
    """Save an uploaded file and return the path."""
    unique_name = get_unique_filename(original_filename)
    file_path = settings.UPLOAD_DIR / unique_name
    file_path.write_bytes(file_content)
    logger.debug(f"Saved upload: {unique_name} ({len(file_content)} bytes)")
    return file_path


async def delete_file(file_path: Path) -> bool:
    """Safely delete a file."""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Deleted temp file: {file_path.name}")
            return True
        return False
    except OSError as e:
        logger.warning(f"Failed to delete temp file {file_path}: {e}")
        return False


async def cleanup_old_files(max_age_hours: int = 24) -> int:
    """Delete upload files older than max_age_hours."""
    deleted = 0
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    for file_path in settings.UPLOAD_DIR.iterdir():
        if file_path.is_file():
            if file_path.stat().st_mtime < cutoff:
                await delete_file(file_path)
                deleted += 1
    if deleted:
        logger.info(f"Cleaned up {deleted} old upload file(s)")
    return deleted
