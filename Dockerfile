# --------- Builder Stage ---------
FROM python:3.13-bookworm AS builder

# Install build dependencies and uv in a single layer
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libuv1-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Set up uv environment path
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock* ./

# Generate lock file and install dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    [ -f uv.lock ] || uv lock --quiet

# Install dependencies without project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy source code
COPY src/ /app/src/

# Install project with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# --------- Final Stage ---------
FROM python:3.13-slim-bookworm

# Set environment variables for container optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

# Install minimal system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with restricted group
RUN groupadd -r appgroup && useradd -r -g appgroup -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy virtual environment and source code from builder stage
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app/src /app/src

# Create logs directory and fix ownership in one step
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

# Switch to non-root user before exposing
USER appuser

# Expose port (default 8000, can be overridden with PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v1/health/ready || exit 1

# Default command for development
CMD ["sh", "-c", "uvicorn src.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload"]

