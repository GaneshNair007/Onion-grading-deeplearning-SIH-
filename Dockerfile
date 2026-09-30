# ============================================================
# ONION-Q  —  Single-container deployment
# Builds React frontend, installs Python deps, runs FastAPI.
# FastAPI serves: React SPA at /site/, YOLOv8 dashboard at
# /yolo/, ONION-Q dashboard at /dashboard/app/, and all APIs.
# ============================================================

# ---------- Stage 1: Build React + Vite frontend ----------
FROM node:20-slim AS frontend-builder

WORKDIR /app

# Install JS deps
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Copy source and build
COPY . .
RUN npm run build
# Output: /app/dist


# ---------- Stage 2: Python runtime + full app ----------
FROM python:3.11-slim AS runtime

# System libs needed by OpenCV / torch headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt ./
# CPU-only torch – keeps image under 2 GB
RUN pip install --no-cache-dir torch==2.13.0 torchvision==0.28.0 \
    --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project source
COPY . .

# Bring in the built React frontend from Stage 1
COPY --from=frontend-builder /app/dist ./dist

# Pre-create dirs that the app writes to at runtime
RUN mkdir -p reports/evidence local_data/gate_calibration backend/storage

# Expose the single port Railway / Render will bind to
EXPOSE 8000

# Start command: single Uvicorn process serving everything
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
