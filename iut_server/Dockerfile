# =============================================================================
#  Office Energy Monitoring — IUT Server Dockerfile
#  Multi-stage, non-root, optimized for Coolify / Contabo VPS deployment.
# =============================================================================

# ---- Stage 1: builder ------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# System deps needed to build some wheels (kept minimal).
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc \
 && rm -rf /var/lib/apt/lists/*

# Install dependencies to a prefix we can copy to the runtime stage.
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ---- Stage 2: runtime ------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    PYTHONPATH=/app

# Create non-root user.
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

WORKDIR /app

# Copy installed Python packages from the builder.
COPY --from=builder /install /usr/local

# Copy the application source without local env files.
COPY iut_server/__init__.py ./iut_server/__init__.py
COPY iut_server/app ./iut_server/app
COPY shared ./shared

# Persistent data directory (mount a Coolify volume here in production).
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request, sys; \
sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health').status == 200 else 1)"

CMD ["uvicorn", "iut_server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Build-time labels (overridden by Coolify).
LABEL org.opencontainers.image.title="office-energy-iut-server" \
      org.opencontainers.image.description="Office energy monitoring FastAPI IUT server" \
      org.opencontainers.image.source="https://github.com/naeemsadik/IUT_Techathon_Preli"
