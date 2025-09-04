# syntax=docker/dockerfile:1

# Base image: Python 3.12 slim
FROM python:3.12-slim

# Install minimal tools (curl helps with debugging/healthchecks)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Poetry and Python runtime configuration
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install Poetry (pinned version) and expose it on PATH
RUN curl -sSL https://install.python-poetry.org | python - --version $POETRY_VERSION \
 && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Workdir for the app
WORKDIR /app

# Copy dependency manifests first to leverage Docker layer caching
COPY pyproject.toml poetry.lock* ./

# Install only production dependencies (no dev group), and do not install the project itself
RUN poetry install --no-root --without dev --no-ansi

# Copy application source
COPY app ./app
COPY main.py ./main.py

# Default command
CMD ["python", "main.py"]
