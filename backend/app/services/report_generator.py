"""
PDF report generation using PyMuPDF.
Generates a downloadable analysis report from persisted analysis results.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pymupdf as fitz

from app.config import settings

logger = logging.getLogger("ats_resume_checker")

# Ensure report directory exists
settings.REPORT_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_LABELS = {
    "keyword_match": "Keyword Match",
    "technical_skill": "Technical Skills",
    "experience_relevance": "Experience Relevance",
    "structure": "Structure",
    "education": "Education",
    "formatting": "Formatting",
}


def generate_report(analysis, output_path: Optional[Path] = None) -> Path:
    """
    Generate a PDF report for an analysis result.
    Returns the path to the generated PDF.
    """
    if output_path is None:
        filename = f"ats-report-{analysis.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        output_path = settings.REPORT_DIR / filename

    doc = fitz.open()

    # ── Page 1: Header + Score ──
    page = doc.new_page(width=612, height=792)  # US Letter
    y = 50

    # Title
    page.insert_text((50, y), "ATS Resume Score Report", fontsize=20, fontname="helv")
    y += 30
    page.insert_text((50, y), f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", fontsize=10, fontname="helv")
    y += 20
    page.insert_text((50, y), f"Resume: {analysis.resume_filename or 'N/A'}", fontsize=10, fontname="helv")
    y += 15
    if analysis.job_title:
        page.insert_text((50, y), f"Job: {analysis.job_title}", fontsize=10, fontname="helv")
        y += 25

    # Score
    page.insert_text((50, y), f"Overall Score: {analysis.total_score:.1f} / 100", fontsize=16, fontname="helv")
    y += 30

    # Category scores
    page.insert_text((50, y), "Category Breakdown", fontsize=13, fontname="helv")
    y += 20
    for score in analysis.scores:
        label = CATEGORY_LABELS.get(score.category, score.category)
        page.insert_text((70, y), f"{label}: {score.score:.1f} / {score.max_score:.1f}", fontsize=10, fontname="helv")
        y += 16

    y += 15

    # ── Keywords ──
    if y > 700:
        page = doc.new_page(width=612, height=792)
        y = 50

    page.insert_text((50, y), "Keyword Analysis", fontsize=13, fontname="helv")
    y += 20

    matched = [k.keyword for k in analysis.matched_keywords]
    missing = [k.keyword for k in analysis.missing_keywords]

    if matched:
        page.insert_text((70, y), f"Matched Keywords ({len(matched)}):", fontsize=10, fontname="helv")
        y += 15
        for kw in matched[:20]:
            page.insert_text((90, y), f"- {kw}", fontsize=9, fontname="helv")
            y += 13
        y += 5

    if missing:
        if y > 700:
            page = doc.new_page(width=612, height=792)
            y = 50
        page.insert_text((70, y), f"Missing Keywords ({len(missing)}):", fontsize=10, fontname="helv")
        y += 15
        for kw in missing[:20]:
            page.insert_text((90, y), f"- {kw}", fontsize=9, fontname="helv")
            y += 13

    # ── Skills ──
    if y > 650:
        page = doc.new_page(width=612, height=792)
        y = 50

    page.insert_text((50, y), "Technical Skills", fontsize=13, fontname="helv")
    y += 20

    skill_matched = [s.skill_name for s in analysis.skill_matches if s.match_type == "matched"]
    skill_missing = [s.skill_name for s in analysis.skill_matches if s.match_type == "missing"]
    skill_additional = [s.skill_name for s in analysis.skill_matches if s.match_type == "additional"]

    if skill_matched:
        page.insert_text((70, y), "Matched:", fontsize=10, fontname="helv")
        y += 15
        for s in skill_matched[:15]:
            page.insert_text((90, y), f"- {s}", fontsize=9, fontname="helv")
            y += 13
        y += 5

    if skill_missing:
        if y > 700:
            page = doc.new_page(width=612, height=792)
            y = 50
        page.insert_text((70, y), "Missing:", fontsize=10, fontname="helv")
        y += 15
        for s in skill_missing[:15]:
            page.insert_text((90, y), f"- {s}", fontsize=9, fontname="helv")
            y += 13
        y += 5

    if skill_additional:
        if y > 700:
            page = doc.new_page(width=612, height=792)
            y = 50
        page.insert_text((70, y), "Additional:", fontsize=10, fontname="helv")
        y += 15
        for s in skill_additional[:15]:
            page.insert_text((90, y), f"- {s}", fontsize=9, fontname="helv")
            y += 13

    # ── Quality Issues ──
    if y > 650:
        page = doc.new_page(width=612, height=792)
        y = 50

    page.insert_text((50, y), "Resume Quality", fontsize=13, fontname="helv")
    y += 20

    for issue in analysis.quality_issues:
        if y > 720:
            page = doc.new_page(width=612, height=792)
            y = 50
        status_marker = {"good": "[OK]", "warning": "[!]", "problem": "[X]"}.get(issue.status, "[?]")
        page.insert_text((70, y), f"{status_marker} {issue.message}", fontsize=9, fontname="helv")
        y += 14

    # ── Suggestions ──
    if y > 650:
        page = doc.new_page(width=612, height=792)
        y = 50

    page.insert_text((50, y), "Recommendations", fontsize=13, fontname="helv")
    y += 20

    for i, sug in enumerate(analysis.suggestions, 1):
        if y > 720:
            page = doc.new_page(width=612, height=792)
            y = 50
        page.insert_text((70, y), f"{i}. [{sug.category.upper()}] {sug.message}", fontsize=9, fontname="helv")
        y += 14

    # ── Methodology + Disclaimer ──
    page = doc.new_page(width=612, height=792)
    y = 50
    page.insert_text((50, y), "Scoring Methodology", fontsize=13, fontname="helv")
    y += 20
    methodology = (
        "This report was generated by the ATS Resume Score Checker. "
        "The scoring engine evaluates resumes across six categories: "
        "Keyword Match (30 pts), Technical Skills (25 pts), Experience Relevance (20 pts), "
        "Structure (10 pts), Education (5 pts), and Formatting (10 pts). "
        "Keyword matching uses TF-IDF and synonym detection. "
        "Semantic relevance is calculated using Sentence Transformers. "
        "The total score is an ATS-style compatibility estimate."
    )
    for line in _wrap_text(methodology, 85):
        page.insert_text((50, y), line, fontsize=9, fontname="helv")
        y += 13

    y += 20
    page.insert_text((50, y), "Disclaimer", fontsize=13, fontname="helv")
    y += 20
    disclaimer = (
        "This score is an ATS-style compatibility estimate generated by our analyzer. "
        "Every ATS system is different and many use proprietary algorithms. "
        "This result should not be treated as the exact score any employer's ATS would produce. "
        "Use this as a guide, not a guarantee."
    )
    for line in _wrap_text(disclaimer, 85):
        page.insert_text((50, y), line, fontsize=9, fontname="helv")
        y += 13

    doc.save(str(output_path))
    doc.close()
    logger.info(f"Generated report: {output_path}")
    return output_path


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """Simple text wrapping."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_chars:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        lines.append(current)
    return lines
