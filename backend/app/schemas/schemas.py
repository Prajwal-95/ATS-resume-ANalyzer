"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ── Auth Schemas ──

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Analysis Schemas ──

class ScoreDetail(BaseModel):
    category: str
    score: float
    max_score: float
    details: Optional[dict] = None

class KeywordItem(BaseModel):
    keyword: str
    confidence: Optional[float] = 1.0

class MissingKeywordItem(BaseModel):
    keyword: str
    importance: Optional[str] = "medium"

class SkillMatchItem(BaseModel):
    skill_name: str
    match_type: str  # matched, missing, additional
    is_required: bool = False

class SuggestionItem(BaseModel):
    category: str
    message: str
    priority: str = "medium"

class QualityIssueItem(BaseModel):
    category: str
    label: Optional[str] = None
    message: str
    status: str  # good, warning, problem

class StructuredResume(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    summary: Optional[str] = None
    education: Optional[List[dict]] = None
    skills: Optional[List[str]] = None
    experience: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None

class AnalysisResult(BaseModel):
    id: int
    resume_filename: Optional[str]
    job_title: Optional[str]
    total_score: float
    scores: List[ScoreDetail]
    matched_keywords: List[KeywordItem]
    missing_keywords: List[MissingKeywordItem]
    skill_matches: List[SkillMatchItem]
    suggestions: List[SuggestionItem]
    quality_issues: List[QualityIssueItem]
    structured_resume: Optional[StructuredResume]
    semantic_similarity: Optional[float] = None
    job_relevance: Optional[float] = None
    disclaimer: str = ""
    created_at: datetime

    class Config:
        from_attributes = True

class AnalysisHistoryItem(BaseModel):
    id: int
    resume_filename: Optional[str]
    job_title: Optional[str]
    total_score: float
    created_at: datetime

    class Config:
        from_attributes = True

class AnalysisResponse(BaseModel):
    id: int
    resume_filename: Optional[str]
    total_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeUploadResponse(BaseModel):
    filename: str
    text_preview: str
    sections: List[str]
    contact: dict
    skills: List[str]
    metadata: dict
