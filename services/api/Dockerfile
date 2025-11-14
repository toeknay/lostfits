FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# deps for psycopg wheels, TLS, etc., then uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates bash git && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir uv

WORKDIR /app

# 1) bring in project metadata (only)
COPY pyproject.toml /app/pyproject.toml

# 2) compile and install into the system interpreter (no venv)
RUN uv pip compile pyproject.toml -o requirements.txt --generate-hashes && \
    uv pip install --system -r requirements.txt

# 3) now copy the application (keeps layer caching sensible)
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
