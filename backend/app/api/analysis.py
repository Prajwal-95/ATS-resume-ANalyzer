"""
Analysis API endpoints: run analysis, view history, delete analyses.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.connection import get_db
from app.models.models import (
    Analysis, AnalysisScore, MatchedKeyword, MissingKeyword,
    SkillMatch, Suggestion, QualityIssue, User,
)
from app.schemas.schemas import (
    AnalysisResult, AnalysisHistoryItem, ScoreDetail, KeywordItem,
    MissingKeywordItem, SkillMatchItem, SuggestionItem, QualityIssueItem,
)
from app.services.resume_parser import extract_resume_text
from app.services.analysis_service import analyze_resume
from app.utils.auth import get_current_user, get_optional_user
from app.utils.file_handler import validate_file, save_upload, delete_file
from app.utils.rate_limiter import check_rate_limit

logger = logging.getLogger("ats_resume_checker")

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResult, status_code=201)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    job_description: str = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a resume and job description, then run the full ATS analysis. Requires authentication."""
    # Rate limit
    from app.config import settings
    check_rate_limit(request, prefix="analysis", max_requests=settings.RATE_LIMIT_ANALYSIS)

    if not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    valid, error = validate_file(file.filename, len(content), content)
    if not valid:
        raise HTTPException(status_code=400, detail=error)

    file_path = None
    try:
        file_path = await save_upload(content, file.filename)
        resume_text, meta = extract_resume_text(str(file_path))

        # Run analysis directly (sync) to preserve async session greenlet context
        result = analyze_resume(resume_text, job_description, file.filename)

        analysis_id, created_at = await _save_analysis(db, user, file.filename, resume_text, job_description, result)
        result["id"] = analysis_id
        result["created_at"] = created_at
        return result
    except (ValueError, FileNotFoundError) as e:
        logger.warning(f"Analysis failed for {file.filename}: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")
    finally:
        if file_path:
            await delete_file(file_path)


