# =============================================================================
# J.A.R.V.I.S. Agent Docker Configuration
# =============================================================================
# Multi-stage build for optimized production image
#
# Build:
#   docker build -t jarvis-agent:latest .
#
# Run:
#   docker run -d -p 8000:8000 --name jarvis jarvis-agent:latest
#
# With environment variables:
#   docker run -d -p 8000:8000 \
#     -e SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx \
#     -e LOG_LEVEL=INFO \
#     --name jarvis jarvis-agent:latest
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build dependencies
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

# Labels
LABEL maintainer="J.A.R.V.I.S. Team"
LABEL version="0.2.0"
LABEL description="J.A.R.V.I.S. Agent Server"

# Security: Create non-root user
RUN groupadd -r jarvis && \
    useradd -r -g jarvis -d /app -s /sbin/nologin -c "J.A.R.V.I.S. Agent User" jarvis

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=jarvis:jarvis . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/public && \
    chmod 755 /app/logs /app/data /app/public

# Switch to non-root user
USER jarvis

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV PORT=8000

# Entry point
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

# -----------------------------------------------------------------------------
# Stage 3: Development image (optional)
# -----------------------------------------------------------------------------
FROM production AS development

USER root

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install dev Python packages
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

USER jarvis

# Override entrypoint for hot reload
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
