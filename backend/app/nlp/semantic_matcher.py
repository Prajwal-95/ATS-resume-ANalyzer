"""
Semantic similarity matching using Sentence Transformers.
Model is loaded once at application startup and reused across requests.
Falls back to TF-IDF cosine similarity if the model is unavailable.
"""
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger("ats_resume_checker")

# Try to load sentence-transformers
try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not installed; using TF-IDF fallback")

_model = None
_model_loaded = False
_model_failed = False


def initialize_model() -> bool:
    """
    Load the Sentence Transformer model. Called once at application startup.
    Returns True if model loaded successfully, False otherwise.
    """
    global _model, _model_loaded, _model_failed

    # Use TF-IDF fallback to avoid greenlet issues with Sentence Transformer threading
    logger.info("Using TF-IDF fallback for semantic matching (Sentence Transformer disabled)")
    _model_failed = True
    return False


def is_model_ready() -> bool:
    """Check if the Sentence Transformer model is loaded and ready."""
    return _model_loaded and _model is not None


def _get_model():
    """Get the loaded model, or None if not available."""
    if _model_loaded and _model is not None:
        return _model
    return None


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Calculate semantic similarity between two texts.
    Returns a value between 0.0 and 1.0.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0

    model = _get_model()
    if model is not None:
        try:
            emb_a = model.encode(text_a, convert_to_tensor=True)
            emb_b = model.encode(text_b, convert_to_tensor=True)
            similarity = util.cos_sim(emb_a, emb_b)
            return round(float(similarity[0][0]), 4)
        except Exception as e:
            logger.warning(f"Sentence Transformer inference failed: {e}")

    # Fallback: TF-IDF cosine similarity
    return _tfidf_similarity(text_a, text_b)


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    """Fallback similarity using TF-IDF + cosine."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform([text_a, text_b])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])
        return round(float(sim[0][0]), 4)
    except Exception:
        return 0.0


def calculate_job_relevance(
    job_description: str,
    resume_summary: str = "",
    resume_experience: str = "",
    resume_projects: str = "",
) -> dict:
    """
    Calculate overall job-relevance by comparing the job description
    against different sections of the resume.
    Returns dict with individual and overall similarity scores.
    """
    results = {
        "overall": 0.0,
        "summary_similarity": 0.0,
        "experience_similarity": 0.0,
        "projects_similarity": 0.0,
    }

    jd_clean = " ".join(job_description.split())[:2000]

    if resume_summary:
        s = semantic_similarity(jd_clean, " ".join(resume_summary.split())[:2000])
        results["summary_similarity"] = s

    if resume_experience:
        e = semantic_similarity(jd_clean, " ".join(resume_experience.split())[:2000])
        results["experience_similarity"] = e

    if resume_projects:
        p = semantic_similarity(jd_clean, " ".join(resume_projects.split())[:2000])
        results["projects_similarity"] = p

    # Weighted average: experience counts more than summary/projects
    weights = []
    scores = []
    if results["experience_similarity"] > 0:
        weights.append(0.5)
        scores.append(results["experience_similarity"])
    if results["summary_similarity"] > 0:
        weights.append(0.25)
        scores.append(results["summary_similarity"])
    if results["projects_similarity"] > 0:
        weights.append(0.25)
        scores.append(results["projects_similarity"])

    if scores:
        total_weight = sum(weights)
        results["overall"] = round(sum(w * s for w, s in zip(weights, scores)) / total_weight, 4)

    return results
