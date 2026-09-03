"""
Transparent ATS scoring engine.
Each score is calculated using clear, documented criteria.
"""

import re
from typing import Optional

from app.scoring.weights import get_scoring_weights, DISCLAIMER
from app.nlp.keyword_extractor import match_keywords, normalize_skill


class ScoringEngine:
    """Calculates transparent ATS-style scores based on defined criteria."""

    def __init__(self):
        self.weights = get_scoring_weights()

    def score_keyword_match(self, matched: list[dict], missing: list[dict]) -> dict:
        """Score 0-30 based on proportion of job keywords found."""
        max_score = self.weights["keyword_match"]["max_score"]
        total = len(matched) + len(missing)
        if total == 0:
            return {"score": 0, "max_score": max_score, "details": {"matched": 0, "missing": 0}}

        ratio = len(matched) / total
        score = round(ratio * max_score, 1)
        return {
            "score": score,
            "max_score": max_score,
            "details": {"matched": len(matched), "missing": len(missing), "match_ratio": round(ratio, 3)},
        }

    def score_technical_skill(self, skill_matches: list[dict]) -> dict:
        """Score 0-25 based on required technical skills found."""
        max_score = self.weights["technical_skill"]["max_score"]
        required = [s for s in skill_matches if s.get("is_required")]
        if not required:
            # No clearly required skills; fall back to matched skills
            matched = [s for s in skill_matches if s["match_type"] == "matched"]
            if matched:
                score = max_score * 0.8
            else:
                score = max_score * 0.4
            return {"score": round(score, 1), "max_score": max_score, "details": {"required_total": 0}}

        required_matched = [s for s in required if s["match_type"] == "matched"]
        ratio = len(required_matched) / len(required)
        score = round(ratio * max_score, 1)
        return {
            "score": score,
            "max_score": max_score,
            "details": {"required_total": len(required), "required_matched": len(required_matched)},
        }

    def score_experience_relevance(self, job_relevance: Optional[float]) -> dict:
        """Score 0-20 based on semantic relevance between JD and experience/projects."""
        max_score = self.weights["experience_relevance"]["max_score"]
        if job_relevance is None:
            return {"score": max_score * 0.5, "max_score": max_score, "details": {"relevance": None}}
        score = round(job_relevance * max_score, 1)
        return {"score": score, "max_score": max_score, "details": {"relevance": job_relevance}}

    def score_structure(self, sections_found: list[str]) -> dict:
        """Score 0-10 based on standard resume sections present."""
        max_score = self.weights["structure"]["max_score"]
        required_sections = ["summary", "education", "skills", "experience", "projects", "certifications"]
        found_count = sum(1 for s in required_sections if s in sections_found)
        ratio = found_count / len(required_sections)
        score = round(ratio * max_score, 1)
        return {"score": score, "max_score": max_score, "details": {"sections_found": sections_found}}

    def score_education(self, has_education: bool) -> dict:
        """Score 0-5 based on education presence."""
        max_score = self.weights["education"]["max_score"]
        score = max_score if has_education else 0
        return {"score": score, "max_score": max_score, "details": {"has_education": has_education}}

    def score_formatting(self, issues: list[dict]) -> dict:
        """Score 0-10 based on detected formatting/parsing issues."""
        max_score = self.weights["formatting"]["max_score"]
        # Start with full marks, deduct for problems
        score = max_score
        deductions = {
            "problem": 1.5,
            "warning": 0.8,
        }
        for issue in issues:
            status = issue.get("status", "")
            if status in deductions:
                score -= deductions[status]
        score = max(0, round(score, 1))
        return {"score": score, "max_score": max_score, "details": {"issues_count": len(issues)}}

    def calculate(
        self,
        *,
        matched: list[dict],
        missing: list[dict],
        skill_matches: list[dict],
        job_relevance: Optional[float],
        sections_found: list[str],
        has_education: bool,
        formatting_issues: list[dict],
    ) -> dict:
        """Run the full scoring engine. Returns dict of category scores plus total."""
        results = {}

        results["keyword_match"] = self.score_keyword_match(matched, missing)
        results["technical_skill"] = self.score_technical_skill(skill_matches)
        results["experience_relevance"] = self.score_experience_relevance(job_relevance)
        results["structure"] = self.score_structure(sections_found)
        results["education"] = self.score_education(has_education)
        results["formatting"] = self.score_formatting(formatting_issues)

        total = sum(s["score"] for s in results.values())
        total = round(max(0, min(100, total)), 1)

        return {
            "scores": results,
            "total": total,
            "disclaimer": DISCLAIMER,
        }
