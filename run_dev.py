"""
NMC SERVER - Local Development Runner
Starts FastAPI Backend (port 8000) and Vite React Frontend (port 5173) concurrently.
"""
import os
import sys
import subprocess
import time

def main():
    print("=" * 65)
    print("  NMC SERVER — Automated Discord Registration & Role System")
    print("=" * 65)

    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

    # Set PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = backend_dir

    print("\n[1/2] Starting FastAPI Backend on http://localhost:8000...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=os.path.dirname(__file__), env=env)

    print("[2/2] Starting React Frontend on http://localhost:5173...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    frontend_cmd = [npm_cmd, "run", "dev"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=frontend_dir)

    print("\n" + "=" * 65)
    print("  Portal is running:")
    print("  -> Website Frontend: http://localhost:5173")
    print("  -> Backend API docs: http://localhost:8000/docs")
    print("=" * 65 + "\n")

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()

if __name__ == "__main__":
    main()
