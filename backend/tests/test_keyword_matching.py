"""
Unit tests for keyword matching and synonym handling.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.nlp.keyword_extractor import normalize_skill, match_keywords, SKILL_SYNONYMS


def test_normalize_skill_synonyms():
    assert normalize_skill("JS") == "javascript"
    assert normalize_skill("js") == "javascript"
    assert normalize_skill("react") == "react"
    assert normalize_skill("AWS") == "amazon web services"


def test_match_keywords_direct():
    matched, missing = match_keywords("I know Python and SQL", ["Python", "Docker"])
    assert len(matched) == 1
    assert matched[0]["keyword"] == "Python"
    assert len(missing) == 1
    assert missing[0]["keyword"] == "Docker"


def test_match_keywords_synonym():
    matched, missing = match_keywords("I have used JS for web development", ["JavaScript"])
    assert len(matched) == 1
    assert matched[0]["keyword"] == "JavaScript"
    assert matched[0]["confidence"] == 0.8


def test_skill_synonym_dictionary_configurable():
    # The dictionary should be present and extendable
    assert "javascript" in SKILL_SYNONYMS
    assert "js" in SKILL_SYNONYMS["javascript"]
