# SkyPulse Production Dockerfile
FROM python:3.11-slim

# Set environment defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency specifications
COPY pyproject.toml .

# Install dependencies including gunicorn for production process management
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "gunicorn>=22.0.0" && \
    pip install --no-cache-dir .

# Copy application source
COPY . .

# Create non-root system user and configure file permissions
RUN useradd --create-home --home-dir /home/appuser --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose default port
EXPOSE 8000

# Container healthcheck using root /healthz probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f "http://localhost:${PORT:-8000}/healthz" || exit 1

# Start production server using Gunicorn + Uvicorn workers with dynamic PORT support
CMD ["sh", "-c", "exec gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${PORT:-8000} --workers 2 --access-logfile -"]
