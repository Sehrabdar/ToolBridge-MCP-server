# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1 — builder
# Installs dependencies into a virtual environment for copying to the final image.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Copy dependency manifests first to benefit from layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies into a venv inside /app/.venv
RUN uv sync --frozen --no-dev --no-editable

# ---------------------------------------------------------------------------
# Stage 2 — runtime
# Lean image containing only what is needed to run the application.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the venv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY src/ ./src/

# Make the venv the active Python environment
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose the application port
EXPOSE 8000

# Health check — the application must respond to GET /health
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# Run the application via uvicorn
CMD ["uvicorn", "toolbridge.main:app", "--host", "0.0.0.0", "--port", "8000"]
