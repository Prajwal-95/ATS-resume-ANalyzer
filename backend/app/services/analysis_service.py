"""
Core analysis service that orchestrates the full pipeline:
extraction -> skill detection -> keyword matching -> scoring -> suggestions.
"""

from typing import Optional

from app.services.resume_parser import (
    extract_sections,
    extract_contact_info,
    extract_skills_from_text,
)
from app.nlp.keyword_extractor import extract_job_keywords, match_keywords, normalize_skill, SKILL_SYNONYMS
from app.nlp.semantic_matcher import calculate_job_relevance
from app.scoring.engine import ScoringEngine
from app.scoring.weights import DISCLAIMER


def analyze_resume(resume_text: str, job_description: str, resume_filename: str = "") -> dict:
    """
    Run the full analysis pipeline and return a complete result dict.
    """
    engine = ScoringEngine()

    # 1. Extract resume structure and contact info
    sections = extract_sections(resume_text)
    contact = extract_contact_info(resume_text)
    resume_skills = extract_skills_from_text(resume_text)

    # 2. Extract job description keywords
    job_keywords = extract_job_keywords(job_description)

    # 3. Match keywords
    matched_kw, missing_kw = match_keywords(resume_text, job_keywords)

    # 4. Build skill matches
    required_skills = _detect_required_skills(job_description, job_keywords)
    skill_matches = _build_skill_matches(required_skills, resume_skills, resume_text)

    # 5. Calculate semantic job relevance
    relevance = calculate_job_relevance(
        job_description,
        resume_summary=sections.get("summary", ""),
        resume_experience=sections.get("experience", ""),
        resume_projects=sections.get("projects", ""),
    )

    # 6. Evaluate formatting / quality issues
    formatting_issues = evaluate_quality(resume_text, sections, contact)

    # 7. Run scoring engine
    scoring_result = engine.calculate(
        matched=matched_kw,
        missing=missing_kw,
        skill_matches=skill_matches,
        job_relevance=relevance.get("overall") or None,
        sections_found=list(sections.keys()),
        has_education="education" in sections,
        formatting_issues=formatting_issues,
    )

    # 8. Generate suggestions
    suggestions = generate_suggestions(
        matched_kw=matched_kw,
        missing_kw=missing_kw,
        skill_matches=skill_matches,
        sections=sections,
    )

    return {
        "resume_filename": resume_filename,
        "job_title": _guess_job_title(job_description),
        "total_score": scoring_result["total"],
        "scores": [
            {
                "category": category,
                "score": score_data["score"],
                "max_score": score_data["max_score"],
                "details": score_data.get("details"),
            }
            for category, score_data in scoring_result["scores"].items()
        ],
        "matched_keywords": matched_kw,
        "missing_keywords": missing_kw,
        "skill_matches": skill_matches,
        "suggestions": suggestions,
        "quality_issues": formatting_issues,
        "structured_resume": {
            **contact,
            "sections": sections,
            "skills": resume_skills,
        },
        "semantic_similarity": relevance.get("overall", 0.0),
        "job_relevance": relevance.get("overall", 0.0),
        "disclaimer": DISCLAIMER,
    }

def _detect_required_skills(job_description: str, keywords: list[str]) -> list[str]:
    """Identify skills strongly associated with the job description."""
    jd_lower = job_description.lower()
    required = []
    for kw in keywords:
        canonical = normalize_skill(kw)
        if kw.lower() in jd_lower:
            count = jd_lower.count(kw.lower())
            if count >= 2 or canonical in SKILL_SYNONYMS or "required" in jd_lower[:2000]:
                required.append(canonical)
    return required


def _build_skill_matches(required_skills: list[str], resume_skills: list[str], resume_text: str) -> list[dict]:
    """Categorize skills into matched / missing / additional."""
    resume_lower = resume_text.lower()
    resume_skill_set = {normalize_skill(s) for s in resume_skills}
    matches = []
    seen = set()

    for skill in required_skills:
        sk = skill
        if sk in seen:
            continue
        seen.add(sk)
        if sk in resume_skill_set or _skill_in_text(sk, resume_lower):
            matches.append({"skill_name": skill, "match_type": "matched", "is_required": True})
        else:
            matches.append({"skill_name": skill, "match_type": "missing", "is_required": True})

    for skill in resume_skills:
        sk = normalize_skill(skill)
        if sk in seen:
            continue
        seen.add(sk)
        is_required = sk in {normalize_skill(r) for r in required_skills}
        if not is_required:
            matches.append({"skill_name": skill, "match_type": "additional", "is_required": False})

    return matches


def _skill_in_text(skill: str, text_lower: str) -> bool:
    """Check if a skill (with synonyms) appears in lowercased text."""
    skill_lower = skill.lower()
    if skill_lower in text_lower:
        return True
    synonyms = SKILL_SYNONYMS.get(skill_lower, [])
    return any(syn in text_lower for syn in synonyms)


def _guess_job_title(job_description: str) -> str:
    """Extract a likely job title from the start of the job description."""
    first_lines = [l.strip() for l in job_description.split("\n") if l.strip()][:8]
    for line in first_lines:
        if len(line) < 70 and not line.lower().startswith(("about", "responsib", "requirement", "qualif", "we are", "job")):
            return line
    return ""

