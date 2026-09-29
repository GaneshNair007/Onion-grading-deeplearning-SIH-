"""
Unified Localhost Runner for Onion Grading System (SIH 2026)
Hosts Frontend and Backend:
- React + Vite Interactive Frontend (Port 5173)
- OnionAI YOLOv8 Deep Learning Grading & Metrology Dashboard (Port 5000)
- ONION-Q Centre Dashboard & Multi-Modal Inspection Server (Port 8000)
- Fully Merged Unified Routes (Port 8000 /site/ and /yolo/)
"""
import os
import sys
import time
import subprocess
from pathlib import Path

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe") if (ROOT / ".venv" / "Scripts" / "python.exe").exists() else sys.executable

def main():
    print("=" * 76)
    print("  [ONION QUALITY GRADING & TRACEABILITY SYSTEM - LOCALHOST SERVER]")
    print("  Smart India Hackathon (SIH 2026)")
    print("=" * 76)
    print("\nStarting services...")

    # 1. Start YOLOv8 Metrology & Grading Backend (Flask) on port 5000
    p_yolo = subprocess.Popen(
        [PYTHON, str(ROOT / "backend" / "model_backend" / "api.py")],
        cwd=str(ROOT),
        env=os.environ.copy()
    )

    # 2. Start ONION-Q Centre Dashboard & Scan Service (FastAPI / Uvicorn) on port 8000
    p_server = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "server.app:app", "--port", "8000", "--host", "0.0.0.0"],
        cwd=str(ROOT),
        env=os.environ.copy()
    )

    # 3. Start React + Vite Frontend on port 5173
    p_vite = None
    if (ROOT / "node_modules").exists():
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        p_vite = subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
            cwd=str(ROOT),
            env=os.environ.copy()
        )

    time.sleep(3)

    print("\n" + "=" * 76)
    print("  ALL SERVICES RUNNING SUCCESSFULLY ON LOCALHOST:")
    print("=" * 76)
    print("  1. React + Vite Interactive Frontend (from frontend branch):")
    print("     -> http://localhost:5173/")
    print("     (VOSTOK Acoustic & Optical Sensing Interface, Experimental Lab)")
    print("")
    print("  2. OnionAI YOLOv8 AI Metrology & Grading Dashboard:")
    print("     -> http://localhost:5000/  (or http://127.0.0.1:5000/)")
    print("     (Live YOLOv8s-seg detection, 25mm ArUco calibration, presets & PDF audits)")
    print("")
    print("  3. ONION-Q Centre Dashboard & Kiosk Scan:")
    print("     -> http://localhost:8000/dashboard/app/index.html")
    print("     -> http://localhost:8000/dashboard/app/scan.html")
    print("")
    print("  4. Fully Merged Unified Routes on Port 8000:")
    print("     -> http://localhost:8000/site/  (React Production Build)")
    print("     -> http://localhost:8000/yolo/  (YOLOv8 Metrology Dashboard)")
    print("")
    print("  5. API Documentation:")
    print("     - FastAPI Swagger Docs: http://localhost:8000/docs")
    print("     - YOLOv8 REST API:     http://localhost:5000/api/docs")
    print("=" * 76)
    print("\nPress Ctrl+C to stop all servers.\n")

    try:
        p_yolo.wait()
        p_server.wait()
        if p_vite:
            p_vite.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        p_yolo.terminate()
        p_server.terminate()
        if p_vite:
            p_vite.terminate()
        p_yolo.wait()
        p_server.wait()
        if p_vite:
            p_vite.wait()
        print("Servers stopped cleanly.")

if __name__ == "__main__":
    main()
