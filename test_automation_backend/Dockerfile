# syntax=docker/dockerfile:1

# Backend Dockerfile for Flask API service
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system deps (psycopg2, curl) and create non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy app code
COPY . /app

# Ensure instance and storage directories exist
RUN mkdir -p /app/instance/storage/srs /app/instance/storage/runs && \
    chown -R root:root /app/instance

# Expose service port
EXPOSE 3001

# Environment defaults (can be overridden by .env / compose)
# MOCK defaults align to current code's expectations
ENV FLASK_ENV=production \
    REACT_APP_NODE_ENV=production \
    MOCK_LLM=true \
    MOCK_EXECUTION=true

# Healthcheck: ping root (/) health route
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
 CMD curl -fsS http://localhost:3001/ || exit 1

# Use gunicorn to serve the Flask app
# The app import path resolves to app:create_app in test_automation_backend/app/__init__.py
# We point to run:app to align with existing run.py entry that exposes app instance.
CMD ["gunicorn", "-b", "0.0.0.0:3001", "run:app"]