def evaluate_quality(text: str, sections: dict, contact: dict) -> list[dict]:
    """
    Evaluate resume formatting and quality. Returns list of issue dicts.
    """
    import re
    from collections import Counter

    issues = []
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    # Contact information
    issues.append(_issue("email", "Email address", "good" if contact.get("email") else "problem",
                         "Email found." if contact.get("email") else "Missing email address."))
    issues.append(_issue("phone", "Phone number", "good" if contact.get("phone") else "warning",
                         "Phone found." if contact.get("phone") else "No phone number detected."))

    # Standard sections
    for section, label in [("summary", "Professional summary"), ("education", "Education"),
                           ("skills", "Skills"), ("experience", "Experience"),
                           ("projects", "Projects"), ("certifications", "Certifications")]:
        present = section in sections and bool(sections[section].strip())
        status = "good" if present else ("warning" if section in ("projects", "certifications") else "problem")
        issues.append(_issue(section, label, status,
                             f"{label} section present." if present else f"{label} section not detected."))

    # Long paragraphs
    long_paragraphs = [p for p in paragraphs if len(p) > 500]
    if long_paragraphs:
        issues.append(_issue("long_paragraphs", "Very long paragraphs", "warning",
                             f"Found {len(long_paragraphs)} very long paragraph(s). Consider splitting."))
    else:
        issues.append(_issue("long_paragraphs", "Very long paragraphs", "good", "No excessively long paragraphs found."))

    # Excessive special characters
    special_chars = re.findall(r"[^\w\s.,;:()\[\]{}\"'\-/|@#+%&*=<>!?]", text)
    if len(special_chars) > 30:
        issues.append(_issue("special_chars", "Excessive special characters", "warning",
                             f"Found {len(special_chars)} special characters. This may confuse parsers."))
    else:
        issues.append(_issue("special_chars", "Special characters", "good", "Special character usage is normal."))


    # Repeated keywords
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    counts = Counter(words)
    repetitive = [w for w, c in counts.items() if c >= 8 and w not in ("that", "this", "with", "have", "from")]
    if repetitive:
        issues.append(_issue("repeated_keywords", "Repeated keywords", "warning",
                             f"Some keywords are repeated very often: {', '.join(repetitive[:5])}"))
    else:
        issues.append(_issue("repeated_keywords", "Repeated keywords", "good", "No abnormal keyword repetition."))

    # Inconsistent date formats
    verbatim_dates = re.findall(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\b", text)
    numeric_dates = re.findall(r"\b\d{1,2}[/-]\d{2,4}\b", text)
    if verbatim_dates and numeric_dates:
        issues.append(_issue("dates", "Inconsistent date formats", "warning", "Date formats are inconsistent."))
    else:
        issues.append(_issue("dates", "Date formats", "good", "Date formats look consistent."))

    # Empty sections
    empty_sections = [name for name, content in sections.items() if not content.strip()]
    if empty_sections:
        issues.append(_issue("empty_sections", "Empty sections", "problem", f"Empty/blank sections: {', '.join(empty_sections)}"))

    return issues


def _issue(category: str, label: str, status: str, message: str) -> dict:
    return {"category": category, "label": label, "status": status, "message": message}


def generate_suggestions(
    matched_kw: list[dict],
    missing_kw: list[dict],
    skill_matches: list[dict],
    sections: dict,
) -> list[dict]:
    """
    Generate actionable, evidence-based suggestions.
    Never invents experience or skills not present in the resume.
    """
    suggestions = []

    # Keyword-based suggestions
    for missing in missing_kw[:3]:
        suggestions.append({
            "category": "keyword",
            "priority": "high",
            "message": (
                f"'{missing['keyword']}' is mentioned in the job description but was not detected in your resume. "
                "If you genuinely have experience with this, consider mentioning it in the relevant "
                "project or experience section."
            ),
        })

    # Skill match suggestions
    matched_skills = [s for s in skill_matches if s["match_type"] == "matched"]
    if matched_skills:
        top = sorted(matched_skills, key=lambda s: s.get("is_required", False), reverse=True)[:3]
        names = ", ".join(s["skill_name"] for s in top)
        suggestions.append({
            "category": "skill",
            "priority": "medium",
            "message": f"Your resume contains {names}, which match important job requirements.",
        })

    # Project/experience length suggestions
    projects_content = sections.get("projects", "")
    if projects_content:
        bullet_count = sum(1 for line in projects_content.split("\n") if line.strip().startswith(("-", "•", "*")))
        if bullet_count < 3:
            suggestions.append({
                "category": "projects",
                "priority": "medium",
                "message": (
                    "Your project descriptions are fairly short. Consider describing what you built, "
                    "the technologies you used, and the measurable result for each project."
                ),
            })

    # Summary suggestion
    if "summary" not in sections:
        suggestions.append({
            "category": "summary",
            "priority": "medium",
            "message": "A professional summary at the top of your resume helps ATS systems quickly understand your profile.",
        })

    # Fallback
    if not suggestions:
        suggestions.append({
            "category": "general",
            "priority": "low",
            "message": "Your resume looks reasonable overall. Review it for clarity and ensure metrics are included where possible.",
        })

    return suggestions

