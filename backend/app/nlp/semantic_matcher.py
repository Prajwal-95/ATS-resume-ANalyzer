"""
Semantic similarity matching using Sentence Transformers.
Falls back to TF-IDF cosine similarity if sentence-transformers is not available.
"""

from typing import Optional

# Try to load sentence-transformers; fall back to sklearn
try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

_model = None


def _get_model():
    global _model
    if _model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _model = False  # Mark as failed
    return _model


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Calculate semantic similarity between two texts.
    Returns a value between 0.0 and 1.0.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0

    model = _get_model()
    if model and model is not False:
        try:
            emb_a = model.encode(text_a, convert_to_tensor=True)
            emb_b = model.encode(text_b, convert_to_tensor=True)
            similarity = util.cos_sim(emb_a, emb_b)
            return round(float(similarity[0][0]), 4)
        except Exception:
            pass

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

    # Weighted average
    scores = [v for k, v in results.items() if k != "overall" and v > 0]
    if scores:
        results["overall"] = round(sum(scores) / len(scores), 4)

    return results
