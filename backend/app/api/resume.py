"""
Resume upload and analysis API endpoints.
"""

import logging

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.models import User
from app.utils.auth import get_current_user
from app.utils.file_handler import validate_file, save_upload, delete_file
from app.services.resume_parser import extract_resume_text, extract_sections, extract_contact_info, extract_skills_from_text
from app.schemas.schemas import ResumeUploadResponse
from app.utils.rate_limiter import check_rate_limit

logger = logging.getLogger("ats_resume_checker")

router = APIRouter()


@router.post("/upload", response_model=ResumeUploadResponse, status_code=201)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume file (PDF or DOCX) and extract its text.
    The temporary file is deleted immediately after extraction. Requires authentication.
    """
    # Rate limit
    rate_headers = check_rate_limit(request, prefix="upload", max_requests=30)

    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Validate file type, size, and content
    valid, error = validate_file(file.filename, len(content), content)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    # Save temporarily
    file_path = None
    try:
        file_path = await save_upload(content, file.filename)

        # Extract text
        text, meta = extract_resume_text(str(file_path))

        sections = extract_sections(text)
        contact = extract_contact_info(text)
        skills = extract_skills_from_text(text)

        return ResumeUploadResponse(
            filename=file.filename,
            text_preview=text[:500],
            sections=list(sections.keys()),
            contact=contact,
            skills=skills,
            metadata=meta,
        )
    except (ValueError, FileNotFoundError) as e:
        logger.warning(f"Resume parsing failed for {file.filename}: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process resume. Please try again.")
    finally:
        # Always clean up the temporary file
        if file_path:
            await delete_file(file_path)
