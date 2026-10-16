"""Test the analysis pipeline against the live database."""
import asyncio
import sys
sys.path.insert(0, "F:\\ATS resume ANalyzer\\backend")

from app.config import settings
from app.database.connection import async_session
from app.services.analysis_service import analyze_resume
from app.api.analysis import _save_analysis

async def test_analysis():
    async with async_session() as db:
        try:
            resume_text = "Python developer with Django and React experience. Built REST APIs and web applications."
            job_description = "Looking for Python developer with Django, React, and AWS experience. Must know SQL and Docker."
            
            print("Running analysis...")
            result = analyze_resume(resume_text, job_description, "test.txt")
            print(f"Analysis result: score={result['total_score']}, categories={len(result['scores'])}")
            
            print("Saving to database...")
            analysis_id, created_at = await _save_analysis(
                db, None, "demo-resume.txt", resume_text, job_description, result
            )
            print(f"Saved: id={analysis_id}, created_at={created_at}")
            
            return True
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    result = asyncio.run(test_analysis())
    print(f"Success: {result}")