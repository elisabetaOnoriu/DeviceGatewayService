# syntax=docker/dockerfile:1
# Use a lightweight Python base image
FROM python:3.11-slim

# Install system dependencies (curl is useful for health checks / debugging)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Configure Poetry (Python package manager)
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python - \
 && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Set the working directory
WORKDIR /app

# Copy dependency files first (to leverage Docker build cache)
COPY pyproject.toml poetry.lock* ./

# Install only production dependencies
RUN poetry install --no-root --only main

# Copy application source code
COPY app ./app
COPY gateway.py ./gateway.py

# Default environment variables (can be overridden from docker-compose.yml)
ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_REGION=us-east-1 \
    LOCALSTACK_ENDPOINT=http://localstack:4566 \
    QUEUE_NAME=device-messages \
    NUM_DEVICES=3 \
    SEND_INTERVAL_SEC=2

# Define the default command when the container starts
CMD ["python", "gateway.py"]
