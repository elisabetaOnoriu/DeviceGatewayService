# syntax=docker/dockerfile:1

# 1) Match Python version with pyproject.toml (requires-python=">=3.12")
FROM python:3.12-slim

# 2) Install minimal system tools (curl is useful for health checks / debugging)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# 3) Configure Poetry (disable virtualenvs inside container)
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 4) Install Poetry (pinned version)
RUN curl -sSL https://install.python-poetry.org | python - --version $POETRY_VERSION \
 && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# 5) Set the working directory
WORKDIR /app

# 6) Copy dependency files first (to leverage Docker build cache)
COPY pyproject.toml poetry.lock* ./

# 7) Install production dependencies only (lock already valid)
RUN poetry install --no-root --without dev --no-ansi
# 8) Copy application source code
COPY app ./app
COPY main.py ./main.py

# 9) Default command when the container starts
CMD ["python", "main.py"]