@router.post("/demo", response_model=AnalysisResult, status_code=201)
async def analyze_demo(
    request: Request,
    payload: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run an analysis from pasted resume text (no file upload). Requires authentication.
    """
    from app.config import settings
    check_rate_limit(request, prefix="demo", max_requests=settings.RATE_LIMIT_ANALYSIS)

    resume_text = (payload.get("resume_text") or "").strip()
    job_description = (payload.get("job_description") or "").strip()

    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text cannot be empty")
    if not job_description:
        raise HTTPException(status_code=400, detail="Job description cannot be empty")

    filename = "demo-resume.txt"

    try:
        # Run analysis directly (sync) to preserve async session greenlet context
        result = analyze_resume(resume_text, job_description, filename)
        analysis_id, created_at = await _save_analysis(db, user, filename, resume_text, job_description, result)
        result["id"] = analysis_id
        result["created_at"] = created_at
        return result
    except Exception as e:
        logger.error(f"Demo analysis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again.")


@router.get("/history", response_model=List[AnalysisHistoryItem])
async def history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all previous analyses for the authenticated user."""
    result = await db.execute(
        select(Analysis).where(Analysis.user_id == user.id).order_by(Analysis.created_at.desc())
    )
    analyses = result.scalars().all()
    return [
        AnalysisHistoryItem(
            id=a.id, resume_filename=a.resume_filename, job_title=a.job_title,
            total_score=a.total_score, created_at=a.created_at,
        )
        for a in analyses
    ]


@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(
    analysis_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a full analysis result by ID.

    - Logged-in users can view their own analyses.
    - Anonymous analyses (user_id=None) are viewable by anyone (required for
      the flow: upload -> analyse -> view results without an account).
    """
    stmt = (
        select(Analysis)
        .where(Analysis.id == analysis_id)
        .options(
            selectinload(Analysis.scores),
            selectinload(Analysis.matched_keywords),
            selectinload(Analysis.missing_keywords),
            selectinload(Analysis.skill_matches),
            selectinload(Analysis.suggestions),
            selectinload(Analysis.quality_issues),
        )
    )
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Access control:
    #  - anonymous analysis (user_id=None) -> anyone can view
    #  - owned analysis -> only the owner can view
    #  - other user's analysis -> forbidden
    if analysis.user_id is not None:
        if user is None or analysis.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this analysis")

    return _build_result_from_db(analysis)


@router.delete("/{analysis_id}", status_code=204)
async def delete_analysis(
    analysis_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific analysis for the authenticated user."""
    result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this analysis")

    await db.delete(analysis)
    await db.commit()
    return None


@router.get("/{analysis_id}/report")
async def download_report(
    analysis_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a PDF report for an analysis."""
    stmt = (
        select(Analysis)
        .where(Analysis.id == analysis_id)
        .options(
            selectinload(Analysis.scores),
            selectinload(Analysis.matched_keywords),
            selectinload(Analysis.missing_keywords),
            selectinload(Analysis.skill_matches),
            selectinload(Analysis.suggestions),
            selectinload(Analysis.quality_issues),
        )
    )
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Access control: same rules as viewing
    if analysis.user_id is not None:
        if user is None or analysis.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this analysis")

    from app.services.report_generator import generate_report
    report_path = generate_report(analysis)

    return FileResponse(
        path=str(report_path),
        media_type="application/pdf",
        filename=f"ats-report-{analysis.id}.pdf",
    )


# ── Helpers ──


async def _save_analysis(db: AsyncSession, user: Optional[User], filename: str, resume_text: str, job_description: str, result: dict) -> tuple[int, datetime]:
    """Persist an analysis result to the database. Returns (analysis_id, created_at)."""
    from datetime import datetime
    analysis = Analysis(
        user_id=user.id if user else None,
        resume_filename=filename,
        resume_text=resume_text,
        job_description=job_description,
        job_title=result.get("job_title", ""),
        total_score=result["total_score"],
        structured_resume=result.get("structured_resume"),
    )
    db.add(analysis)
    await db.flush()

    analysis_id = analysis.id
    created_at = analysis.created_at

    for score_data in result["scores"]:
        db.add(AnalysisScore(
            analysis_id=analysis_id, category=score_data["category"], score=score_data["score"],
            max_score=score_data["max_score"], details=score_data.get("details"),
        ))

    for kw in result.get("matched_keywords", []):
        db.add(MatchedKeyword(analysis_id=analysis_id, keyword=kw["keyword"], confidence=kw.get("confidence", 1.0)))

    for kw in result.get("missing_keywords", []):
        db.add(MissingKeyword(analysis_id=analysis_id, keyword=kw["keyword"], importance=kw.get("importance", "medium")))

    for sm in result.get("skill_matches", []):
        db.add(SkillMatch(analysis_id=analysis_id, skill_name=sm["skill_name"], match_type=sm["match_type"], is_required=sm.get("is_required", False)))

    for sug in result.get("suggestions", []):
        db.add(Suggestion(analysis_id=analysis_id, category=sug["category"], message=sug["message"], priority=sug.get("priority", "medium")))

    for qi in result.get("quality_issues", []):
        db.add(QualityIssue(analysis_id=analysis_id, category=qi["category"], label=qi.get("label"), message=qi["message"], status=qi["status"]))

    await db.commit()
    return analysis_id, created_at


def _build_result_from_db(analysis: Analysis) -> AnalysisResult:
    """Reconstruct the full result from a database entity."""
    return AnalysisResult(
        id=analysis.id,
        resume_filename=analysis.resume_filename,
        job_title=analysis.job_title,
        total_score=analysis.total_score,
        scores=[
            ScoreDetail(category=s.category, score=s.score, max_score=s.max_score, details=s.details)
            for s in analysis.scores
        ],
        matched_keywords=[KeywordItem(keyword=k.keyword, confidence=k.confidence) for k in analysis.matched_keywords],
        missing_keywords=[MissingKeywordItem(keyword=k.keyword, importance=k.importance) for k in analysis.missing_keywords],
        skill_matches=[SkillMatchItem(skill_name=s.skill_name, match_type=s.match_type, is_required=s.is_required) for s in analysis.skill_matches],
        suggestions=[SuggestionItem(category=s.category, message=s.message, priority=s.priority) for s in analysis.suggestions],
        quality_issues=[QualityIssueItem(category=q.category, label=q.label, message=q.message, status=q.status) for q in analysis.quality_issues],
        structured_resume=analysis.structured_resume,
        created_at=analysis.created_at,
    )
