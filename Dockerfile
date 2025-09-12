# syntax=docker/dockerfile:1
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# pune poetry în PATH
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Instalează Poetry în /opt/poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --without dev --no-ansi

COPY app ./app
COPY main.py ./main.py

CMD ["python", "main.py"]
