"""
Resume upload and analysis API endpoints.
"""

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.utils.file_handler import validate_file, save_upload, delete_file
from app.services.resume_parser import extract_resume_text
from app.schemas.schemas import AnalysisResult, AnalysisResponse

router = APIRouter()


@router.post("/upload", response_model=AnalysisResponse, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a resume file (PDF or DOCX) and extract its text.
    The temporary file is deleted immediately after extraction.
    """
    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Validate file type and size
    valid, error = validate_file(file.filename, len(content))
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    # Save temporarily
    file_path = None
    try:
        file_path = await save_upload(content, file.filename)

        # Extract text
        text, meta = extract_resume_text(str(file_path))

        return {
            "id": 0,
            "resume_filename": file.filename,
            "total_score": 0.0,
            "created_at": None,
        }
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")
    finally:
        # Always clean up the temporary file
        if file_path:
            await delete_file(file_path)
