"""
KnowSphere All-in-One Local Runner
Starts Backend (FastAPI) and Frontend (Vite/React) natively with a single command.
No Docker or Neo4j container required.
"""
import os
import sys
import time
import signal
import shutil
import subprocess
import threading
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "data"

# Find Python executable
def get_python_executable() -> str:
    if os.name == "nt":
        venv_py = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
        if venv_py.exists():
            return str(venv_py)
    else:
        venv_py = ROOT_DIR / ".venv" / "bin" / "python"
        if venv_py.exists():
            return str(venv_py)
    return sys.executable

# Find npm / npx
def get_npm_cmd() -> str:
    npm_path = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    return npm_path or "npm"

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def print_banner():
    cyan = "\033[96m" if os.name != "nt" or "WT_SESSION" in os.environ or "TERM" in os.environ else ""
    green = "\033[92m" if os.name != "nt" or "WT_SESSION" in os.environ or "TERM" in os.environ else ""
    yellow = "\033[93m" if os.name != "nt" or "WT_SESSION" in os.environ or "TERM" in os.environ else ""
    reset = "\033[0m" if os.name != "nt" or "WT_SESSION" in os.environ or "TERM" in os.environ else ""

    print(f"\n{cyan}======================================================================{reset}")
    print(f"{cyan}  >>  KnowSphere - GraphRAG Enterprise Knowledge Explorer{reset}")
    print(f"{cyan}======================================================================{reset}")
    print(f"  {green}> Frontend App   :{reset} http://localhost:5173")
    print(f"  {green}> Backend API    :{reset} http://localhost:8000")
    print(f"  {green}> Interactive API:{reset} http://localhost:8000/docs")
    print(f"  {green}> Graph Backend  :{reset} Embedded Graph Engine (NetworkX)")
    print(f"----------------------------------------------------------------------")
    print(f"  {yellow}Demo Accounts:{reset}")
    print(f"    * Admin : admin@knowsphere.ai / admin123")
    print(f"    * Demo  : demo@knowsphere.ai  / demo1234")
    print(f"----------------------------------------------------------------------")
    print(f"  Press {yellow}Ctrl+C{reset} to stop all services.\n")

def stream_output(process, prefix: str, color_code: str = ""):
    reset_code = "\033[0m" if color_code else ""
    try:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            stripped = line.rstrip()
            if stripped:
                print(f"{color_code}[{prefix}]{reset_code} {stripped}")
    except Exception:
        pass

def ensure_seed_data(python_exe: str):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    graph_store = DATA_DIR / "graph_store.json"
    sqlite_db = DATA_DIR / "knowsphere.db"
    
    if not graph_store.exists() or not sqlite_db.exists():
        print("[Runner] Initializing seed data and graph store...")
        try:
            subprocess.run(
                [python_exe, str(BACKEND_DIR / "seed_data.py")],
                cwd=str(ROOT_DIR),
                check=True,
            )
            print("[Runner] Seed data initialized successfully.")
        except Exception as e:
            print(f"[Runner] Note: Seed initialization returned: {e}")

def main():
    python_exe = get_python_executable()
    npm_cmd = get_npm_cmd()

    print(f"[Runner] Using Python: {python_exe}")
    print(f"[Runner] Using npm   : {npm_cmd}")

    # Ensure data is seeded
    ensure_seed_data(python_exe)

    print_banner()

    # Environment variables for subprocesses
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["VITE_API_URL"] = "http://localhost:8000"

    # Start Backend
    backend_cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "backend",
        "--port",
        "8000",
        "--reload",
    ]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )

    # Start Frontend
    if os.name == "nt":
        frontend_cmd = f'"{npm_cmd}" run dev -- --port 5173'
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=True,
            env=env,
        )
    else:
        frontend_cmd = [npm_cmd, "run", "dev", "--", "--port", "5173"]
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(FRONTEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )

    # Stream logs in background threads
    cyan_code = "\033[96m" if os.name != "nt" or "WT_SESSION" in os.environ or "TERM" in os.environ else ""
    magenta_code = "\033[95m" if os.name != "nt" or "WT_SESSION" in os.environ or "TERM" in os.environ else ""

    t_backend = threading.Thread(target=stream_output, args=(backend_proc, "BACKEND", cyan_code), daemon=True)
    t_frontend = threading.Thread(target=stream_output, args=(frontend_proc, "FRONTEND", magenta_code), daemon=True)

    t_backend.start()
    t_frontend.start()

    # Graceful shutdown handler
    def cleanup(*args):
        print("\n[Runner] Shutting down KnowSphere services...")
        try:
            if backend_proc.poll() is None:
                backend_proc.terminate()
                backend_proc.wait(timeout=3)
        except Exception:
            backend_proc.kill()

        try:
            if frontend_proc.poll() is None:
                if os.name == "nt":
                    # Kill full process tree for shell=True on Windows
                    subprocess.run(f"taskkill /F /T /PID {frontend_proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    frontend_proc.terminate()
                    frontend_proc.wait(timeout=3)
        except Exception:
            frontend_proc.kill()

        print("[Runner] KnowSphere stopped cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        while True:
            if backend_proc.poll() is not None:
                print(f"[Runner] Backend exited with code {backend_proc.returncode}")
                cleanup()
            if frontend_proc.poll() is not None:
                print(f"[Runner] Frontend exited with code {frontend_proc.returncode}")
                cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
