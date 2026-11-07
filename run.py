#!/usr/bin/env python3
"""
ClauseLens Cross-Platform Task Runner
Use this on Windows, macOS, or Linux where 'make' is not installed.

Usage:
    python run.py test       - Run all 16 backend unit & integration tests
    python run.py eval       - Run benchmark evaluation harness and verify targets
    python run.py lint       - Run ruff linter check
    python run.py build      - Build production frontend assets
    python run.py dev-backend - Start FastAPI server on http://localhost:8000
    python run.py dev-frontend - Start Vite frontend on http://localhost:5173
    python run.py dev        - Start both backend and frontend concurrently
"""

import sys
import subprocess
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def run(cmd: str, cwd: str = ROOT, check: bool = True):
    print(f"\n[ClauseLens Runner] >> {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    if check and res.returncode != 0:
        sys.exit(res.returncode)
    return res.returncode


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    task = sys.argv[1].lower()

    py = f'"{sys.executable}"'

    if task == "test":
        run(f"{py} -m pytest backend/tests -v")

    elif task == "eval":
        run(f"{py} -m backend.eval.run_eval")

    elif task == "lint":
        run(f"{py} -m ruff check backend/")

    elif task == "build":
        frontend_dir = os.path.join(ROOT, "frontend")
        run("npm run build", cwd=frontend_dir)

    elif task == "dev-backend":
        run(f"{py} -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload")

    elif task == "dev-frontend":
        frontend_dir = os.path.join(ROOT, "frontend")
        run("npm run dev", cwd=frontend_dir)

    elif task == "dev":
        print("\nStarting ClauseLens backend and frontend concurrently...")
        frontend_dir = os.path.join(ROOT, "frontend")
        p_back = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
            cwd=ROOT
        )
        try:
            subprocess.run("npm run dev", shell=True, cwd=frontend_dir)
        finally:
            p_back.terminate()

    elif task == "install":
        run(f"{py} -m pip install -r backend/requirements.txt")
        frontend_dir = os.path.join(ROOT, "frontend")
        run("npm install", cwd=frontend_dir)

    else:
        print(f"Unknown task: '{task}'")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
