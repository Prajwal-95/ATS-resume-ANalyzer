"""
Unit tests for resume text parsing and section extraction.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.resume_parser import extract_sections, extract_contact_info, extract_skills_from_text

SAMPLE_RESUME = """
John Doe
john.doe@example.com | (555) 123-4567
linkedin.com/in/johndoe | github.com/johndoe

Summary
Full Stack Developer with 4 years of experience in React, Node.js, and Python.

Skills
Python, JavaScript, React, Node.js, SQL, Git, Docker

Experience

Senior Developer, TechCorp (2021 - Present)
- Built web apps with React and Node.js
- Designed REST APIs

Education

BSc Computer Science, State University
"""


def test_extract_contact_info():
    contact = extract_contact_info(SAMPLE_RESUME)
    assert contact["email"] == "john.doe@example.com"
    assert contact["name"] == "John Doe"


def test_extract_sections():
    sections = extract_sections(SAMPLE_RESUME)
    assert "summary" in sections
    assert "skills" in sections
    assert "experience" in sections
    assert "education" in sections


def test_extract_skills():
    skills = extract_skills_from_text(SAMPLE_RESUME)
    assert "Python" in skills
    assert "React" in skills
    assert "SQL" in skills
