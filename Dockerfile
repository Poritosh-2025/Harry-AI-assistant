# Production Dockerfile - AI Chat Application
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt gunicorn

# Application code
COPY --chown=appuser:appuser . .

# Create directories
RUN rm -rf /app/celerybeat-schedule && \
    mkdir -p /app/staticfiles /app/mediafiles /app/logs /app/celerybeat-schedule && \
    chown -R appuser:appuser /app

# Entrypoint
COPY --chown=appuser:appuser docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER appuser
EXPOSE 8000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]