"""
ATS Resume Score Checker — Development Launcher
Starts both the FastAPI backend and Vite frontend concurrently.

Usage:
    python run.py            # Start both backend and frontend
    python run.py --backend  # Start only the backend
    python run.py --frontend # Start only the frontend

Prerequisites:
    - Python 3.10+ with backend dependencies installed
    - Node.js 18+ with frontend dependencies installed
    - PostgreSQL running (or use Docker: docker compose up -d db)
    - Backend .env configured (cp backend/.env.example backend/.env)
"""

import argparse
import platform
import signal
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"""
{CYAN}{BOLD}===============================================
   ATS Resume Score Checker — Dev Launcher
==============================================={RESET}

  {GREEN}Backend:{RESET}  http://localhost:8000  (docs: /docs)
  {BLUE}Frontend:{RESET} http://localhost:5173
""")


def get_python_executable():
    if platform.system() == "Windows":
        venv_python = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    else:
        venv_python = BACKEND_DIR / "venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def get_npm_executable():
    if platform.system() == "Windows":
        local_npm = FRONTEND_DIR / "node_modules" / ".bin" / "npm.cmd"
    else:
        local_npm = FRONTEND_DIR / "node_modules" / ".bin" / "npm"
    if local_npm.exists():
        return str(local_npm)
    return "npm"


def check_prerequisites():
    errors = []
    if not BACKEND_DIR.exists():
        errors.append(f"{RED}X backend/ directory not found.{RESET}")
    if not FRONTEND_DIR.exists():
        errors.append(f"{RED}X frontend/ directory not found.{RESET}")
    if not Path(get_python_executable()).exists():
        errors.append(f"{YELLOW}! Python venv not found. Run: cd backend && python -m venv venv && pip install -r requirements.txt{RESET}")
    if not (FRONTEND_DIR / "node_modules").exists():
        errors.append(f"{YELLOW}! node_modules not found. Run: cd frontend && npm install{RESET}")
    if not (BACKEND_DIR / ".env").exists():
        errors.append(f"{YELLOW}! backend/.env not found. Run: cp backend/.env.example backend/.env{RESET}")
    if errors:
        print(f"\n{BOLD}{RED}Prerequisites check failed:{RESET}\n")
        for err in errors:
            print(f"  {err}\n")
        sys.exit(1)
    print(f"{GREEN}All prerequisites satisfied.{RESET}\n")


def start_backend():
    python_exe = get_python_executable()
    cmd = [python_exe, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    print(f"{GREEN}{BOLD}[Backend]{RESET} Starting FastAPI server...")
    print(f"  {GREEN}>{RESET} {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=str(BACKEND_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)


def start_frontend():
    npm_exe = get_npm_executable()
    cmd = [npm_exe, "run", "dev"]
    print(f"{BLUE}{BOLD}[Frontend]{RESET} Starting Vite dev server...")
    print(f"  {BLUE}>{RESET} {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=str(FRONTEND_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)


def main():
    parser = argparse.ArgumentParser(description="Launch ATS Resume Score Checker (backend + frontend)")
    parser.add_argument("--backend", action="store_true", help="Start only the backend server")
    parser.add_argument("--frontend", action="store_true", help="Start only the frontend dev server")
    args = parser.parse_args()

    start_both = not args.backend and not args.frontend
    processes = []

    def shutdown(signum=None, frame=None):
        print(f"\n{YELLOW}Shutting down...{RESET}")
        for name, proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except (subprocess.TimeoutExpired, OSError):
                proc.kill()
        print(f"{GREEN}All services stopped. Goodbye!{RESET}")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print_banner()
    check_prerequisites()

    if start_both or args.backend:
        processes.append(("Backend", start_backend()))
    if start_both or args.frontend:
        processes.append(("Frontend", start_frontend()))

    print(f"\n{BOLD}Press Ctrl+C to stop all services.{RESET}\n")

    try:
        while processes:
            for name, proc in list(processes):
                color = GREEN if name == "Backend" else BLUE
                line = proc.stdout.readline()
                if line:
                    print(f"{color}[{name}]{RESET} {line.rstrip()}")
                elif proc.poll() is not None:
                    print(f"{color}[{name}]{RESET} {RED}Process exited (code {proc.returncode}){RESET}")
                    processes.remove((name, proc))
    except KeyboardInterrupt:
        pass

    shutdown()


if __name__ == "__main__":
    main()

