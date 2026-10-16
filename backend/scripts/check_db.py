import sqlite3
conn = sqlite3.connect('ats_resume_checker.db')
cursor = conn.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = [r[0] for r in cursor.fetchall()]
print('Tables:', tables)
conn.close()