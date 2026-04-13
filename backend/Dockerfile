# ── Backend Dockerfile ────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps for LightGBM (needs libgomp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cached layer — only rebuilds if requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Model directory is mounted at runtime via docker-compose volume
# but we create the folder so the container starts even if mount is delayed
RUN mkdir -p /app/model

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
