"""
Unified Localhost Runner for Onion Grading System (SIH 2026)
Hosts both Frontend and Backend:
- OnionAI YOLOv8 Deep Learning Grading & Metrology Dashboard (Port 5000)
- ONION-Q Centre Dashboard & Multi-Modal Inspection Server (Port 8000)
- Fully Merged Unified Route (Port 8000 /yolo/)
"""
import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe") if (ROOT / ".venv" / "Scripts" / "python.exe").exists() else sys.executable

def main():
    print("=" * 76)
    print("  🧅 ONION QUALITY GRADING & TRACEABILITY SYSTEM - LOCALHOST SERVER")
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

    time.sleep(2)

    print("\n" + "=" * 76)
    print("  🚀 ALL SERVICES RUNNING SUCCESSFULLY ON LOCALHOST:")
    print("=" * 76)
    print("  1. 🧅 OnionAI YOLOv8 AI Metrology & Grading Dashboard:")
    print("     👉 http://localhost:5000/")
    print("     (Live YOLOv8s-seg detection, 25mm ArUco calibration, presets & PDF audits)")
    print("")
    print("  2. 📊 ONION-Q Centre Dashboard:")
    print("     👉 http://localhost:8000/dashboard/app/index.html")
    print("")
    print("  3. 🔬 Multi-Modal Onion Scan Interface:")
    print("     👉 http://localhost:8000/dashboard/app/scan.html")
    print("")
    print("  4. 🔗 Fully Merged Unified Route on Port 8000:")
    print("     👉 http://localhost:8000/yolo/")
    print("")
    print("  5. 📑 API Documentation:")
    print("     - FastAPI Swagger Docs: http://localhost:8000/docs")
    print("     - YOLOv8 REST API:     http://localhost:5000/api/docs")
    print("=" * 76)
    print("\nPress Ctrl+C to stop all servers.\n")

    try:
        p_yolo.wait()
        p_server.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        p_yolo.terminate()
        p_server.terminate()
        p_yolo.wait()
        p_server.wait()
        print("Servers stopped cleanly.")

if __name__ == "__main__":
    main()
