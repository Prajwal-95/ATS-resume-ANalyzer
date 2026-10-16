"""Verify migration created all expected tables and indexes."""
import sqlite3
import sys
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "test_migration.db"
if not db_path.exists():
    print(f"Database not found: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(str(db_path))
tables = [
    r[0]
    for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
]
indexes = [
    r[0]
    for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name")
]
conn.close()

expected_tables = ["analyses", "analysis_scores", "matched_keywords", "missing_keywords",
                   "quality_issues", "skill_matches", "suggestions", "users"]
missing = [t for t in expected_tables if t not in tables]
print(f"Tables: {tables}")
print(f"Indexes: {indexes}")
if missing:
    print(f"MISSING TABLES: {missing}")
    sys.exit(1)
print("All expected tables present.")
