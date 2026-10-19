"""Integration test: start FastAPI with built frontend, verify all endpoints."""
import os
import sys
import time
import urllib.request
import urllib.error
import json
import subprocess

os.environ["FRONTEND_BUILD_DIR"] = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "frontend", "dist"
))
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_integration.db"
os.environ["ENVIRONMENT"] = "development"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["JWT_SECRET_KEY"] = "dev-secret-key-change-in-production-abc123xyz"

# Remove old test database
db_path = os.path.join(os.path.dirname(__file__), "backend", "test_integration.db")
if os.path.exists(db_path):
    try:
        os.remove(db_path)
    except PermissionError:
        print(f"Warning: Could not remove {db_path} (locked by another process). Continuing anyway.")

# Use the venv Python explicitly (the backend tests use it)
venv_python = os.path.join(os.path.dirname(__file__), "backend", "venv", "Scripts", "python.exe")
if not os.path.exists(venv_python):
    venv_python = sys.executable

print(f"Starting uvicorn backend on port 8765 using {venv_python}...")
log_path = os.path.join(os.path.dirname(__file__), "backend", "uvicorn_test.log")
with open(log_path, "w") as log_file:
    proc = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "8765"],
        cwd=os.path.join(os.path.dirname(__file__), "backend"),
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

# Poll until server is ready (up to 20 seconds)
ready = False
for i in range(40):
    time.sleep(0.5)
    if proc.poll() is not None:
        print(f"Uvicorn exited early with code {proc.returncode}")
        break
    try:
        urllib.request.urlopen("http://127.0.0.1:8765/healthz", timeout=2)
        ready = True
        print(f"Server ready after {(i+1)*0.5:.1f}s")
        break
    except Exception:
        pass

if not ready:
    print("Server did not start in time. Log output:")
    with open(log_path, "r") as f:
        print(f.read())
    proc.kill()
    sys.exit(1)

BASE = "http://127.0.0.1:8765"
results = []

def test(name, url, method="GET", body=None, headers=None):
    if headers is None:
        headers = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            code = resp.status
            data = resp.read().decode("utf-8", errors="replace")[:200]
            results.append((name, code, "OK"))
            print(f"  {name}: {code} OK  {data[:120]}")
    except urllib.error.HTTPError as e:
        code = e.code
        results.append((name, code, f"HTTP {e.reason}"))
        print(f"  {name}: {code} {e.reason}")
    except Exception as e:
        results.append((name, "ERR", str(e)))
        print(f"  {name}: ERR {e}")

print("\n=== TESTS ===")
test("healthz", f"{BASE}/healthz")
test("health", f"{BASE}/health")
test("spa_root", f"{BASE}/")
test("spa_upload", f"{BASE}/upload")
test("spa_results", f"{BASE}/results/123")
test("spa_history", f"{BASE}/history")
test("spa_login", f"{BASE}/login")
test("spa_register", f"{BASE}/register")
test("spa_fallback", f"{BASE}/some-nonexistent-route")
test("api_auth_register", f"{BASE}/auth/register", method="POST",
     body={"email": "test@example.com", "username": "testuser", "password": "SecurePass1"})
test("api_analysis_demo", f"{BASE}/analysis/demo", method="POST",
     body={"resume_text": "Test resume with Python and SQL skills",
           "job_description": "Looking for Python SQL developer"})
test("static_asset", f"{BASE}/assets/index-C0kjRs8y.js")

print("\n=== STOPPING BACKEND ===")
proc.kill()
try:
    proc.wait(timeout=5)
except subprocess.TimeoutExpired:
    pass

print("\n=== UVICORN OUTPUT (last 30 lines) ===")
time.sleep(1)  # let file handle flush
with open(log_path, "r") as f:
    lines = f.readlines()
for line in lines[-30:]:
    print(line.rstrip())

print("\n=== SUMMARY ===")
# 200 = OK, 201 = Created (correct for POST /auth/register and /analysis/demo)
SUCCESS_CODES = {200, 201}
passed = sum(1 for _, code, _ in results if code in SUCCESS_CODES)
failed = sum(1 for _, code, _ in results if code not in SUCCESS_CODES)
print(f"  Passed: {passed}/{len(results)}")
print(f"  Failed: {failed}/{len(results)}")
for name, code, status in results:
    if code not in SUCCESS_CODES:
        print(f"    - {name}: {code} {status}")

sys.exit(0 if failed == 0 else 1)