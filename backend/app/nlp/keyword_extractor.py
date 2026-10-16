"""
Keyword extraction from job descriptions and resumes.
Uses spaCy for NER and noun phrase extraction, plus TF-IDF for importance ranking.
"""

import re
from collections import Counter
from typing import Optional

# spaCy is optional; falls back to TF-IDF if not installed
try:
    import spacy
except ImportError:
    spacy = None

# Load spaCy model (small English model for efficiency)
if spacy is not None:
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        nlp = None
else:
    nlp = None


# ── Configurable Skill Synonym Dictionary ──
SKILL_SYNONYMS: dict[str, list[str]] = {
    "javascript": ["js", "ecmascript", "es6", "es2015"],
    "typescript": ["ts"],
    "python": ["py"],
    "react": ["reactjs", "react.js"],
    "vue": ["vuejs", "vue.js"],
    "angular": ["angularjs", "angular.js"],
    "node.js": ["nodejs", "node"],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "c sharp"],
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "natural language processing": ["nlp"],
    "artificial intelligence": ["ai"],
    "continuous integration": ["ci"],
    "continuous deployment": ["cd"],
    "ci/cd": ["cicd", "ci cd", "continuous integration/continuous deployment"],
    "amazon web services": ["aws"],
    "google cloud platform": ["gcp", "google cloud"],
    "microsoft azure": ["azure"],
    "structured query language": ["sql"],
    "hyper text markup language": ["html"],
    "cascading style sheets": ["css"],
    "rest api": ["restful api", "rest", "restful"],
    "graphql": ["graph ql"],
    "object-oriented programming": ["oop"],
}

# Build reverse lookup
_SYNONYM_TO_CANONICAL: dict[str, str] = {}
for canonical, synonyms in SKILL_SYNONYMS.items():
    _SYNONYM_TO_CANONICAL[canonical.lower()] = canonical.lower()
    for syn in synonyms:
        _SYNONYM_TO_CANONICAL[syn.lower()] = canonical.lower()


def normalize_skill(skill: str) -> str:
    """Normalize a skill name using the synonym dictionary."""
    lower = skill.lower().strip()
    return _SYNONYM_TO_CANONICAL.get(lower, lower)


def extract_keywords_tfidf(documents: list[str], top_n: int = 30) -> list[tuple[str, float]]:
    """
    Extract top keywords from a set of documents using TF-IDF.
    Returns list of (keyword, importance_score) tuples.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    if not documents or all(not d.strip() for d in documents):
        return []

    vectorizer = TfidfVectorizer(
        max_features=200,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.95,
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        return []

    feature_names = vectorizer.get_feature_names_out()

    # Sum TF-IDF scores across all documents
    import numpy as np
    scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()
    top_indices = scores.argsort()[::-1][:top_n]

    keywords = []
    for idx in top_indices:
        kw = feature_names[idx]
        score = float(scores[idx])
        # Skip pure stopwords / very short tokens
        if len(kw) > 1:
            keywords.append((kw, round(score, 4)))

    return keywords


def extract_entities(text: str) -> list[str]:
    """Extract named entities and noun phrases using spaCy."""
    if nlp is None:
        return []

    doc = nlp(text)
    entities = set()

    # Named entities
    for ent in doc.ents:
        if ent.label_ in ("ORG", "PRODUCT", "TECH", "SKILL"):
            entities.add(ent.text.strip())

    # Noun chunks (often contain skill names)
    for chunk in doc.noun_chunks:
        clean = chunk.text.strip().lower()
        if len(clean) > 1 and len(clean) < 40:
            entities.add(chunk.text.strip())

    return sorted(entities)


def extract_job_keywords(job_description: str) -> list[str]:
    """
    Extract important keywords from a job description.
    Combines TF-IDF with entity extraction.
    """
    keywords = []

    # TF-IDF approach
    tfidf_kw = extract_keywords_tfidf([job_description], top_n=40)
    keywords.extend([kw for kw, _ in tfidf_kw])

    # Entity extraction
    entities = extract_entities(job_description)
    keywords.extend(entities)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for kw in keywords:
        normalized = normalize_skill(kw)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(kw)

    return unique


def match_keywords(resume_text: str, job_keywords: list[str]) -> tuple[list[dict], list[dict]]:
    """
    Match job description keywords against resume text.
    Uses word-boundary matching to avoid false substring matches
    (e.g., "Java" should not match "JavaScript").
    Returns (matched, missing) lists.
    """
    resume_lower = resume_text.lower()
    matched = []
    missing = []

    for kw in job_keywords:
        kw_lower = kw.lower().strip()
        # Word-boundary direct match
        if _word_boundary_match(kw_lower, resume_lower):
            matched.append({"keyword": kw, "confidence": 1.0})
            continue

        # Synonym match
        canonical = normalize_skill(kw)
        synonyms = SKILL_SYNONYMS.get(canonical, []) + [canonical]
        found = False
        for syn in synonyms:
            if _word_boundary_match(syn.lower(), resume_lower):
                matched.append({"keyword": kw, "confidence": 0.8})
                found = True
                break

        if not found:
            missing.append({"keyword": kw, "importance": "high"})

    return matched, missing


def _word_boundary_match(keyword: str, text: str) -> bool:
    """
    Check if keyword appears in text with word boundaries.
    Handles multi-word keywords like "machine learning" and "node.js".
    """
    # Escape special regex chars in keyword
    escaped = re.escape(keyword)
    # For multi-word keywords, match as phrase with word boundaries at ends
    if " " in keyword:
        pattern = r'\b' + escaped.replace(r'\ ', r'\s+') + r'\b'
    else:
        # For single words, use word boundaries
        pattern = r'\b' + escaped + r'\b'
    return bool(re.search(pattern, text, re.IGNORECASE))
