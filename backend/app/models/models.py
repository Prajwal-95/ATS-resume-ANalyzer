"""
SQLAlchemy database models.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    ForeignKey, JSON, Boolean, Index
)
from sqlalchemy.orm import relationship
from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    resume_filename = Column(String(500))
    resume_text = Column(Text)
    job_description = Column(Text)
    job_title = Column(String(500), nullable=True)
    total_score = Column(Float, default=0)
    structured_resume = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analyses")
    scores = relationship("AnalysisScore", back_populates="analysis", cascade="all, delete-orphan")
    matched_keywords = relationship("MatchedKeyword", back_populates="analysis", cascade="all, delete-orphan")
    missing_keywords = relationship("MissingKeyword", back_populates="analysis", cascade="all, delete-orphan")
    skill_matches = relationship("SkillMatch", back_populates="analysis", cascade="all, delete-orphan")
    suggestions = relationship("Suggestion", back_populates="analysis", cascade="all, delete-orphan")
    quality_issues = relationship("QualityIssue", back_populates="analysis", cascade="all, delete-orphan")


class AnalysisScore(Base):
    __tablename__ = "analysis_scores"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    score = Column(Float, default=0)
    max_score = Column(Float, default=0)
    details = Column(JSON, nullable=True)

    analysis = relationship("Analysis", back_populates="scores")


class MatchedKeyword(Base):
    __tablename__ = "matched_keywords"
    __table_args__ = (
        Index("idx_matched_kw_analysis", "analysis_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    keyword = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0)

    analysis = relationship("Analysis", back_populates="matched_keywords")


class MissingKeyword(Base):
    __tablename__ = "missing_keywords"
    __table_args__ = (
        Index("idx_missing_kw_analysis", "analysis_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    keyword = Column(String(255), nullable=False)
    importance = Column(String(50), default="medium")

    analysis = relationship("Analysis", back_populates="missing_keywords")


class SkillMatch(Base):
    __tablename__ = "skill_matches"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False)
    match_type = Column(String(50), nullable=False)  # matched, missing, additional
    is_required = Column(Boolean, default=False)

    analysis = relationship("Analysis", back_populates="skill_matches")


class Suggestion(Base):
    __tablename__ = "suggestions"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(50), default="medium")  # high, medium, low

    analysis = relationship("Analysis", back_populates="suggestions")


class QualityIssue(Base):
    __tablename__ = "quality_issues"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)  # good, warning, problem

    analysis = relationship("Analysis", back_populates="quality_issues")
