# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# (opțional) toolchain pt. pachete cu C extensions: psycopg2/lxml/cryptography etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc build-essential python3-dev \
    libssl-dev libffi-dev \
    libpq-dev \
    libxml2-dev libxslt1-dev \
 && rm -rf /var/lib/apt/lists/*

# Instalează Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}

WORKDIR /app

# Copiem metadata pentru cache
COPY pyproject.toml poetry.lock* ./

# 💡 Repară lock-ul în build (evită mismatch local)
RUN poetry lock --no-update \
 && poetry install --no-root --without dev --no-ansi

# Abia apoi codul
COPY app ./app
COPY main.py ./main.py

CMD ["python", "main.py"]
