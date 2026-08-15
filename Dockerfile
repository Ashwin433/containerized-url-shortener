# ==============================
# Stage 1: Builder
# ==============================
FROM python:3.12-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Create virtual environment
RUN python -m venv /opt/venv

# Copy production dependencies
COPY requirements.txt .

# Upgrade packaging tools and install dependencies
RUN pip install --no-cache-dir --upgrade \
        pip \
        setuptools==78.1.1 \
        wheel==0.46.2 \
        jaraco.context==6.1.0 \
    && pip install --no-cache-dir -r requirements.txt


# ==============================
# Stage 2: Production
# ==============================
FROM python:3.12-slim AS production

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Copy Python virtual environment
COPY --from=builder /opt/venv /opt/venv

# Copy application
COPY app ./app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app /opt/venv

# Switch to non-root user
USER appuser

# Application port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s \
            --timeout=5s \
            --start-period=20s \
            --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app.main:app"]
