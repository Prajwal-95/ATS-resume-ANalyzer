"""
Unit tests for the transparent ATS scoring engine.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.scoring.engine import ScoringEngine


def test_scoring_weights_total_100():
    """The configurable scoring weights must sum to 100."""
    engine = ScoringEngine()
    total = sum(int(w["max_score"]) for w in engine.weights.values())
    assert total == 100


def test_keyword_match_score():
    engine = ScoringEngine()
    matched = [{"keyword": "python"}, {"keyword": "sql"}]
    missing = [{"keyword": "docker"}, {"keyword": "aws"}]
    result = engine.score_keyword_match(matched, missing)
    assert result["max_score"] == 30
    assert abs(result["score"] - 15.0) < 0.01  # 2/4 matched = 50%


def test_keyword_match_no_matches():
    engine = ScoringEngine()
    result = engine.score_keyword_match([], [{"keyword": "docker"}])
    assert result["score"] == 0


def test_technical_skill_score():
    engine = ScoringEngine()
    skill_matches = [
        {"skill_name": "python", "match_type": "matched", "is_required": True},
        {"skill_name": "docker", "match_type": "missing", "is_required": True},
    ]
    result = engine.score_technical_skill(skill_matches)
    assert result["max_score"] == 25
    assert abs(result["score"] - 12.5) < 0.01


def test_experience_relevance_score():
    engine = ScoringEngine()
    result = engine.score_experience_relevance(0.8)
    assert abs(result["score"] - 16.0) < 0.01  # 0.8 * 20
    assert result["max_score"] == 20


def test_structure_score():
    engine = ScoringEngine()
    sections = ["summary", "education", "skills", "experience", "projects"]
    result = engine.score_structure(sections)
    # 5/6 sections present, rounded to 1 decimal = 8.3
    assert abs(result["score"] - 8.3) < 0.011


def test_education_score():
    engine = ScoringEngine()
    assert engine.score_education(True)["score"] == 5
    assert engine.score_education(False)["score"] == 0


def test_formatting_score_deductions():
    engine = ScoringEngine()
    issues = [
        {"status": "problem"},
        {"status": "warning"},
    ]
    result = engine.score_formatting(issues)
    # 10 - 1.5 - 0.8 = 7.7
    assert abs(result["score"] - 7.7) < 0.01


def test_total_score_calculation():
    engine = ScoringEngine()
    result = engine.calculate(
        matched=[{"keyword": "python"}],
        missing=[{"keyword": "docker"}],
        skill_matches=[
            {"skill_name": "python", "match_type": "matched", "is_required": True},
            {"skill_name": "docker", "match_type": "missing", "is_required": True},
        ],
        job_relevance=0.8,
        sections_found=["summary", "education", "skills", "experience", "projects"],
        has_education=True,
        formatting_issues=[{"status": "good"}],
    )
    assert 0 <= result["total"] <= 100
    assert result["disclaimer"]  # disclaimer must be present
